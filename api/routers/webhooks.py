from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import stripe

from database import get_db
from config import get_settings
from models.tenant import Tenant, PlanTier

router = APIRouter()
settings = get_settings()
stripe.api_key = settings.STRIPE_SECRET_KEY

PLAN_TIER_MAP = {
    "starter_plan": PlanTier.starter,
    "pro_plan": PlanTier.pro,
    "enterprise_plan": PlanTier.enterprise,
}


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Receive Stripe webhooks and update subscription status."""
    try:
        event = stripe.Webhook.construct_event(
            payload=await request.body(),
            sig_header=stripe_signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    event_type = event["type"]
    data_object = event["data"]["object"]

    if event_type in (
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        subscription = data_object
        stripe_customer_id = subscription["customer"]
        subscription_status = subscription["status"]
        
        lookup_key = None
        if subscription.get("items") and subscription["items"].get("data"):
            lookup_key = subscription["items"]["data"][0]["price"]["lookup_key"]
        
        plan_tier = PLAN_TIER_MAP.get(lookup_key) if lookup_key else None


        result = await db.execute(
            select(Tenant).where(Tenant.stripe_customer_id == stripe_customer_id)
        )
        tenant = result.scalar_one_or_none()

        if tenant:
            if plan_tier:
                tenant.plan_tier = plan_tier
            tenant.subscription_status = subscription_status
            db.add(tenant)
            await db.commit()

    elif event_type == "checkout.session.completed":
        session = data_object
        stripe_customer_id = session.get("customer")
        client_reference_id = session.get("client_reference_id")

        if client_reference_id:
            result = await db.execute(
                select(Tenant).where(Tenant.id == client_reference_id)
            )
            tenant = result.scalar_one_or_none()
            if tenant and not tenant.stripe_customer_id:
                tenant.stripe_customer_id = stripe_customer_id
                db.add(tenant)
                await db.commit()

    return {"status": "success"}
