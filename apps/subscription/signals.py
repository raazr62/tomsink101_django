from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Package, Subscription
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import stripe
import requests
from base64 import b64encode
import logging

User = get_user_model()

logger = logging.getLogger(__name__)

# 30 Days free trial for new users
@receiver(post_save, sender=User)
def grant_free_pro_trial(sender, instance, created, **kwargs):
    if not created:
        return
    # pick the Pro package by name or fall back to a free package
    pro_pkg = Package.objects.filter(name__iexact="pro").first()
    if not pro_pkg:
        pro_pkg = Package.objects.filter(price=0).first()
    if not pro_pkg:
        return
    if Subscription.objects.filter(user=instance, is_active=True).exists():
        return
    Subscription.objects.create(
        user=instance,
        package=pro_pkg,
        start_date=timezone.now(),
        end_date=timezone.now() + timedelta(days=30),
        is_active=True,
        payment_method="free_trial",
    )

# PayPal Helper Functions
def get_paypal_access_token():
    """Get PayPal OAuth access token."""
    try:
        client_id = settings.PAYPAL_CLIENT_ID
        client_secret = settings.PAYPAL_CLIENT_SECRET
        
        if not client_id or not client_secret:
            return None
        
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
    except Exception:
        pass
    return None


def paypal_api_request(method, endpoint, data=None, access_token=None):
    """Make PayPal API request."""
    try:
        if not access_token:
            access_token = get_paypal_access_token()
        
        if not access_token:
            return None
        
        url = f"{settings.PAYPAL_API_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
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
    except Exception:
        pass
    return None


@receiver(post_save, sender=Package)
def create_stripe_product(sender, instance, created, **kwargs):
    """Create Stripe product and/or price when missing.

    Note: IDs are stored on the Package record. If you change Stripe accounts
    (or switch test/live keys), existing stored IDs may no longer exist.
    Clearing the IDs and saving the package will re-create them.
    """
    if not instance.stripe_product_id and not instance.stripe_price_id and not instance.discount_price:
        # Nothing to sync for free/zero-priced packages
        return

    if not instance.stripe_product_id or not instance.stripe_price_id:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            stripe_product_id = instance.stripe_product_id
            stripe_price_id = instance.stripe_price_id

            if not stripe_product_id:
                stripe_product = stripe.Product.create(
                    name=instance.name,
                    description=instance.description or "",
                )
                stripe_product_id = stripe_product.id

            if not stripe_price_id:
                stripe_price = stripe.Price.create(
                    product=stripe_product_id,
                    currency='USD',
                    unit_amount=int(instance.discount_price * 100),
                    recurring={
                        'interval': instance.interval,
                    },
                )
                stripe_price_id = stripe_price.id

            Package.objects.filter(pk=instance.pk).update(
                stripe_product_id=stripe_product_id,
                stripe_price_id=stripe_price_id,
            )
        except stripe.error.StripeError:
            logger.exception("Stripe sync failed for Package id=%s", instance.pk)


@receiver(post_save, sender=Package)
def create_paypal_product(sender, instance, created, **kwargs):
    """Create PayPal product and billing plan if they don't exist."""
    if created and not instance.paypal_product_id:
        try:
            access_token = get_paypal_access_token()
            if not access_token:
                return
            
            # Create PayPal product
            product_data = {
                "name": instance.name,
                "description": instance.description or instance.name,
                "type": "SERVICE",
                "category": "SOFTWARE"
            }
            
            product = paypal_api_request('POST', '/v1/catalogs/products', product_data, access_token)
            if not product:
                return
            
            instance.paypal_product_id = product.get('id')
            
            # Map interval to PayPal frequency
            interval_map = {
                'month': 'MONTH',
                'year': 'YEAR',
                'week': 'WEEK',
                'daily': 'DAY'
            }
            
            # Create billing plan
            plan_data = {
                "product_id": instance.paypal_product_id,
                "name": f"{instance.name} Plan",
                "description": instance.description or f"{instance.name} subscription plan",
                "billing_cycles": [
                    {
                        "frequency": {
                            "interval_unit": interval_map.get(instance.interval, 'MONTH'),
                            "interval_count": 1
                        },
                        "tenure_type": "REGULAR",
                        "sequence": 1,
                        "total_cycles": 0,  # 0 means infinite
                        "pricing_scheme": {
                            "fixed_price": {
                                "value": str(instance.discount_price),
                                "currency_code": "USD"
                            }
                        }
                    }
                ],
                "payment_preferences": {
                    "auto_bill_outstanding": True,
                    "setup_fee": {
                        "value": "0",
                        "currency_code": "USD"
                    },
                    "setup_fee_failure_action": "CONTINUE",
                    "payment_failure_threshold": 3
                }
            }
            
            plan = paypal_api_request('POST', '/v1/billing/plans', plan_data, access_token)
            if plan:
                instance.paypal_plan_id = plan.get('id')
                
                # Save without triggering signals again
                Package.objects.filter(pk=instance.pk).update(
                    paypal_product_id=instance.paypal_product_id,
                    paypal_plan_id=instance.paypal_plan_id
                )
        except Exception:
            pass


