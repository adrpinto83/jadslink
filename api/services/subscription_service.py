import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from config import get_settings
from models.tenant import Tenant
from models.user import User

settings = get_settings()
stripe.api_key = settings.STRIPE_SECRET_KEY

PLAN_LIMITS = {
    "starter": 5,
    "pro": 50,
    "enterprise": -1,  # Unlimited
}


async def create_stripe_customer(tenant: Tenant, db: AsyncSession) -> str:
    """Create a Stripe customer for a tenant."""
    # Get the tenant owner's email explicitly (avoid N+1 lazy-load)
    user_result = await db.execute(
        select(User).where(User.tenant_id == tenant.id).limit(1)
    )
    owner = user_result.scalar_one_or_none()

    if not owner:
        raise ValueError(f"Tenant {tenant.id} has no users")

    customer = stripe.Customer.create(
        email=owner.email,
        name=tenant.name,
        metadata={"tenant_id": str(tenant.id)},
    )
    tenant.stripe_customer_id = customer.id
    db.add(tenant)
    await db.commit()
    return customer.id
