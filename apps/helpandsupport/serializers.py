from rest_framework import serializers
from .models import ContactSupport, LegalDocument, SupportTicket


class ContactSupportSerializer(serializers.ModelSerializer):
    """
    Serializer for ContactSupport model.
    Returns contact information for display in the UI.
    """
    class Meta:
        model = ContactSupport
        fields = [
            'id',
            'support_email',
            'support_phone',
            'support_phone_display',
            'average_response_time',
            'is_active',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']


class LegalDocumentListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing legal documents.
    Returns basic information without full content.
    """
    class Meta:
        model = LegalDocument
        fields = [
            'id',
            'title',
            'document_type',
            'slug',
            'version',
            'effective_date',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'updated_at']


class LegalDocumentDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for legal document details.
    Includes full content.
    """
    class Meta:
        model = LegalDocument
        fields = [
            'id',
            'title',
            'document_type',
            'content',
            'slug',
            'version',
            'effective_date',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating support tickets.
    """
    class Meta:
        model = SupportTicket
        fields = [
            'email',
            'subject',
            'message',
        ]
    
    def create(self, validated_data):
        # Add user if authenticated
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
            if not validated_data.get('email'):
                validated_data['email'] = request.user.email
        
        return super().create(validated_data)


class SupportTicketSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying support tickets.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = SupportTicket
        fields = [
            'id',
            'ticket_number',
            'user',
            'user_email',
            'email',
            'subject',
            'message',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'resolved_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'ticket_number',
            'user',
            'user_email',
            'status_display',
            'priority_display',
            'resolved_at',
            'created_at',
            'updated_at',
        ]


class HelpAndSupportSerializer(serializers.Serializer):
    """
    Combined serializer for the main Help & Support page.
    Returns contact support info and legal document links.
    """
    contact_support = ContactSupportSerializer(read_only=True)
    legal_documents = LegalDocumentListSerializer(many=True, read_only=True)
