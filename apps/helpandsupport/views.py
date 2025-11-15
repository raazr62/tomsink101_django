from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import ContactSupport, LegalDocument, SupportTicket
from .serializers import (
    ContactSupportSerializer,
    LegalDocumentListSerializer,
    LegalDocumentDetailSerializer,
    SupportTicketCreateSerializer,
    SupportTicketSerializer,
    HelpAndSupportSerializer,
)


class HelpAndSupportView(APIView):
    """
    Get combined help and support information.
    Returns contact support details and list of legal documents.
    
    GET /api/help-support/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Get contact support info (singleton)
            contact_support = ContactSupport.objects.filter(is_active=True).first()
            
            # Get active legal documents
            legal_documents = LegalDocument.objects.filter(is_active=True).order_by('order', 'title')
            
            data = {
                'contact_support': ContactSupportSerializer(contact_support).data if contact_support else None,
                'legal_documents': LegalDocumentListSerializer(legal_documents, many=True).data
            }
            
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'message': 'Help and support information retrieved successfully.',
                'data': data
            })
        
        except Exception as e:
            return Response({
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'success': False,
                'message': 'Failed to retrieve help and support information.',
                'data': {'error': str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContactSupportView(APIView):
    """
    Get contact support information only.
    
    GET /api/help-support/contact/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            contact_support = ContactSupport.objects.filter(is_active=True).first()
            
            if not contact_support:
                return Response({
                    'status': status.HTTP_404_NOT_FOUND,
                    'success': False,
                    'message': 'Contact support information not found.',
                    'data': {}
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = ContactSupportSerializer(contact_support)
            
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'message': 'Contact support information retrieved successfully.',
                'data': serializer.data
            })
        
        except Exception as e:
            return Response({
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'success': False,
                'message': 'Failed to retrieve contact support information.',
                'data': {'error': str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LegalDocumentsListView(APIView):
    """
    Get list of all legal documents.
    
    GET /api/help-support/legal/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            documents = LegalDocument.objects.filter(is_active=True).order_by('order', 'title')
            serializer = LegalDocumentListSerializer(documents, many=True)
            
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'message': 'Legal documents retrieved successfully.',
                'data': serializer.data
            })
        
        except Exception as e:
            return Response({
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'success': False,
                'message': 'Failed to retrieve legal documents.',
                'data': {'error': str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LegalDocumentDetailView(APIView):
    """
    Get specific legal document by slug or type.
    
    GET /api/help-support/legal/<slug>/
    GET /api/help-support/legal/terms-of-service/
    GET /api/help-support/legal/privacy-policy/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, slug):
        try:
            # Try to find by slug first, then by document_type
            try:
                document = LegalDocument.objects.get(slug=slug, is_active=True)
            except LegalDocument.DoesNotExist:
                document = LegalDocument.objects.get(document_type=slug, is_active=True)
            
            serializer = LegalDocumentDetailSerializer(document)
            
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'message': 'Legal document retrieved successfully.',
                'data': serializer.data
            })
        
        except LegalDocument.DoesNotExist:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'success': False,
                'message': 'Legal document not found.',
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'success': False,
                'message': 'Failed to retrieve legal document.',
                'data': {'error': str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SupportTicketCreateView(APIView):
    """
    Create a new support ticket.
    Users can submit support requests.
    
    POST /api/help-support/ticket/create/
    """
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        try:
            serializer = SupportTicketCreateSerializer(
                data=request.data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                ticket = serializer.save()
                
                # Return the created ticket with full details
                result_serializer = SupportTicketSerializer(ticket)
                
                return Response({
                    'status': status.HTTP_201_CREATED,
                    'success': True,
                    'message': f'Support ticket created successfully. Ticket number: {ticket.ticket_number}',
                    'data': result_serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'status': status.HTTP_400_BAD_REQUEST,
                'success': False,
                'message': 'Failed to create support ticket.',
                'data': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'success': False,
                'message': 'An error occurred while creating the ticket.',
                'data': {'error': str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserSupportTicketsView(APIView):
    """
    Get all support tickets for the authenticated user.
    
    GET /api/help-support/tickets/
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request):
        try:
            tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')
            serializer = SupportTicketSerializer(tickets, many=True)
            
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'message': 'Support tickets retrieved successfully.',
                'data': serializer.data
            })
        
        except Exception as e:
            return Response({
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'success': False,
                'message': 'Failed to retrieve support tickets.',
                'data': {'error': str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SupportTicketDetailView(APIView):
    """
    Get specific support ticket details for the authenticated user.
    
    GET /api/help-support/tickets/<ticket_number>/
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request, ticket_number):
        try:
            ticket = SupportTicket.objects.get(
                ticket_number=ticket_number,
                user=request.user
            )
            
            serializer = SupportTicketSerializer(ticket)
            
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'message': 'Support ticket retrieved successfully.',
                'data': serializer.data
            })
        
        except SupportTicket.DoesNotExist:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'success': False,
                'message': 'Support ticket not found.',
                'data': {}
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'success': False,
                'message': 'Failed to retrieve support ticket.',
                'data': {'error': str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
