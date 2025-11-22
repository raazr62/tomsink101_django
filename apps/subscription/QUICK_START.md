# Quick Start - Dual Payment Setup

## Step 1: Environment Variables

Create or update your `.env` file:

```env
# Stripe (existing)
STRIPE_SECRET_KEY=sk_test_51xxxxx
STRIPE_WEBHOOK_KEY=whsec_xxxxx

# PayPal (new)
PAYPAL_CLIENT_ID=AxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxZg
PAYPAL_CLIENT_SECRET=ExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxUg
PAYPAL_MODE=sandbox
```

## Step 2: Apply Migrations

```bash
python manage.py migrate
```

## Step 3: Configure Packages in Admin

1. Go to: `http://127.0.0.1:8000/admin/subscription/package/`

2. Create or edit a package:
   - **Name**: Premium Monthly
   - **Price**: 29.99
   - **Interval**: month
   
3. **Stripe Configuration** (expand section):
   - stripe_product_id: `prod_xxxxx` (from Stripe Dashboard)
   - stripe_price_id: `price_xxxxx` (from Stripe Dashboard)
   
4. **PayPal Configuration** (expand section):
   - paypal_product_id: `PROD-xxxxx` (from PayPal Dashboard)
   - paypal_plan_id: `P-xxxxx` (from PayPal Dashboard)

5. Save

## Step 4: Setup Webhooks

### Stripe Webhook:
1. URL: `https://yourdomain.com/api/subscription/webhook/`
2. Events: `customer.subscription.*`

### PayPal Webhook:
1. URL: `https://yourdomain.com/api/subscription/paypal-webhook/`
2. Events: `BILLING.SUBSCRIPTION.*`

## Step 5: Test Endpoints

### Get Packages:
```bash
curl http://127.0.0.1:8000/api/subscription/packages/
```

### Stripe Checkout:
```bash
curl -X POST http://127.0.0.1:8000/api/subscription/subscription/1/checkout/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### PayPal Checkout:
```bash
curl -X POST http://127.0.0.1:8000/api/subscription/subscription/1/paypal-checkout/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Step 6: Frontend Integration

```javascript
// Fetch packages
const packages = await fetch('/api/subscription/packages/');

// User selects payment method
if (paymentMethod === 'stripe') {
  const response = await fetch(`/api/subscription/subscription/${pkgId}/checkout/`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  window.location.href = response.data.checkout_url;
}

if (paymentMethod === 'paypal') {
  const response = await fetch(`/api/subscription/subscription/${pkgId}/paypal-checkout/`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  window.location.href = response.data.approval_url;
}
```

## What Changed?

### Models:
✅ `Package.paypal_product_id` - New field
✅ `Package.paypal_plan_id` - New field
✅ `Subscription.payment_method` - Tracks 'stripe' or 'paypal'
✅ `Subscription.paypal_subscription_id` - New field

### Views:
✅ `PayPalSubscriptionCreate` - New view for PayPal checkout
✅ `paypal_webhook_view` - New webhook handler
✅ `CancelSubscription` - Now supports both payment methods
✅ `stripe_webhook_view` - Updated to set payment_method='stripe'

### URLs:
✅ `/api/subscription/subscription/<id>/paypal-checkout/` - New endpoint
✅ `/api/subscription/paypal-webhook/` - New webhook endpoint

### Settings:
✅ `PAYPAL_CLIENT_ID` - New setting
✅ `PAYPAL_CLIENT_SECRET` - New setting
✅ `PAYPAL_MODE` - New setting (sandbox/live)
✅ `PAYPAL_API_URL` - Auto-configured based on mode

## Troubleshooting

### PayPal returns 401:
- Check `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET`
- Ensure credentials match the mode (sandbox vs live)

### Stripe checkout fails:
- Verify `stripe_price_id` exists in Stripe Dashboard
- Check `STRIPE_SECRET_KEY` is correct

### Webhook not received:
- Ensure URL is publicly accessible (use ngrok for local testing)
- Check webhook events are configured correctly

## Testing with Sandbox

### Stripe:
- Use test card: `4242 4242 4242 4242`
- Any future expiry date
- Any CVC

### PayPal:
1. Create sandbox accounts at: developer.paypal.com
2. Use sandbox buyer account for payment
3. Login at: sandbox.paypal.com

---

That's it! Your app now supports both Stripe and PayPal payments. 🎉
