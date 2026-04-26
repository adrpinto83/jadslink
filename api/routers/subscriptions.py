from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import stripe

from database import get_db
from config import get_settings
from deps import get_current_tenant
from models.tenant import Tenant

router = APIRouter()
settings = get_settings()
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.get("/plans")
async def get_subscription_plans():
    """Get the available SaaS subscription plans."""
    # En desarrollo, retornar datos mock si la clave Stripe no está configurada
    if settings.STRIPE_SECRET_KEY == "sk_test_your_stripe_secret_key" or not settings.STRIPE_SECRET_KEY.startswith("sk_"):
        # Mock data para desarrollo
        return [
            {
                "id": "price_starter",
                "object": "price",
                "billing_scheme": "per_unit",
                "created": 1704067200,
                "currency": "usd",
                "custom_unit_amount": None,
                "lookup_key": "starter_plan",
                "metadata": {
                    "plan_name": "Starter",
                    "max_nodes": "3",
                    "max_tickets": "1000",
                },
                "nickname": "Starter Plan",
                "product": {
                    "id": "prod_starter",
                    "object": "product",
                    "name": "Starter Plan",
                    "description": "3 nodos, 1,000 tickets/mes",
                },
                "recurring": {
                    "aggregate_usage": None,
                    "interval": "month",
                    "interval_count": 1,
                    "trial_period_days": 14,
                    "usage_type": "licensed",
                },
                "type": "recurring",
                "unit_amount": 2900,  # $29/mes
                "unit_amount_decimal": "2900",
            },
            {
                "id": "price_pro",
                "object": "price",
                "billing_scheme": "per_unit",
                "created": 1704067200,
                "currency": "usd",
                "custom_unit_amount": None,
                "lookup_key": "pro_plan",
                "metadata": {
                    "plan_name": "Pro",
                    "max_nodes": "10",
                    "max_tickets": "5000",
                },
                "nickname": "Pro Plan",
                "product": {
                    "id": "prod_pro",
                    "object": "product",
                    "name": "Pro Plan",
                    "description": "10 nodos, 5,000 tickets/mes",
                },
                "recurring": {
                    "aggregate_usage": None,
                    "interval": "month",
                    "interval_count": 1,
                    "trial_period_days": 14,
                    "usage_type": "licensed",
                },
                "type": "recurring",
                "unit_amount": 9900,  # $99/mes
                "unit_amount_decimal": "9900",
            },
        ]

    # Producción: llamar a Stripe API
    try:
        prices = stripe.Price.list(lookup_keys=["starter_plan", "pro_plan"], expand=["data.product"])
        return prices.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error conectando con Stripe: {str(e)}")


@router.post("/checkout-session")
async def create_checkout_session(
    price_id: str,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe Checkout session for a subscription."""
    try:
        # Create Stripe customer if not exists
        if not current_tenant.stripe_customer_id:
            # Get primary user email
            primary_user = current_tenant.users[0] if current_tenant.users else None
            customer = stripe.Customer.create(
                email=primary_user.email if primary_user else "noreply@jadslink.io",
                name=current_tenant.name,
                metadata={"tenant_id": str(current_tenant.id)},
            )
            current_tenant.stripe_customer_id = customer.id
            db.add(current_tenant)
            await db.commit()

        checkout_session = stripe.checkout.Session.create(
            client_reference_id=str(current_tenant.id),
            customer=current_tenant.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=f"{settings.FRONTEND_URL}/billing?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/billing",
        )
        return {"sessionId": checkout_session.id}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portal-session")
async def create_portal_session(current_tenant: Tenant = Depends(get_current_tenant)):
    """Create a Stripe Customer Portal session."""
    if not current_tenant.stripe_customer_id:
        raise HTTPException(status_code=400, detail="Cliente de Stripe no encontrado para este operador.")
    
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=current_tenant.stripe_customer_id,
            return_url=f"{settings.FRONTEND_URL}/billing",
        )
        return {"url": portal_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
