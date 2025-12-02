import email

from apps.users.managers import UserManager
from .models import User, Profile, OTP
from rest_framework import  serializers
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from django.utils.timezone import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from .utils import generate_otp, send_normal_mail, send_verification_otp_email
from django.utils import timezone
from apps.utils.helpers import error


class SignUpSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({'email': 'User with this email already exists.'})
        return attrs

    class Meta:
        model = User
        fields = ['email', 'password', 'name']

    def create(self, validated_data):
        name = validated_data.pop('name', '')
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        # Create user
        user = User.objects.create_user(email=email, password=password, **validated_data)

        # Create profile
        Profile.objects.create(
            user=user,
            name=name
        )

        # Generate OTP for email verification
        otp = generate_otp(6)
        user.email_verification_otp = make_password(otp)
        user.otp_expires_at = timezone.now() + timedelta(minutes=10)
        user.otp_attempts = 0
        user.save()

        # Send verification OTP email
        try:
            send_verification_otp_email(user, otp)
        except Exception as e:
            # Log the error but don't fail the signup
            print(f"Failed to send verification email: {str(e)}")

        return user
    
    def to_representation(self, instance):
        return {
            'id': instance.id,
            'name': instance.profile.name,
            'email': instance.email,
            'is_email_verified': instance.is_email_verified,
            'message': 'Account created successfully. Please check your email to verify your account.'
        }


class SignInSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    refresh_token = serializers.CharField(read_only=True)
    access_token = serializers.CharField(read_only=True)

    def validate(self, attrs):
        password = attrs.get('password')
        user = User.objects.filter(email=attrs['email']).first()
        if not user:
           raise serializers.ValidationError({'email': 'User with this email does not exist.'})
        if not user.check_password(password):
            raise serializers.ValidationError({'password': 'Invalid password.'})
        if not user.is_active:
            raise serializers.ValidationError({'error': 'Account is inactive. please verify your email to activate your account.'})
        self.user = user
        return attrs

    def to_representation(self, instance):
        user = self.user
        refresh = RefreshToken.for_user(user)
        return {
            'id': user.id,
            'email': user.email,
            'refresh_token': str(refresh),
            'access_token': str(refresh.access_token)
        }

class SignOutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        self.refresh_token = attrs.get('refresh_token')
        return attrs
    
    def save(self, **kwargs):
        try:
            token = RefreshToken(self.refresh_token)
            token.blacklist()
        except Exception as e:
            return ValidationError({'error': str(e)})

class ChangePasswordSerializer(serializers.Serializer):
    email = serializers.CharField()
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'name', 'old_password', 'new_password', 'confirm_password']

    def validate(self, attrs):
        email = attrs.get('email')
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        user = User.objects.filter(email=email).first()
        if not user:
            raise ValidationError({'error': 'User not found.'})
        
        if not user.check_password(old_password):
            raise ValidationError({'error': 'Old password is incorrect.'})
        
        if new_password != confirm_password:
            raise ValidationError({'error': 'New password and confirm password is not match.'})
        
        if old_password == new_password:
            raise ValidationError({'error': 'The new password is not the same as the old password.'})
        
        try:
            validate_password(new_password)
        except Exception as e:
            raise ValidationError({'error': str(e.messages)})
        
        self.user = user
        return attrs
    
    def save(self):
        new_password = self.validated_data['new_password']
        user = self.user
        user.set_password(new_password)
        user.save()
        return user

