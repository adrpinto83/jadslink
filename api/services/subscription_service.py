import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from models.tenant import Tenant

settings = get_settings()
stripe.api_key = settings.STRIPE_SECRET_KEY

PLAN_LIMITS = {
    "starter": 5,
    "pro": 50,
    "enterprise": -1,  # Unlimited
}


async def create_stripe_customer(tenant: Tenant, db: AsyncSession) -> str:
    """Create a Stripe customer for a tenant."""
    customer = stripe.Customer.create(
        email=tenant.users[0].email,  # Assumes the first user is the owner
        name=tenant.name,
        metadata={"tenant_id": str(tenant.id)},
    )
    tenant.stripe_customer_id = customer.id
    db.add(tenant)
    await db.commit()
    return customer.id
