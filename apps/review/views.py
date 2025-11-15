from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.views import APIView
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404
from apps.review.models import Review, ReviewCategory, ReviewSettings
from apps.review.serializers import (
    ReviewSerializer, ReviewCreateSerializer,
    ReviewCategorySerializer, ReviewSettingsSerializer
)


class ReviewListView(APIView):
    """
    GET: List approved reviews (public)
    POST: Create new review (public if anonymous allowed)
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """List all approved reviews"""
        if request.user.is_staff:
            reviews = Review.objects.all().order_by('-created_at')
        else:
            reviews = Review.objects.filter(is_approved=True).order_by('-created_at')
        
        serializer = ReviewSerializer(reviews, many=True)
        return Response({
            'status': status.HTTP_200_OK,
            'success': True,
            'count': reviews.count(),
            'data': serializer.data
        })
    
    def post(self, request):
        """Create a new review"""
        # Check if reviews are enabled
        settings = ReviewSettings.objects.first()
        if settings and not settings.enable_reviews:
            return Response({
                'status': status.HTTP_403_FORBIDDEN,
                'success': False,
                'message': 'Review submission is currently disabled'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check authentication if required
        if settings and not settings.allow_anonymous and not request.user.is_authenticated:
            return Response({
                'status': status.HTTP_401_UNAUTHORIZED,
                'success': False,
                'message': 'You must be logged in to submit a review'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = ReviewCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            review = serializer.save()
            return Response({
                'status': status.HTTP_201_CREATED,
                'success': True,
                'message': 'Thank you for your feedback! Your review has been submitted.' + 
                        (' It will be visible after admin approval.' if settings and settings.require_approval else ''),
                'data': ReviewSerializer(review).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'status': status.HTTP_400_BAD_REQUEST,
            'success': False,
            'message': 'Invalid data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ReviewDetailView(APIView):
    """
    GET: Get single review
    PUT/PATCH: Update review (admin only)
    DELETE: Delete review (admin only)
    """
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]
    
    def get(self, request, pk):
        """Get single review"""
        if request.user.is_staff:
            review = get_object_or_404(Review, pk=pk)
        else:
            review = get_object_or_404(Review, pk=pk, is_approved=True)
        
        serializer = ReviewSerializer(review)
        return Response({
            'status': status.HTTP_200_OK,
            'success': True,
            'data': serializer.data
        })
    
    def put(self, request, pk):
        """Update review (admin only)"""
        review = get_object_or_404(Review, pk=pk)
        serializer = ReviewSerializer(review, data=request.data, partial=False)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'message': 'Review updated successfully',
                'data': serializer.data
            })
        
        return Response({
            'status': status.HTTP_400_BAD_REQUEST,
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        """Partial update review (admin only)"""
        review = get_object_or_404(Review, pk=pk)
        serializer = ReviewSerializer(review, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'message': 'Review updated successfully',
                'data': serializer.data
            })
        
        return Response({
            'status': status.HTTP_400_BAD_REQUEST,
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """Delete review (admin only)"""
        review = get_object_or_404(Review, pk=pk)
        review.delete()
        return Response({
            'status': status.HTTP_204_NO_CONTENT,
            'success': True,
            'message': 'Review deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


class FeaturedReviewsView(APIView):
    """
    GET: Get featured reviews only
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get all featured reviews"""
        reviews = Review.objects.filter(is_approved=True, is_featured=True).order_by('-created_at')
        serializer = ReviewSerializer(reviews, many=True)
        return Response({
            'status': status.HTTP_200_OK,
            'success': True,
            'count': reviews.count(),
            'data': serializer.data
        })


class ReviewStatsView(APIView):
    """
    GET: Get review statistics
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get review statistics"""
        stats = Review.objects.filter(is_approved=True).aggregate(
            total_reviews=Count('id'),
            average_rating=Avg('rating'),
            five_star=Count('id', filter=Q(rating=5)),
            four_star=Count('id', filter=Q(rating=4)),
            three_star=Count('id', filter=Q(rating=3)),
            two_star=Count('id', filter=Q(rating=2)),
            one_star=Count('id', filter=Q(rating=1))
        )
        return Response({
            'status': status.HTTP_200_OK,
            'success': True,
            'data': stats
        })


class ApproveReviewView(APIView):
    """
    POST: Approve a review (admin only)
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request, pk):
        """Approve a review"""
        review = get_object_or_404(Review, pk=pk)
        review.is_approved = True
        review.save()
        return Response({
            'status': status.HTTP_200_OK,
            'success': True,
            'message': 'Review approved successfully',
            'data': ReviewSerializer(review).data
        })


class FeatureReviewView(APIView):
    """
    POST: Feature/unfeature a review (admin only)
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request, pk):
        """Toggle feature status of a review"""
        review = get_object_or_404(Review, pk=pk)
        review.is_featured = not review.is_featured
        review.save()
        return Response({
            'status': status.HTTP_200_OK,
            'success': True,
            'message': f"Review {'featured' if review.is_featured else 'unfeatured'} successfully",
            'data': ReviewSerializer(review).data
        })


class ReviewSettingsView(APIView):
    """
    Get review form settings (public)
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        settings = ReviewSettings.objects.first()
        if not settings:
            # Create default settings
            settings = ReviewSettings.objects.create()
        
        serializer = ReviewSettingsSerializer(settings)
        return Response({
            'status': status.HTTP_200_OK,
            'success': True,
            'data': serializer.data
        })


class SubmitReviewView(APIView):
    """
    Public endpoint for submitting reviews
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Check if reviews are enabled
        settings = ReviewSettings.objects.first()
        if settings and not settings.enable_reviews:
            return Response({
                'status': status.HTTP_403_FORBIDDEN,
                'success': False,
                'message': 'Review submission is currently disabled'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check authentication if required
        if settings and not settings.allow_anonymous and not request.user.is_authenticated:
            return Response({
                'status': status.HTTP_401_UNAUTHORIZED,
                'success': False,
                'message': 'You must be logged in to submit a review'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = ReviewCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            review = serializer.save()
            
            # Send notification email if enabled
            if settings and settings.notify_on_new_review and settings.notification_email:
                # TODO: Implement email notification
                pass
            
            return Response({
                'status': status.HTTP_201_CREATED,
                'success': True,
                'message': 'Thank you for your feedback! Your review has been submitted.' + 
                        (' It will be visible after admin approval.' if settings.require_approval else ''),
                'data': ReviewSerializer(review).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'status': status.HTTP_400_BAD_REQUEST,
            'success': False,
            'message': 'Invalid data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ReviewCategoryListView(APIView):
    """
    GET: List all active review categories
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """List all active categories"""
        categories = ReviewCategory.objects.filter(is_active=True).order_by('order', 'name')
        serializer = ReviewCategorySerializer(categories, many=True)
        return Response({
            'status': status.HTTP_200_OK,
            'success': True,
            'count': categories.count(),
            'data': serializer.data
        })