class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.CharField()

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'error': 'User not found.'})

        otp_code = generate_otp()
        otp_hashed = make_password(otp_code)
        purpose = attrs['purpose']

        expires_at = timezone.now() + timedelta(minutes=3)

        OTP.objects.update_or_create(user=user, defaults={'otp': otp_hashed, 'is_verify': False, 'purpose': purpose, 'created_at': timezone.now(), 'expires_at': expires_at})

        data = {
            'subject': 'OTP for reset password.',
            'body': f'Your OTP is {otp_code}. Expire in 3 minutes.',
            'from': settings.EMAIL_HOST_USER,
            'to': [user.email,]
        }
        send_normal_mail(data)
        return attrs

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        purpose = attrs.get('purpose')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist as e:
            raise serializers.ValidationError({'error': 'User not found.'})

        try:
            otp_obj = OTP.objects.select_related('user').get(user=user, purpose=purpose)
            if otp_obj.is_verify:
                raise serializers.ValidationError({'error': 'OTP already used.'})
            if not otp_obj.is_expired():
                raise serializers.ValidationError({'error': 'OTP still valid. Please wait for it to expire.'})
        except OTP.DoesNotExist:
            raise serializers.ValidationError({'error': 'User with OTP not found.'})

        otp_code = generate_otp()
        otp_hashed = make_password(otp_code)
        purpose = attrs['purpose']

        expires_at = timezone.now() + timedelta(minutes=3)

        OTP.objects.update_or_create(user=user, defaults={'otp': otp_hashed, 'is_verify': False, 'purpose': purpose, 'created_at': timezone.now(), 'expires_at': expires_at})

        data = {
            'subject': 'OTP for reset password.',
            'body': f'Your OTP is {otp_code}. Expire in 3 minutes.',
            'from': settings.EMAIL_HOST_USER,
            'to': [user.email,]
        }
        send_normal_mail(data)
        return attrs

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    purpose = serializers.CharField()

    def validate(self, data):
        email = data.get("email")
        otp_input = data.get("otp")
        purpose = data.get("purpose")
        print(email, otp_input, purpose)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({'error': "Invalid email."})

        try:
            otp_obj = OTP.objects.get(user=user, purpose=purpose)
        except OTP.DoesNotExist:
            raise serializers.ValidationError({'error': "OTP not found. Please request a new one."})

        if otp_obj.is_verify:
            raise serializers.ValidationError({'error': "OTP already varified."})

        if otp_obj.is_expired():
            otp_obj.delete()
            raise serializers.ValidationError({'error': "OTP expired. Please request a new one."})

        if not otp_obj.check_otp(otp_input):
            otp_obj.attempts += 1
            if otp_obj.attempts >= 3:
                otp_obj.delete()
                raise serializers.ValidationError({'error': "Too many incorrect attempts. Please request a new one."})
            otp_obj.save()
            raise serializers.ValidationError({'error': f"Incorrect OTP. Attempt {otp_obj.attempts}/3."})

        self.user = user
        self.otp_obj = otp_obj
        return data

    def save(self):
        self.otp_obj.is_verify = True
        self.otp_obj.attempts = 0
        self.otp_obj.save()

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    purpose = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data['email']
        otp = data['otp']
        purpose = data['purpose']
        new_password = data['new_password']
        confirm_password = data['confirm_password']

        try:
            user = User.objects.get(email=email)
            otp_obj = OTP.objects.get(user=user, purpose=purpose)
        except (User.DoesNotExist, OTP.DoesNotExist):
            raise serializers.ValidationError({'error': "Invalid credentials or OTP."})

        if otp_obj.is_expired():
            otp_obj.delete()
            raise serializers.ValidationError({'error': "OTP has expired."})

        if not otp_obj.check_otp(otp):
            raise serializers.ValidationError({'error': "Incorrect OTP."})
        
        if not otp_obj.is_verify:
            raise serializers.ValidationError({'error': 'OTP not verified yet. Please verify OTP first.'})

        if new_password != confirm_password:
            raise serializers.ValidationError({'error': "Passwords do not match."})

        try:
            validate_password(new_password, user)
            print("Password validation passed")
        except serializers.ValidationError as e:
            raise serializers.ValidationError({'error': str(e.messages)})

        data['user'] = user
        print(data)
        print(data['user'])
        return data

    def save(self):
        user = self.validated_data['user']
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        OTP.objects.filter(user=user, purpose=self.validated_data['purpose']).delete()

class PreparationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['preparation_type']

class UpdateProfileAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['avatar']
        extra_kwargs = {
            'avatar': { 'write_only': True },
        }




#  user
class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "is_staff",
            "is_active",
            "date_joined",
            "profile",
        ]


# UserProfile
class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = [
            "user",
            "name",
            "accepted_terms",
            "avatar",
            "dob",
            "created_at",
            "updated_at",
        ]


