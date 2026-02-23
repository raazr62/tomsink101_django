from .models import Package, Subscription, PackageFeature, PricingSection
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import SubscriptionHeaderSerializer, SubscriptionSerializer, PackageSerializer, PricingSectionSerializer, PackageCMSSerializer
import requests
import json
from base64 import b64encode
from django.db.models import Prefetch

# Create your views here.

User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY


# PayPal Helper Functions
def get_paypal_access_token():
    """Get PayPal OAuth access token."""
    client_id = settings.PAYPAL_CLIENT_ID
    client_secret = settings.PAYPAL_CLIENT_SECRET
    
    auth = b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    
    url = f"{settings.PAYPAL_API_URL}/v1/oauth2/token"
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


def paypal_api_request(method, endpoint, data=None, access_token=None):
    """Make PayPal API request."""
    if not access_token:
        access_token = get_paypal_access_token()
    
    if not access_token:
        return None
    
    url = f"{settings.PAYPAL_API_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    elif method == "PATCH":
        response = requests.patch(url, headers=headers, json=data)
    else:
        return None
    
    if response.status_code in [200, 201]:
        return response.json()
    return None

class PackageView(APIView):
    def get(self,request,pk=None):
        if pk:
            package = Package.objects.get(pk=pk)
            serializer = PackageSerializer(package)
            response = {
                "status": status.HTTP_200_OK,
                "success": True,
                "message": "Package retrieved successfully",
                "data": serializer.data
            }
            return Response(response)
        packages = Package.objects.all()
        serializer = PackageSerializer(packages, many=True)
        response = {
            "status": status.HTTP_200_OK,
            "success": True,
            "message": "All packages retrieved successfully",
            "data": serializer.data
        }
        return Response(response)

class SubscriptionView(APIView):
    def get(self, request, package_id=None):
        if package_id:
            subscription = Subscription.objects.get(id=package_id)
            serializer = SubscriptionSerializer(subscription)
            response = {
                "status": status.HTTP_200_OK,
                "success": True,
                "message": "Subscription retrieved successfully",
                "data": serializer.data
            }
            return Response(response)
        subscriptions = Subscription.objects.all()
        serializer = SubscriptionSerializer(subscriptions, many=True)
        response = {
            "status": status.HTTP_200_OK,
            "success": True,
            "message": "All subscriptions retrieved successfully",
            "data": serializer.data
        }
        return Response(response)


