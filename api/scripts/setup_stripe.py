#!/usr/bin/env python3
"""
Setup script to create Stripe products and prices for JADSlink.

Usage:
    STRIPE_API_KEY=sk_test_xxx python setup_stripe.py

This script creates:
1. Free plan product + price
2. Pro plan product + price
3. Enterprise plan product + price

All prices use lookup_keys for easy identification in webhooks.
"""

import stripe
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings

settings = get_settings()

if not settings.STRIPE_SECRET_KEY or settings.STRIPE_SECRET_KEY.startswith("sk_test_your"):
    print("❌ STRIPE_SECRET_KEY not configured. Set it in .env file.")
    sys.exit(1)

stripe.api_key = settings.STRIPE_SECRET_KEY

PLANS = [
    {
        "id": "free",
        "name": "Free",
        "description": "1 node, 50 tickets/month - Free trial plan for testing",
        "price": 0,  # $0/month
        "interval": "month",
        "lookup_key": "free_plan",
    },
    {
        "id": "pro",
        "name": "Pro",
        "description": "5 nodes, 500 tickets/month - Professional plan",
        "price": 2900,  # $29/month in cents
        "interval": "month",
        "lookup_key": "pro_plan",
    },
    {
        "id": "enterprise",
        "name": "Enterprise",
        "description": "Unlimited nodes and tickets - Custom pricing",
        "price": None,  # Custom pricing
        "interval": None,
        "lookup_key": "enterprise_plan",
    },
]


def setup_stripe():
    """Create Stripe products and prices."""
    print("🔧 Setting up Stripe products and prices...\n")

    created_products = []

    for plan in PLANS:
        try:
            # Check if product already exists
            existing = stripe.Product.list(
                limit=100,
                lookup_keys=[plan["lookup_key"]],
            )

            if existing.data:
                product = existing.data[0]
                print(f"✓ Product already exists: {plan['name']} (ID: {product.id})")
                created_products.append(product)
            else:
                # Create product
                product = stripe.Product.create(
                    name=plan["name"],
                    description=plan["description"],
                    metadata={"plan_id": plan["id"]},
                    lookup_key=plan["lookup_key"],
                )
                print(f"✓ Created product: {plan['name']} (ID: {product.id})")
                created_products.append(product)

            # Create price if not enterprise
            if plan["price"] is not None:
                # Check if price already exists
                prices = stripe.Price.list(
                    product=product.id,
                    limit=10,
                )

                if prices.data:
                    price = prices.data[0]
                    print(
                        f"  ✓ Price already exists: ${plan['price']/100:.2f}/{plan['interval']} "
                        f"(ID: {price.id})"
                    )
                else:
                    # Create price
                    price = stripe.Price.create(
                        product=product.id,
                        unit_amount=plan["price"],
                        currency="usd",
                        recurring={"interval": plan["interval"]},
                        lookup_key=plan["lookup_key"],
                    )
                    print(
                        f"  ✓ Created price: ${plan['price']/100:.2f}/{plan['interval']} "
                        f"(ID: {price.id})"
                    )
            else:
                print(f"  ℹ Enterprise plan uses custom pricing (no default price)")

        except stripe.error.StripeError as e:
            print(f"❌ Error setting up {plan['name']}: {e}")
            return False

    print("\n✅ Stripe setup complete!")
    print("\n📝 Summary:")
    print("  • Free plan: $0/month (1 node, 50 tickets)")
    print("  • Pro plan: $29/month (5 nodes, 500 tickets)")
    print("  • Enterprise plan: Custom pricing (unlimited)")

    print("\n🔗 Next steps:")
    print("  1. Go to https://dashboard.stripe.com/webhooks")
    print("  2. Create endpoint for: POST " + settings.FRONTEND_URL + "/api/v1/webhooks/stripe")
    print("  3. Select events:")
    print("     • customer.subscription.created")
    print("     • customer.subscription.updated")
    print("     • customer.subscription.deleted")
    print("     • checkout.session.completed")
    print("  4. Copy signing secret to .env as STRIPE_WEBHOOK_SECRET")

    return True


if __name__ == "__main__":
    success = setup_stripe()
    sys.exit(0 if success else 1)
