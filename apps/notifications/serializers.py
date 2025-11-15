from rest_framework import serializers
from .models import NotificationPreference


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationPreference model.
    Used for both displaying and updating notification preferences.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id',
            'user',
            'user_email',
            'email_notifications',
            'daily_checkin_reminders',
            'milestone_achievements',
            'ai_insights_and_tips',
            'push_notifications',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'user_email', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """
        Custom validation if needed
        """
        return attrs


class NotificationPreferenceUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for updating notification preferences.
    Only includes the fields that can be updated.
    """
    class Meta:
        model = NotificationPreference
        fields = [
            'email_notifications',
            'daily_checkin_reminders',
            'milestone_achievements',
            'ai_insights_and_tips',
            'push_notifications',
        ]
    
    def update(self, instance, validated_data):
        """
        Update notification preferences
        """
        instance.email_notifications = validated_data.get('email_notifications', instance.email_notifications)
        instance.daily_checkin_reminders = validated_data.get('daily_checkin_reminders', instance.daily_checkin_reminders)
        instance.milestone_achievements = validated_data.get('milestone_achievements', instance.milestone_achievements)
        instance.ai_insights_and_tips = validated_data.get('ai_insights_and_tips', instance.ai_insights_and_tips)
        instance.push_notifications = validated_data.get('push_notifications', instance.push_notifications)
        instance.save()
        return instance


class BulkUpdateSerializer(serializers.Serializer):
    """
    Serializer for bulk enable/disable all notifications.
    Used with the Enable All and Disable All buttons.
    """
    action = serializers.ChoiceField(
        choices=['enable_all', 'disable_all'],
        required=True,
        help_text="Action to perform: 'enable_all' or 'disable_all'"
    )
