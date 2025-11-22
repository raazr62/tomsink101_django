# Subscription API Reference

Base URL: `/api/subscription/`

All endpoints require JWT authentication unless specified otherwise.

---

## Packages

### List All Packages
Get all available subscription packages.

**Endpoint:** `GET /api/subscription/packages/`

**Authentication:** Not required (public)

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
      "description": "Full access to all features",
      "interval": "month",
      "stripe_product_id": "prod_xxxxx",
      "stripe_price_id": "price_xxxxx",
      "paypal_product_id": "PROD-xxxxx",
      "paypal_plan_id": "P-xxxxx",
      "discount": "16.67",
      "is_active": true
    }
  ]
}
```

---

### Get Single Package
Get details of a specific package.

**Endpoint:** `GET /api/subscription/packages/<id>`

**Authentication:** Not required (public)

**Response:**
```json
{
  "status": 200,
  "success": true,
  "message": "Package retrieved successfully",
  "data": {
    "id": 1,
    "name": "Premium Monthly",
    "price": "29.99",
    "discount_price": "24.99",
    "description": "Full access to all features",
    "interval": "month",
    "is_active": true
  }
}
```

---

## Subscriptions

### Get User Subscriptions
Get all subscriptions for the authenticated user.

**Endpoint:** `GET /api/subscription/subscription/`

**Authentication:** Required (JWT)

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
      "stripe_subscription_id": "sub_xxxxx",
      "paypal_subscription_id": "",
      "is_active": true
    }
  ]
}
```

---

### Get Single Subscription
Get details of a specific subscription.

**Endpoint:** `GET /api/subscription/subscription/<id>`

**Authentication:** Required (JWT)

**Response:**
```json
{
  "status": 200,
  "success": true,
  "message": "Subscription retrieved successfully",
  "data": {
    "id": 1,
    "user": "user@example.com",
    "package": {
      "id": 1,
      "name": "Premium Monthly"
    },
    "payment_method": "paypal",
    "is_active": true
  }
}
```

---

## Stripe Checkout

### Create Stripe Checkout Session
Create a Stripe checkout session for subscription.

**Endpoint:** `POST /api/subscription/subscription/<package_id>/checkout/`

**Authentication:** Required (JWT)

**Request:** None (package_id in URL)

**Success Response:**
```json
{
  "status": 200,
  "success": true,
  "message": "Checkout session created successfully.",
  "data": {
    "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_xxxxx",
    "session_id": "cs_test_xxxxx",
    "success_url": "http://127.0.0.1:8000/package/success",
    "cancel_url": "http://127.0.0.1:8000/package/cancel"
  }
}
```

**Error Response (Package not found):**
```json
{
  "status": 404,
  "success": false,
  "message": "Package not found."
}
```

**Error Response (Stripe not configured):**
```json
{
  "status": 400,
  "success": false,
  "message": "Stripe is not configured for this package."
}
```

**Flow:**
1. Frontend calls this endpoint
2. Backend creates Stripe checkout session
3. Frontend redirects user to `checkout_url`
4. User completes payment on Stripe
5. Stripe sends webhook to `/api/subscription/webhook/`
6. Backend creates subscription record
7. User is redirected to `success_url`

---

## PayPal Checkout

### Create PayPal Subscription
Create a PayPal subscription for a package.

**Endpoint:** `POST /api/subscription/subscription/<package_id>/paypal-checkout/`

**Authentication:** Required (JWT)

**Request:** None (package_id in URL)

**Success Response:**
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

**Error Response (Package not found):**
```json
{
  "status": 404,
  "success": false,
  "message": "Package not found."
}
```

**Error Response (PayPal not configured):**
```json
{
  "status": 400,
  "success": false,
  "message": "PayPal plan not configured for this package."
}
```

**Error Response (PayPal auth failed):**
```json
{
  "status": 500,
  "success": false,
  "message": "Failed to authenticate with PayPal."
}
```

**Flow:**
1. Frontend calls this endpoint
2. Backend creates PayPal subscription
3. Frontend redirects user to `approval_url`
4. User approves payment on PayPal
5. PayPal sends webhook to `/api/subscription/paypal-webhook/`
6. Backend activates subscription record
7. User is redirected to success URL

---

## Cancel Subscription

### Cancel Active Subscription
Cancel a user's active subscription (works for both Stripe and PayPal).

**Endpoint:** `POST /api/subscription/cancel_subscription/<subscription_id>`

**Authentication:** Required (JWT)

**Request:** None (subscription_id in URL)

**Success Response:**
```json
{
  "status": 200,
  "success": true,
  "message": "Subscription cancelled successfully."
}
```

**Error Response (Not found or unauthorized):**
```json
{
  "status": 404,
  "success": false,
  "message": "Not found."
}
```

**Error Response (Stripe error):**
```json
{
  "status": 400,
  "success": false,
  "message": "Failed to cancel subscription.",
  "error": "No such subscription: sub_xxxxx"
}
```

**Notes:**
- Automatically detects payment method (Stripe or PayPal)
- Calls appropriate cancellation API
- Sets `is_active=False` in database
- User can only cancel their own subscriptions

---

## Webhooks

### Stripe Webhook
Handle Stripe subscription events.

**Endpoint:** `POST /api/subscription/webhook/`

**Authentication:** Webhook signature verification