class DeleteAccountSerializer(serializers.Serializer):
    """
    Serializer for account deletion
    Requires password confirmation before deletion
    """
    password = serializers.CharField(write_only=True, required=True)
    confirm_deletion = serializers.BooleanField(required=True)
    
    def validate_confirm_deletion(self, value):
        """Ensure user confirmed deletion"""
        if not value:
            raise serializers.ValidationError("You must confirm account deletion.")
        return value
    
    def validate(self, attrs):
        """Validate password and check if user can be deleted"""
        user = self.context['request'].user
        password = attrs.get('password')
        
        if not user.check_password(password):
            raise serializers.ValidationError({'password': 'Invalid password.'})
        
        return attrs


class VerifyEmailOTPSerializer(serializers.Serializer):
    """Serializer for email verification using OTP"""
    email = serializers.EmailField(required=True)
    otp_code = serializers.CharField(required=True, max_length=6, min_length=6)
    
    def validate(self, attrs):
        email = attrs.get('email')
        otp_code = attrs.get('otp_code')
        
        try:
            user = User.objects.get(email=email)
            
            if user.is_email_verified:
                raise serializers.ValidationError({'email': 'This email is already verified.'})
            
            if not user.email_verification_otp:
                raise serializers.ValidationError({'otp_code': 'No OTP found. Please request a new one.'})
            
            if user.is_verification_otp_expired():
                raise serializers.ValidationError({'otp_code': 'OTP has expired. Please request a new one.'})
            
            # Check max attempts
            if user.otp_attempts >= 5:
                raise serializers.ValidationError({'otp_code': 'Maximum verification attempts exceeded. Please request a new OTP.'})
            
            # Verify OTP
            if not user.check_verification_otp(otp_code):
                user.otp_attempts += 1
                user.save()
                remaining = 5 - user.otp_attempts
                raise serializers.ValidationError({'otp_code': f'Invalid OTP. {remaining} attempts remaining.'})
            
            self.user = user
            return attrs
            
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': 'No account found with this email address.'})
    
    def save(self):
        """Mark email as verified"""
        from .utils import send_verification_success_email
        
        self.user.is_email_verified = True
        self.user.email_verification_otp = None
        self.user.otp_expires_at = None
        self.user.otp_attempts = 0
        self.user.is_active = True
        self.user.save()
        
        # Send confirmation email
        try:
            send_verification_success_email(self.user)
        except Exception as e:
            print(f"Failed to send confirmation email: {str(e)}")
        
        return self.user


class ResendVerificationOTPSerializer(serializers.Serializer):
    """Serializer for resending verification OTP"""
    email = serializers.EmailField(required=True)
    
    def validate(self, attrs):
        """Validate email exists and needs verification"""
        email = attrs.get('email')
        try:
            user = User.objects.get(email=email)
            
            if user.is_email_verified:
                raise serializers.ValidationError({'email': 'This email is already verified.'})
            
            # Store user for save method
            self.user = user
            return attrs
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': 'No account found with this email address.'})
    
    def save(self):
        """Generate new OTP and send email"""
        from .utils import send_verification_otp_email
        
        # Generate new OTP
        otp = generate_otp(6)
        self.user.email_verification_otp = make_password(otp)
        self.user.otp_expires_at = timezone.now() + timedelta(minutes=10)
        self.user.otp_attempts = 0
        self.user.save()
        
        # Send verification OTP email
        try:
            send_verification_otp_email(self.user, otp)
        except Exception as e:
            raise serializers.ValidationError(f'Failed to send verification email: {str(e)}')
        
        return self.user
    
    

from rest_framework import serializers
from apps.users.utils import Google, register_with_google
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from apps.users.utils import Google, register_with_google

class GoogleSerializer(serializers.Serializer):
    access_token = serializers.CharField()

    def validate_access_token(self, access_token):
        user_data = Google.validate(access_token)
        try:
            user_data['sub']
        except KeyError:
            raise AuthenticationFailed('Invalid token')
        
        if user_data['aud'] != settings.GOOGLE_CLIENT_ID:
            raise AuthenticationFailed("Could not verify Google token")
        
        user_id = user_data['sub']
        email = user_data['email']
        first_name = user_data.get('given_name', '')
        last_name = user_data.get('family_name', '')

        provider = 'google'

        return register_with_google(provider, email, first_name, last_name)


