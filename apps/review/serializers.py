from rest_framework import serializers
from apps.review.models import Review, ReviewCategory, ReviewSettings
from django.utils import timezone


class ReviewSerializer(serializers.ModelSerializer):
    user_identifier = serializers.SerializerMethodField()
    rating_stars = serializers.ReadOnlyField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'user_identifier', 'rating', 'rating_stars',
            'feedback_text', 'created_at', 'is_approved',
            'is_featured', 'admin_response', 'responded_at'
        ]
        read_only_fields = ['id', 'created_at', 'is_approved', 'is_featured', 
                           'admin_response', 'responded_at', 'rating_stars']
    
    def get_user_identifier(self, obj):
        return obj.get_user_identifier()


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reviews (public submission)"""
    
    class Meta:
        model = Review
        fields = ['rating', 'feedback_text', 'user_name', 'user_email']
    
    def validate_rating(self, value):
        """Validate rating is within allowed range"""
        settings = ReviewSettings.objects.first()
        if settings:
            if value < settings.min_rating or value > settings.max_rating:
                raise serializers.ValidationError(
                    f"Rating must be between {settings.min_rating} and {settings.max_rating}"
                )
        return value
    
    def validate_feedback_text(self, value):
        """Validate feedback text length"""
        settings = ReviewSettings.objects.first()
        if settings:
            if len(value) < settings.min_text_length:
                raise serializers.ValidationError(
                    f"Feedback must be at least {settings.min_text_length} characters"
                )
            if len(value) > settings.max_text_length:
                raise serializers.ValidationError(
                    f"Feedback cannot exceed {settings.max_text_length} characters"
                )
        return value
    
    def create(self, validated_data):
        # Add user if authenticated
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        
        # Check if approval required
        settings = ReviewSettings.objects.first()
        if settings and not settings.require_approval:
            validated_data['is_approved'] = True
        
        return super().create(validated_data)


class ReviewCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewCategory
        fields = ['id', 'name', 'description', 'icon', 'order', 'is_active']


class ReviewSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewSettings
        fields = [
            'enable_reviews', 'allow_anonymous', 'show_title',
            'show_subtitle', 'placeholder_text', 'submit_button_text',
            'min_rating', 'max_rating', 'min_text_length', 'max_text_length'
        ]
