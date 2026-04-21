# Stripe Setup Guide

Complete guide to configure Stripe for JADSlink SaaS subscriptions.

## Overview

JADSlink uses Stripe for subscription management with 3 tiers:

| Plan | Nodes | Tickets/mo | Price |
|------|-------|-----------|-------|
| Free | 1 | 50 | $0 |
| Pro | 5 | 500 | $29 |
| Enterprise | ∞ | ∞ | Custom |

## Prerequisites

- Stripe account (https://dashboard.stripe.com)
- Stripe API keys (Secret and Publishable)
- JADSlink backend running locally or in production

## Step 1: Get Stripe API Keys

1. Go to https://dashboard.stripe.com/apikeys
2. Copy your **Secret Key** (starts with `sk_live_` or `sk_test_`)
3. Copy your **Publishable Key** (starts with `pk_live_` or `pk_test_`)

## Step 2: Configure Environment Variables

Update `.env` file:

```bash
STRIPE_SECRET_KEY=sk_test_YOUR_SECRET_KEY
STRIPE_PUBLIC_KEY=pk_test_YOUR_PUBLIC_KEY
```

For production, use `sk_live_*` and `pk_live_*` keys.

## Step 3: Create Stripe Products and Prices

Run the setup script:

```bash
cd api
python scripts/setup_stripe.py
```

This creates:
- **Free Product**: $0/month (lookup_key: `free_plan`)
- **Pro Product**: $29/month (lookup_key: `pro_plan`)
- **Enterprise Product**: Custom (lookup_key: `enterprise_plan`)

✅ You should see confirmation messages for each product created.

### Manual Setup (Alternative)

If you prefer to create products manually in Stripe Dashboard:

1. Go to https://dashboard.stripe.com/products
2. Click **+ Create Product**
3. Create 3 products with exact details:

**Product 1: Free**
- Name: `Free`
- Description: `1 node, 50 tickets/month - Free trial plan for testing`
- Pricing:
  - Amount: `$0.00`
  - Billing period: `Monthly`
  - Lookup key: `free_plan`

**Product 2: Pro**
- Name: `Pro`
- Description: `5 nodes, 500 tickets/month - Professional plan`
- Pricing:
  - Amount: `$29.00`
  - Billing period: `Monthly`
  - Lookup key: `pro_plan`

**Product 3: Enterprise**
- Name: `Enterprise`
- Description: `Unlimited nodes and tickets - Custom pricing`
- Pricing:
  - No standard price (custom per customer)
  - Lookup key: `enterprise_plan`

## Step 4: Configure Webhook Endpoint

1. Go to https://dashboard.stripe.com/webhooks
2. Click **Add Endpoint**
3. Enter your endpoint URL:
   ```
   https://your-domain.com/api/v1/webhooks/stripe
   ```
   - For local testing: use ngrok or Stripe CLI
4. Select events to listen to:
   - ✅ `customer.subscription.created`
   - ✅ `customer.subscription.updated`
   - ✅ `customer.subscription.deleted`
   - ✅ `checkout.session.completed`
5. Copy the **Signing Secret** (starts with `whsec_`)
6. Update `.env`:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_YOUR_SIGNING_SECRET
   ```

## Step 5: Test Webhook Locally (with Stripe CLI)

1. Install Stripe CLI: https://stripe.com/docs/stripe-cli
2. Login:
   ```bash
   stripe login
   ```
3. Forward webhooks to local:
   ```bash
   stripe listen --forward-to http://localhost:8000/api/v1/webhooks/stripe
   ```
4. Copy the signing secret and update `.env`:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_test_xxxxx
   ```

## Step 6: Verify Integration

### Test Checkout Flow

```bash
# 1. Get a JWT token for a user
TOKEN="your_jwt_token"

# 2. Create checkout session
curl -X POST http://localhost:8000/api/v1/subscriptions/checkout-session \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"price_id": "price_1234"}'

# Response should include sessionId
```

### Test Webhook

```bash
# Using Stripe CLI (after setup):
stripe trigger customer.subscription.created

# You should see webhook event in:
# - Stripe Dashboard: Webhooks → Events
# - Backend logs: INFO: Webhook processed
# - Database: tenants table updated with new subscription_status
```

### Test Backend

Run tests:

```bash
cd api
pytest tests/test_subscriptions.py -v
```

All tests should pass ✅

## Environment Variables Reference

```bash
# Required
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Optional
STRIPE_ENDPOINT_SECRET=whsec_...  # Alternative name for webhook secret
```

## API Endpoints

### Subscriptions

**GET** `/api/v1/subscriptions/plans`
- Get available subscription plans
- Public endpoint (no auth required)

**POST** `/api/v1/subscriptions/checkout-session`
- Create Stripe Checkout session for subscription
- Requires: JWT token, `price_id` query param
- Returns: `{ "sessionId": "cs_..." }`

**GET** `/api/v1/subscriptions/portal-session`
- Create Stripe Customer Portal session
- Requires: JWT token
- Returns: `{ "url": "https://billing.stripe.com/..." }`

### Webhooks

**POST** `/api/v1/webhooks/stripe`
- Receive Stripe webhook events
- Requires: `Stripe-Signature` header
- Events handled:
  - `customer.subscription.created` → Update tenant plan_tier
  - `customer.subscription.updated` → Update subscription_status
  - `customer.subscription.deleted` → Set subscription_status to "canceled"
  - `checkout.session.completed` → Link stripe_customer_id to tenant

## Troubleshooting

### "STRIPE_SECRET_KEY not configured"
- Check `.env` file contains correct key
- Key should start with `sk_test_` (test) or `sk_live_` (production)

### Webhook not received
- Verify endpoint URL is publicly accessible
- Check webhook logs in Stripe Dashboard
- Confirm signing secret matches `.env`
- For local testing, use Stripe CLI: `stripe listen --forward-to ...`

### Checkout fails with "Invalid price_id"
- Verify price exists in Stripe Dashboard
- Check price ID matches (starts with `price_`)
- Confirm product has correct lookup_key

### Subscription not updating after payment
- Check webhook is properly configured
- Verify STRIPE_WEBHOOK_SECRET is set
- Check backend logs for webhook processing errors
- Manually trigger webhook test in Stripe Dashboard

## Production Deployment

When deploying to production:

1. Update environment variables to use `sk_live_*` keys
2. Update webhook endpoint to production URL
3. Re-run setup script or update Stripe products:
   ```bash
   STRIPE_API_KEY=sk_live_... python scripts/setup_stripe.py
   ```
4. Test full checkout flow end-to-end
5. Monitor webhook delivery in Stripe Dashboard

## Security Notes

⚠️ **Important:**
- Never commit API keys to git
- Use `.env.local` or environment variables
- Rotate webhook signing secrets regularly
- Validate all webhook signatures (already done in code)
- Use HTTPS in production (required by Stripe)
- Implement rate limiting (already in place for auth endpoints)

## References

- [Stripe Dashboard](https://dashboard.stripe.com)
- [Stripe API Docs](https://stripe.com/docs/api)
- [Stripe Webhooks](https://stripe.com/docs/webhooks)
- [Stripe CLI](https://stripe.com/docs/stripe-cli)
- [Stripe Checkout](https://stripe.com/docs/payments/checkout)

## Support

For issues:
1. Check Stripe Dashboard → Logs
2. Check backend logs: `docker compose logs api`
3. Verify webhook endpoint accessibility
4. Test with Stripe CLI: `stripe events resend <event_id>`
