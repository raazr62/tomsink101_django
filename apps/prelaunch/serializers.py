from rest_framework import serializers
from .models import PrelaunchUser, PrelaunchReferral
from django.db.models import Count


class PrelaunchUserSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and displaying prelaunch users.
    """
    referral_link = serializers.ReadOnlyField()
    referral_count = serializers.ReadOnlyField()
    
    class Meta:
        model = PrelaunchUser
        fields = [
            'id',
            'name',
            'email',
            'referral_code',
            'referred_by',
            'referral_link',
            'referral_count',
            'activated',
            'created_at',
        ]
        read_only_fields = ['id', 'referral_code', 'referral_link', 'referral_count', 'created_at']

    def validate_email(self, value):
        """Check if email already exists."""
        if PrelaunchUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_referred_by(self, value):
        """Validate that the referral code exists if provided."""
        if value and not PrelaunchUser.objects.filter(referral_code=value).exists():
            raise serializers.ValidationError("Invalid referral code.")
        return value


class PrelaunchUserDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer with referral statistics.
    """
    referral_link = serializers.ReadOnlyField()
    referral_count = serializers.ReadOnlyField()
    referred_users = serializers.SerializerMethodField()
    
    class Meta:
        model = PrelaunchUser
        fields = [
            'id',
            'name',
            'email',
            'referral_code',
            'referred_by',
            'referral_link',
            'referral_count',
            'referred_users',
            'activated',
            'created_at',
        ]
        read_only_fields = fields

    def get_referred_users(self, obj):
        """Get list of users referred by this user."""
        referrals = obj.get_referrals()[:10]  # Limit to 10 most recent
        return [{
            'name': user.name,
            'email': user.email,
            'created_at': user.created_at
        } for user in referrals]


class PrelaunchReferralSerializer(serializers.ModelSerializer):
    """
    Serializer for referral records.
    """
    parent_name = serializers.CharField(source='parent_user.name', read_only=True)
    parent_email = serializers.CharField(source='parent_user.email', read_only=True)
    child_name = serializers.CharField(source='child_user.name', read_only=True)
    
    class Meta:
        model = PrelaunchReferral
        fields = [
            'id',
            'parent_referral_code',
            'parent_name',
            'parent_email',
            'child_email',
            'child_name',
            'created_at',
        ]
        read_only_fields = fields


class ReferralLeaderboardSerializer(serializers.Serializer):
    """
    Serializer for referral leaderboard/rankings.
    """
    rank = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()
    referral_code = serializers.CharField()
    referral_count = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class PrelaunchStatsSerializer(serializers.Serializer):
    """
    Serializer for overall pre-launch statistics.
    """
    total_signups = serializers.IntegerField()
    total_referrals = serializers.IntegerField()
    total_activated = serializers.IntegerField()
    top_referrers = ReferralLeaderboardSerializer(many=True)
    recent_signups = PrelaunchUserSerializer(many=True)