class SubscriptionCreate(APIView):
    """Create Stripe subscription checkout session."""
    
    def post(self, request, package_id):
        user = request.user
        
        try:
            package = Package.objects.get(id=package_id)
        except Package.DoesNotExist:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'success': False,
                'message': 'Package not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not package.stripe_price_id:
            return Response({
                'status': status.HTTP_400_BAD_REQUEST,
                'success': False,
                'message': 'Stripe is not configured for this package.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            customers = stripe.Customer.list(email=user.email)

            if customers.data:
                stripe_customer = customers.data[0]
            else:
                stripe_customer = stripe.Customer.create(
                    email=user.email,
                    name=f'{user.profile.name}'
                )
        except stripe.error.StripeError as e:
            return Response({
                'status': status.HTTP_400_BAD_REQUEST,
                'success': False,
                'message': 'Failed to create or retrieve customer.',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            current_subscription = Subscription.objects.filter(
                user=user, 
                is_active=True,
                payment_method='stripe'
            ).first()
            stripe_subscription = None

            if current_subscription and current_subscription.stripe_subscription_id:
                try:
                    stripe_subscription = stripe.Subscription.retrieve(current_subscription.stripe_subscription_id)
                except stripe.error.InvalidRequestError:
                    # Subscription doesn't exist in Stripe, treat as no subscription
                    current_subscription = None
                    stripe_subscription = None
        except Exception as e:
            current_subscription = None
            stripe_subscription = None

        if stripe_subscription:
            try:
                stripe.Subscription.modify(
                    stripe_subscription.id,
                    items=[{
                        'id': stripe_subscription['items']['data'][0].id,
                        'price': package.stripe_price_id
                    }],
                    proration_behavior='create_prorations',
                )
                update_subscription = stripe.Subscription.retrieve(stripe_subscription.id)
                current_subscription.is_active = False
                current_subscription.save()

                # Calculate end_date with fallback
                end_date = None
                if hasattr(update_subscription, 'current_period_end') and update_subscription.current_period_end:
                    end_date = datetime.fromtimestamp(update_subscription.current_period_end, tz=timezone.utc)
                else:
                    # Fallback: calculate based on package interval
                    from django.utils import timezone as django_timezone
                    start_date = django_timezone.now()
                    if package.interval == 'month':
                        end_date = start_date + timedelta(days=30)
                    elif package.interval == 'year':
                        end_date = start_date + timedelta(days=365)
                    elif package.interval == 'week':
                        end_date = start_date + timedelta(days=7)
                    elif package.interval == 'daily':
                        end_date = start_date + timedelta(days=1)
                    else:
                        end_date = start_date + timedelta(days=30)  # default to 30 days

                new_subscription = Subscription.objects.create(
                    user=user,
                    package=package,
                    payment_method='stripe',
                    stripe_subscription_id=update_subscription.id,
                    end_date=end_date,
                    is_active=True,
                )
                return Response({
                    'status': status.HTTP_200_OK,
                    'success': True,
                    'message': 'Subscription updated successfully.',
                    'data': SubscriptionSerializer(new_subscription).data
                }, status=status.HTTP_200_OK)
            except stripe.error.StripeError as e:
                return Response({
                    'status': status.HTTP_400_BAD_REQUEST,
                    'success': False,
                    'message': 'Failed to update subscription.',
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    mode='subscription',
                    line_items=[{'price': package.stripe_price_id, 'quantity': 1}],
                    customer=stripe_customer.id,
                    success_url=settings.STRIPE_SUCCESS_URL,
                    cancel_url=settings.STRIPE_CANCEL_URL,
                    metadata={
                        'package_id': str(package_id),
                        'user_id': str(user.id)
                    },
                    subscription_data={
                        'metadata': {
                            'user_id': str(user.id),
                            'package_id': str(package_id),
                        }
                    }
                )
                return Response({
                    'status': status.HTTP_200_OK,
                    'success': True,
                    'message': 'Checkout session created successfully.',
                    'data': {
                        'checkout_url': checkout_session.url,
                        'session_id': checkout_session.id,
                        'success_url': settings.STRIPE_SUCCESS_URL,
                        'cancel_url': settings.STRIPE_CANCEL_URL,
                    }
                }, status=status.HTTP_200_OK)
            except stripe.error.StripeError as e:
                return Response({
                    'status': status.HTTP_400_BAD_REQUEST,
                    'success': False,
                    'message': 'Failed to create checkout session.',
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)



@csrf_exempt
def stripe_webhook_view(request):
    """Handle Stripe webhook events."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_KEY
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    except ValueError:
        return HttpResponse(status=400)
    
    if event['type'] == 'customer.subscription.created':
        data = event['data']['object']
        metadata = data.get('metadata', {})
        user_id = metadata.get('user_id')
        package_id = metadata.get('package_id')
        stripe_subscription_id = data.get('id')

        try:
            user = User.objects.get(id=user_id)
            package = Package.objects.get(id=package_id)
            
            # Deactivate existing Stripe subscriptions
            Subscription.objects.filter(
                user=user,
                is_active=True,
                payment_method='stripe'
            ).update(is_active=False)

            # Get end_date from webhook or fetch from Stripe
            end_date = None
            if 'current_period_end' in data:
                end_date = datetime.fromtimestamp(data['current_period_end'], tz=timezone.utc)
            else:
                # Fetch full subscription details from Stripe
                try:
                    stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
                    if hasattr(stripe_subscription, 'current_period_end'):
                        end_date = datetime.fromtimestamp(stripe_subscription.current_period_end, tz=timezone.utc)
                except stripe.error.StripeError:
                    pass
            
            # If still no end_date, calculate from package interval
            if end_date is None:
                start_date = timezone.now()
                if package.interval == 'month':
                    end_date = start_date + timedelta(days=30)
                elif package.interval == 'year':
                    end_date = start_date + timedelta(days=365)
                elif package.interval == 'week':
                    end_date = start_date + timedelta(days=7)
                elif package.interval == 'daily':
                    end_date = start_date + timedelta(days=1)
                else:
                    end_date = start_date + timedelta(days=30)  # default to 30 days

            Subscription.objects.create(
                user=user,
                package=package,
                payment_method='stripe',
                stripe_subscription_id=stripe_subscription_id,
                end_date=end_date,
                is_active=True,
            )
        except (User.DoesNotExist, Package.DoesNotExist):
            return HttpResponse(status=400)
        except Exception:
            return HttpResponse(status=400)
            
    elif event['type'] == 'customer.subscription.updated':
        data = event['data']['object']
        stripe_subscription_id = data.get('id')

        try:
            update_data = {
                'is_active': (data.get('status') == 'active')
            }
            
            # Only update end_date if present
            if 'current_period_end' in data:
                update_data['end_date'] = datetime.fromtimestamp(data['current_period_end'])
            
            Subscription.objects.filter(
                stripe_subscription_id=stripe_subscription_id
            ).update(**update_data)
        except Exception:
            pass
            
    elif event['type'] == 'customer.subscription.deleted':
        data = event['data']['object']
        stripe_subscription_id = data['id']
        
        try:
            Subscription.objects.filter(
                stripe_subscription_id=stripe_subscription_id
            ).update(is_active=False)
        except Exception:
            pass
            
    return HttpResponse(status=200)

class CancelSubscription(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication] 

    def post(self, request, subscription_id):
        user = request.user
        subscription = Subscription.objects.get(pk=subscription_id, user=user)

        try:
            if subscription.payment_method == 'stripe':
                stripe.Subscription.delete(subscription.stripe_subscription_id)
            elif subscription.payment_method == 'paypal':
                access_token = get_paypal_access_token()
                if access_token:
                    paypal_api_request(
                        'POST',
                        f'/v1/billing/subscriptions/{subscription.paypal_subscription_id}/cancel',
                        data={"reason": "User requested cancellation"},
                        access_token=access_token
                    )

            subscription.is_active = False
            subscription.save()
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'message': 'Subscription cancelled successfully.',
            }, status=status.HTTP_200_OK)

        except stripe.error.InvalidRequestError as e:
            return Response({
                'status': status.HTTP_400_BAD_REQUEST,
                'success': False,
                'message': 'Failed to cancel subscription.',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except stripe.error.RateLimitError as e:
            return Response({
                'status': status.HTTP_429_TOO_MANY_REQUESTS,
                'success': False,
                'message': 'Failed to cancel subscription.',
                'error': str(e)
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        except Exception as e:
            return Response({
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'success': False,
                'message': 'An error occurred while cancelling subscription.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    


class PayPalSubscriptionCreate(APIView):
    """Create PayPal subscription."""
    
    def post(self, request, package_id):
        user = request.user
        package = Package.objects.get(id=package_id)
        
        if not package.paypal_plan_id:
            return Response({
                'status': status.HTTP_400_BAD_REQUEST,
                'success': False,
                'message': 'PayPal plan not configured for this package.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        access_token = get_paypal_access_token()
        if not access_token:
            return Response({
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'success': False,
                'message': 'Failed to authenticate with PayPal.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Create PayPal subscription
        subscription_data = {
            "plan_id": package.paypal_plan_id,
            "subscriber": {
                "name": {
                    "given_name": user.first_name,
                    "surname": user.last_name
                },
                "email_address": user.email
            },
            "application_context": {
                "brand_name": settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else "Fitness App",
                "locale": "en-US",
                "shipping_preference": "NO_SHIPPING",
                "user_action": "SUBSCRIBE_NOW",
                "payment_method": {
                    "payer_selected": "PAYPAL",
                    "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED"
                },
                "return_url": settings.PAYPAL_SUCCESS_URL,
                "cancel_url": settings.PAYPAL_CANCEL_URL
            },
            "custom_id": f"{user.id}_{package_id}"
        }
        
        result = paypal_api_request('POST', '/v1/billing/subscriptions', subscription_data, access_token)
        
        if result:
            # Get approval link
            approval_link = None
            for link in result.get('links', []):
                if link.get('rel') == 'approve':
                    approval_link = link.get('href')
                    break
            
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'message': 'PayPal subscription created successfully.',
                'data': {
                    'subscription_id': result.get('id'),
                    'approval_url': approval_link,
                    'status': result.get('status')
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': status.HTTP_400_BAD_REQUEST,
                'success': False,
                'message': 'Failed to create PayPal subscription.'
            }, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def paypal_webhook_view(request):
    """Handle PayPal webhook events."""
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    try:
        webhook_data = json.loads(request.body)
        event_type = webhook_data.get('event_type')
        resource = webhook_data.get('resource', {})
        
        # Verify webhook signature (optional but recommended)
        # TODO: Implement webhook signature verification
        
        if event_type == 'BILLING.SUBSCRIPTION.ACTIVATED':
            # Subscription activated after payment
            subscription_id = resource.get('id')
            custom_id = resource.get('custom_id', '')
            
            if custom_id:
                user_id, package_id = custom_id.split('_')
                user = User.objects.get(id=user_id)
                package = Package.objects.get(id=package_id)
                
                # Deactivate existing subscriptions
                Subscription.objects.filter(user=user, is_active=True).update(is_active=False)
                
                # Create new subscription
                Subscription.objects.create(
                    user=user,
                    package=package,
                    payment_method='paypal',
                    paypal_subscription_id=subscription_id,
                    is_active=True
                )
        
        elif event_type == 'BILLING.SUBSCRIPTION.CANCELLED':
            subscription_id = resource.get('id')
            Subscription.objects.filter(
                paypal_subscription_id=subscription_id
            ).update(is_active=False)
        
        elif event_type == 'BILLING.SUBSCRIPTION.SUSPENDED':
            subscription_id = resource.get('id')
            Subscription.objects.filter(
                paypal_subscription_id=subscription_id
            ).update(is_active=False)
        
        elif event_type == 'BILLING.SUBSCRIPTION.UPDATED':
            subscription_id = resource.get('id')
            # Handle subscription updates if needed
            pass
        
        return HttpResponse(status=200)
    
    except Exception as e:
        return HttpResponse(status=400)


# ============= CMS API Views =============

class PricingSectionView(APIView):
    """Get the active pricing section with all packages and features"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            pricing_section = PricingSection.objects.filter(is_active=True).first()
            
            if not pricing_section:
                # Return default structure if no pricing section exists
                packages = Package.objects.filter(is_active=True).prefetch_related('features')
                return Response({
                    'status': status.HTTP_200_OK,
                    'success': True,
                    'data': {
                        'title': 'Choose Your Plan',
                        'subtitle': '',
                        'background_color': '#1a1a1a',
                        'text_color': '#ffffff',
                        'popular_badge_text': 'Most Popular',
                        'popular_badge_color': '#d4ff00',
                        'free_plan_button_text': 'Get Started Free',
                        'paid_plan_button_text': 'Get Started',
                        'packages': PackageCMSSerializer(packages, many=True).data
                    }
                }, status=status.HTTP_200_OK)
            
            serializer = PricingSectionSerializer(pricing_section)
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'success': False,
                'message': 'Failed to fetch pricing section',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Subscription Packages
class PackageListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            packages = Package.objects.filter(is_active=True).prefetch_related('features')
            serializer = PackageCMSSerializer(packages, many=True, context={'request': request})
            
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'success': False,
                'message': 'Failed to fetch packages',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PackageDetailView(APIView):
    """Get a single package with all features"""
    permission_classes = [AllowAny]
    
    def get(self, request, package_id):
        try:
            package = Package.objects.prefetch_related('features').get(id=package_id, is_active=True)
            serializer = PackageCMSSerializer(package)
            
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Package.DoesNotExist:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'success': False,
                'message': 'Package not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'success': False,
                'message': 'Failed to fetch package',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Subscription Header
class SubscriptionHeaderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # active subscription
        subscription = (Subscription.objects.filter(user=user, is_active=True).select_related('package').order_by('-start_date').first())

        # latest subscription
        if not subscription:
            subscription = (Subscription.objects.filter(user=user).select_related('package').order_by('-start_date').first())

        if not subscription:
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'message': 'No subscription found for this user',
                'data': None
            }, status=status.HTTP_200_OK)

        serializer = SubscriptionHeaderSerializer(subscription)

        return Response({
            'status': status.HTTP_200_OK,
            'success': True,
            'message': 'Subscription header data retrieved successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
