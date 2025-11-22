# Payment Integration Guide - Stripe & PayPal

## Overview
The subscription app now supports both **Stripe** and **PayPal** payment methods. Users can choose their preferred payment gateway when subscribing to packages.

---

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx
STRIPE_WEBHOOK_KEY=whsec_xxxxxxxxxxxxx

# PayPal Configuration
PAYPAL_CLIENT_ID=xxxxxxxxxxxxx
PAYPAL_CLIENT_SECRET=xxxxxxxxxxxxx
PAYPAL_MODE=sandbox  # Use 'live' for production
```

### Settings Configuration

Already configured in `project/settings.py`:

```python
# Stripe
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_KEY = config('STRIPE_WEBHOOK_KEY')
STRIPE_SUCCESS_URL = 'http://127.0.0.1:8000/package/success'
STRIPE_CANCEL_URL = 'http://127.0.0.1:8000/package/cancel'

# PayPal
PAYPAL_CLIENT_ID = config('PAYPAL_CLIENT_ID', default='')
PAYPAL_CLIENT_SECRET = config('PAYPAL_CLIENT_SECRET', default='')
PAYPAL_MODE = config('PAYPAL_MODE', default='sandbox')
PAYPAL_API_URL = 'https://api-m.sandbox.paypal.com'  # or live
PAYPAL_SUCCESS_URL = 'http://127.0.0.1:8000/package/paypal-success'
PAYPAL_CANCEL_URL = 'http://127.0.0.1:8000/package/paypal-cancel'
```

---

## API Endpoints

### 1. Get All Packages
```http
GET /api/subscription/packages/
Authorization: Bearer <JWT_TOKEN>
```

**Response:**
```json
{
  "status": 200,
  "success": true,
  "message": "All packages retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "Premium Monthly",
      "price": "29.99",
      "discount_price": "24.99",
      "description": "Access to all features",
      "interval": "month",
      "stripe_product_id": "prod_xxxxx",
      "stripe_price_id": "price_xxxxx",
      "paypal_product_id": "PROD-xxxxx",
      "paypal_plan_id": "P-xxxxx",
      "is_active": true
    }
  ]
}
```

---

### 2. Create Stripe Subscription
```http
POST /api/subscription/subscription/<package_id>/checkout/
Authorization: Bearer <JWT_TOKEN>
```

**Response:**
```json
{
  "status": 200,
  "success": true,
  "message": "Checkout session created successfully.",
  "data": {
    "url": "https://checkout.stripe.com/pay/cs_test_xxxxx",
    "success_url": "http://127.0.0.1:8000/package/success",
    "cancel_url": "http://127.0.0.1:8000/package/cancel"
  }
}
```

**Flow:**
1. User clicks subscribe button
2. API creates Stripe checkout session
3. User is redirected to `url` for payment
4. After payment, Stripe sends webhook to `/api/subscription/webhook/`
5. Webhook creates `Subscription` record with `payment_method='stripe'`

---

### 3. Create PayPal Subscription
```http
POST /api/subscription/subscription/<package_id>/paypal-checkout/
Authorization: Bearer <JWT_TOKEN>
```

**Response:**
```json
{
  "status": 200,
  "success": true,
  "message": "PayPal subscription created successfully.",
  "data": {
    "subscription_id": "I-xxxxxxxxxxxxx",
    "approval_url": "https://www.sandbox.paypal.com/checkoutnow?token=xxxxx",
    "status": "APPROVAL_PENDING"
  }
}
```

**Flow:**
1. User clicks PayPal subscribe button
2. API creates PayPal subscription
3. User is redirected to `approval_url` for payment
4. After approval, PayPal sends webhook to `/api/subscription/paypal-webhook/`
5. Webhook activates `Subscription` record with `payment_method='paypal'`

---

### 4. Cancel Subscription
```http
POST /api/subscription/cancel_subscription/<subscription_id>
Authorization: Bearer <JWT_TOKEN>
```

**Response:**
```json
{
  "status": 200,
  "success": true,
  "message": "Subscription cancelled successfully."
}
```

**Supports both Stripe and PayPal subscriptions automatically.**

---

### 5. Get User Subscriptions
```http
GET /api/subscription/subscription/
Authorization: Bearer <JWT_TOKEN>
```

**Response:**
```json
{
  "status": 200,
  "success": true,
  "message": "All subscriptions retrieved successfully",
  "data": [
    {
      "id": 1,
      "user": "user@example.com",
      "package": {
        "id": 1,
        "name": "Premium Monthly",
        "price": "29.99"
      },
      "payment_method": "stripe",
      "start_date": "2025-11-22T10:00:00Z",
      "end_date": "2025-12-22T10:00:00Z",
      "is_active": true
    }
  ]
}
```

---

## Database Models

### Package Model
```python
class Package(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    interval = models.CharField(max_length=10)  # year/month/week/daily
    
    # Stripe IDs
    stripe_product_id = models.CharField(max_length=100)
    stripe_price_id = models.CharField(max_length=100)
    
    # PayPal IDs
    paypal_product_id = models.CharField(max_length=100)
    paypal_plan_id = models.CharField(max_length=100)
    
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
```

### Subscription Model
```python
class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    
    # Payment tracking
    payment_method = models.CharField(
        max_length=20,
        choices=[('stripe', 'Stripe'), ('paypal', 'PayPal')]
    )
    stripe_subscription_id = models.CharField(max_length=100)
    paypal_subscription_id = models.CharField(max_length=100)
    
    is_active = models.BooleanField(default=False)
```

---

## Webhook Setup

### Stripe Webhook
**URL:** `https://yourdomain.com/api/subscription/webhook/`

**Events to subscribe:**
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`

**Setup:**
1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint with above URL
3. Copy webhook secret to `STRIPE_WEBHOOK_KEY`

---

### PayPal Webhook
**URL:** `https://yourdomain.com/api/subscription/paypal-webhook/`

**Events to subscribe:**
- `BILLING.SUBSCRIPTION.ACTIVATED`
- `BILLING.SUBSCRIPTION.CANCELLED`
- `BILLING.SUBSCRIPTION.SUSPENDED`
- `BILLING.SUBSCRIPTION.UPDATED`

**Setup:**
1. Go to PayPal Developer → Applications → Webhooks
2. Add webhook with above URL
3. Subscribe to billing subscription events

---

## Setting Up Packages

### For Stripe Packages:
1. Create product in Stripe Dashboard
2. Create recurring price for the product
3. Copy `product_id` → `stripe_product_id`
4. Copy `price_id` → `stripe_price_id`

### For PayPal Packages:
1. Create product in PayPal Dashboard
2. Create billing plan for the product
3. Copy product ID → `paypal_product_id`
4. Copy plan ID → `paypal_plan_id`

### Using Admin Panel:
1. Go to `/admin/subscription/package/`
2. Create or edit a package
3. Fill in both Stripe and PayPal IDs
4. Set price and interval

---

## Frontend Integration

### Example: Package Selection Page

```javascript
// Fetch packages
fetch('/api/subscription/packages/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(res => res.json())
.then(data => {
  // Display packages with both payment options
  data.data.forEach(package => {
    console.log(package.name, package.price);
    // Show "Pay with Stripe" button
    // Show "Pay with PayPal" button
  });
});
```

### Example: Stripe Checkout

```javascript
// User clicks "Pay with Stripe"
fetch(`/api/subscription/subscription/${packageId}/checkout/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(res => res.json())
.then(data => {
  // Redirect to Stripe checkout
  window.location.href = data.data.url;
});
```

### Example: PayPal Checkout

```javascript
// User clicks "Pay with PayPal"
fetch(`/api/subscription/subscription/${packageId}/paypal-checkout/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(res => res.json())
.then(data => {
  // Redirect to PayPal approval
  window.location.href = data.data.approval_url;
});
```

---

## Testing

### Stripe Test Cards:
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`

### PayPal Test Accounts:
- Create sandbox accounts in PayPal Developer Dashboard
- Use sandbox business account for receiving payments
- Use sandbox personal account for making payments

---

## Security Considerations

### ✅ Implemented:
- CSRF protection on webhooks
- JWT authentication on API endpoints
- User validation (can only manage own subscriptions)
- Payment method tracking

### 🔄 Recommended:
- Webhook signature verification for PayPal
- Rate limiting on payment endpoints
- Logging payment attempts
- Email notifications on subscription changes

---

## Common Issues & Solutions

### Issue: PayPal webhook not working
**Solution:** Ensure `PAYPAL_MODE` is set correctly (sandbox vs live) and webhook URL is publicly accessible.

### Issue: Stripe webhook signature verification fails
**Solution:** Check that `STRIPE_WEBHOOK_KEY` matches the webhook secret in Stripe Dashboard.

### Issue: Package doesn't have PayPal/Stripe IDs
**Solution:** Configure both payment gateways in admin panel or set up products/plans in respective dashboards.

---

## Migration Notes

Existing Stripe subscriptions will continue to work. The new fields are:
- `Package.paypal_product_id`
- `Package.paypal_plan_id`
- `Subscription.payment_method`
- `Subscription.paypal_subscription_id`

All existing subscriptions will have `payment_method='stripe'` by default.

---

## Summary

✅ **Dual Payment Support**: Users can choose Stripe or PayPal
✅ **Unified API**: Same endpoints, different payment flows
✅ **Webhook Handling**: Automatic subscription activation
✅ **Admin Panel**: Easy configuration of both gateways
✅ **Flexible**: Can enable/disable payment methods per package
✅ **Backward Compatible**: Existing Stripe subscriptions work unchanged
