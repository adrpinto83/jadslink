from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import stripe

from database import get_db
from config import get_settings
from models.tenant import Tenant

router = APIRouter()
settings = get_settings()
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/stripe")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None), db: AsyncSession = Depends(get_db)):
    """Receive Stripe webhooks and update subscription status."""
    try:
        event = stripe.Webhook.construct_event(
            payload=await request.body(),
            sig_header=stripe_signature,
            secret=settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail=str(e))
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail=str(e))

    # Handle the event
    if event["type"] == "customer.subscription.updated":
        subscription = event["data"]["object"]
        stripe_customer_id = subscription["customer"]
        plan_tier = subscription["items"]["data"][0]["price"]["lookup_key"]
        subscription_status = subscription["status"]

        result = await db.execute(select(Tenant).where(Tenant.stripe_customer_id == stripe_customer_id))
        tenant = result.scalar_one_or_none()

        if tenant:
            tenant.plan_tier = plan_tier
            tenant.subscription_status = subscription_status
            db.add(tenant)
            await db.commit()

    elif event["type"] == "checkout.session.completed":
        session = event['data']['object']
        stripe_customer_id = session.get('customer')
        client_reference_id = session.get('client_reference_id')

        if client_reference_id:
            result = await db.execute(select(Tenant).where(Tenant.id == client_reference_id))
            tenant = result.scalar_one_or_none()
            if tenant and not tenant.stripe_customer_id:
                tenant.stripe_customer_id = stripe_customer_id
                db.add(tenant)
                await db.commit()

    return {"status": "success"}
