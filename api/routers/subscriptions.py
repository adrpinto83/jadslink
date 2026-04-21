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
    # Prices are defined in the Stripe dashboard
    try:
        prices = stripe.Price.list(lookup_keys=["starter_plan", "pro_plan"], expand=["data.product"])
        return prices.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