**Events Handled:**
- `customer.subscription.created` - Creates new subscription
- `customer.subscription.updated` - Updates subscription end date and status
- `customer.subscription.deleted` - Deactivates subscription

**Request:** Stripe webhook payload

**Response:** `200 OK` (always, even on errors)

**Setup:**
1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://yourdomain.com/api/subscription/webhook/`
3. Select events: `customer.subscription.*`
4. Copy webhook secret to `STRIPE_WEBHOOK_KEY` in .env

---

### PayPal Webhook
Handle PayPal billing subscription events.

**Endpoint:** `POST /api/subscription/paypal-webhook/`

**Authentication:** None (should implement signature verification)

**Events Handled:**
- `BILLING.SUBSCRIPTION.ACTIVATED` - Activates subscription
- `BILLING.SUBSCRIPTION.CANCELLED` - Deactivates subscription
- `BILLING.SUBSCRIPTION.SUSPENDED` - Deactivates subscription
- `BILLING.SUBSCRIPTION.UPDATED` - Updates subscription details

**Request:** PayPal webhook payload

**Response:** `200 OK` (always, even on errors)

**Setup:**
1. Go to PayPal Developer Dashboard → Applications → Webhooks
2. Add webhook: `https://yourdomain.com/api/subscription/paypal-webhook/`
3. Select events: All `BILLING.SUBSCRIPTION.*` events
4. Save webhook

---

## Data Models

### Package
```typescript
{
  id: number
  name: string
  price: decimal(10,2)
  discount_price: decimal(10,2)
  description: text
  interval: "year" | "month" | "week" | "daily"
  stripe_product_id: string
  stripe_price_id: string
  paypal_product_id: string
  paypal_plan_id: string
  discount: decimal(10,2)
  is_active: boolean
}
```

### Subscription
```typescript
{
  id: number
  user: User
  package: Package
  payment_method: "stripe" | "paypal"
  start_date: datetime
  end_date: datetime
  stripe_subscription_id: string
  paypal_subscription_id: string
  is_active: boolean
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request - Invalid data or payment gateway error |
| 401 | Unauthorized - Missing or invalid JWT token |
| 404 | Not Found - Package or subscription doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded (Stripe) |
| 500 | Internal Server Error - Payment gateway authentication failed |

---

## Rate Limiting

Currently not implemented. Recommended for production:
- 10 requests per minute per user for checkout endpoints
- 100 requests per minute for list endpoints
- No limit for webhooks

---

## Testing

### Stripe Test Data:
**Test Card:** 4242 4242 4242 4242
**Expiry:** Any future date
**CVC:** Any 3 digits
**ZIP:** Any 5 digits

### PayPal Test Data:
**Mode:** Use `PAYPAL_MODE=sandbox` in .env
**Accounts:** Create at developer.paypal.com
**Login:** Use sandbox credentials at sandbox.paypal.com

### Local Testing with Webhooks:
```bash
# Install ngrok
ngrok http 8000

# Use ngrok URL for webhooks
https://abc123.ngrok.io/api/subscription/webhook/
https://abc123.ngrok.io/api/subscription/paypal-webhook/
```

---

## Frontend Examples

### Fetch Packages
```javascript
const response = await fetch('/api/subscription/packages/');
const data = await response.json();
console.log(data.data); // Array of packages
```

### Stripe Checkout
```javascript
const response = await fetch(
  `/api/subscription/subscription/${packageId}/checkout/`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${jwtToken}`,
      'Content-Type': 'application/json'
    }
  }
);
const data = await response.json();
if (data.success) {
  window.location.href = data.data.checkout_url;
}
```

### PayPal Checkout
```javascript
const response = await fetch(
  `/api/subscription/subscription/${packageId}/paypal-checkout/`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${jwtToken}`,
      'Content-Type': 'application/json'
    }
  }
);
const data = await response.json();
if (data.success) {
  window.location.href = data.data.approval_url;
}
```

### Cancel Subscription
```javascript
const response = await fetch(
  `/api/subscription/cancel_subscription/${subscriptionId}`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${jwtToken}`,
      'Content-Type': 'application/json'
    }
  }
);
const data = await response.json();
console.log(data.message);
```

---

## Security Best Practices

1. **Always use HTTPS** in production
2. **Verify webhook signatures** (implement for PayPal)
3. **Validate user permissions** before allowing cancellations
4. **Log all payment attempts** for audit trail
5. **Use environment variables** for sensitive data
6. **Implement rate limiting** on checkout endpoints
7. **Send email notifications** on subscription changes
8. **Monitor webhook failures** and retry logic

---

## Common Issues

### "Package not found" error
- Verify package ID is correct
- Check if package is active (`is_active=True`)

### "Stripe is not configured" error
- Ensure `stripe_price_id` is set for the package
- Verify the price ID exists in Stripe Dashboard

### "PayPal authentication failed" error
- Check `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET`
- Ensure credentials match the mode (sandbox vs live)

### Webhook not received
- Verify webhook URL is publicly accessible
- Check webhook events are configured correctly
- Use ngrok for local testing
- Check server logs for incoming webhook requests

---

## Support

For issues or questions:
1. Check the PAYMENT_INTEGRATION_GUIDE.md
2. Review QUICK_START.md for setup steps
3. Verify environment variables in .env
4. Check Django logs for detailed errors
