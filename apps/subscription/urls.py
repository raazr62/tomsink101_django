from django.urls import path
from . import views

urlpatterns = [
    # Package endpoints
    path('packages/', views.PackageView.as_view(), name='package'),
    path('packages/<int:pk>', views.PackageView.as_view(), name='package'),
    
    # Subscription endpoints
    path('subscription/', views.SubscriptionView.as_view(), name='subscription'),
    path('subscription/<int:package_id>', views.SubscriptionView.as_view(), name='subscription'),

    # Stripe checkout
    path('subscription/<int:package_id>/checkout/', views.SubscriptionCreate.as_view(), name='subscription-checkout'),
    
    # PayPal checkout
    path('subscription/<int:package_id>/paypal-checkout/', views.PayPalSubscriptionCreate.as_view(), name='paypal-subscription-checkout'),
    
    # Cancel subscription
    path('cancel_subscription/<int:subscription_id>', views.CancelSubscription.as_view(), name='cancel_subscription'),
    
    # Webhooks
    path('webhook/', views.stripe_webhook_view, name='stripe-webhook'),
    path('paypal-webhook/', views.paypal_webhook_view, name='paypal-webhook'),
]