@receiver(post_save, sender=Package)
def update_stripe_product(sender, instance, created, **kwargs):
    """Update Stripe product and price when package is modified."""
    if created or not instance.stripe_product_id:
        return
    
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe_product = stripe.Product.retrieve(instance.stripe_product_id)
        
        # Update product name if changed
        if stripe_product['name'] != instance.name:
            stripe.Product.modify(
                stripe_product.id,
                name=instance.name,
                description=instance.description or ""
            )
        
        # Check if price needs updating
        if instance.stripe_price_id:
            stripe_price = stripe.Price.retrieve(instance.stripe_price_id)
            
            # If price or interval changed, create new price and deactivate old one
            if (stripe_price['unit_amount'] != int(instance.discount_price * 100) or
                stripe_price['recurring']['interval'] != instance.interval):
                
                # Deactivate old price
                stripe.Price.modify(instance.stripe_price_id, active=False)
                
                # Create new price
                new_price = stripe.Price.create(
                    product=instance.stripe_product_id,
                    currency='USD',
                    unit_amount=int(instance.discount_price * 100),
                    recurring={
                        'interval': instance.interval,
                    }
                )
                
                # Update instance without triggering signals
                Package.objects.filter(pk=instance.pk).update(
                    stripe_price_id=new_price.id
                )
    except stripe.error.StripeError:
        logger.exception("Stripe update failed for Package id=%s", instance.pk)


@receiver(post_save, sender=Package)
def update_paypal_product(sender, instance, created, **kwargs):
    """Update PayPal product and plan when package is modified."""
    if created or not instance.paypal_product_id:
        return
    
    try:
        access_token = get_paypal_access_token()
        if not access_token:
            return
        
        # Update PayPal product
        product_update = {
            "description": instance.description or instance.name,
            "category": "SOFTWARE"
        }
        
        paypal_api_request(
            'PATCH',
            f'/v1/catalogs/products/{instance.paypal_product_id}',
            [{"op": "replace", "path": "/description", "value": instance.description or instance.name}],
            access_token
        )
        
        # Note: PayPal billing plans cannot be updated once created
        # If price/interval changes, you need to create a new plan
        # and update the package with the new plan_id
        
    except Exception:
        pass


@receiver(pre_delete, sender=Package)
def delete_stripe_product(sender, instance, **kwargs):
    """Deactivate Stripe product and price when package is deleted."""
    if instance.stripe_product_id:
        try:
            stripe.Product.modify(
                instance.stripe_product_id,
                active=False,
            )
            if instance.stripe_price_id:
                stripe.Price.modify(
                    instance.stripe_price_id,
                    active=False,
                )
        except stripe.error.StripeError:
            pass


@receiver(pre_delete, sender=Package)
def delete_paypal_product(sender, instance, **kwargs):
    """Deactivate PayPal billing plan when package is deleted."""
    if instance.paypal_plan_id:
        try:
            access_token = get_paypal_access_token()
            if access_token:
                # Deactivate the billing plan
                paypal_api_request(
                    'POST',
                    f'/v1/billing/plans/{instance.paypal_plan_id}/deactivate',
                    {},
                    access_token
                )
        except Exception:
            pass
