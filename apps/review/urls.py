from django.urls import path
from apps.review.views import (
    ReviewListView, ReviewDetailView, FeaturedReviewsView, 
    ReviewStatsView, ApproveReviewView, FeatureReviewView,
    ReviewSettingsView, SubmitReviewView, ReviewCategoryListView
)

app_name = 'review'

urlpatterns = [
    # Review endpoints
    path('reviews/', ReviewListView.as_view(), name='review-list'),
    path('reviews/<int:pk>/', ReviewDetailView.as_view(), name='review-detail'),
    path('reviews/featured/', FeaturedReviewsView.as_view(), name='review-featured'),
    path('reviews/stats/', ReviewStatsView.as_view(), name='review-stats'),
    path('reviews/<int:pk>/approve/', ApproveReviewView.as_view(), name='review-approve'),
    path('reviews/<int:pk>/feature/', FeatureReviewView.as_view(), name='review-feature'),
    
    # Category endpoints
    path('categories/', ReviewCategoryListView.as_view(), name='category-list'),
    
    # Settings and submission
    path('settings/', ReviewSettingsView.as_view(), name='settings'),
    path('submit/', SubmitReviewView.as_view(), name='submit'),
]
