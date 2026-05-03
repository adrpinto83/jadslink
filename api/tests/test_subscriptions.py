"""
Tests for subscription endpoints (Stripe integration)
"""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.tenant import Tenant, PlanTier, SubscriptionStatus
from models.user import User
from database import async_session_maker


@pytest.fixture
async def test_tenant_with_user(db: AsyncSession):
    """Create a test tenant and user."""
    tenant = Tenant(
        id=uuid4(),
        name="Test Operator",
        slug="test-operator",
        is_active=True,
        plan_tier=PlanTier.starter,
        subscription_status=SubscriptionStatus.trialing,
    )
    db.add(tenant)

    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        role="operator",
        tenant_id=tenant.id,
        is_active=True,
    )
    db.add(user)
    await db.commit()

    return tenant, user


@pytest.mark.asyncio
async def test_get_subscription_plans():
    """Test getting available subscription plans."""
    with patch("stripe.Price.list") as mock_list:
        mock_list.return_value.data = [
            MagicMock(
                id="price_free",
                unit_amount=0,
                currency="usd",
                product=MagicMock(id="prod_free", name="Free"),
                recurring=MagicMock(interval="month"),
            ),
            MagicMock(
                id="price_pro",
                unit_amount=2900,
                currency="usd",
                product=MagicMock(id="prod_pro", name="Pro"),
                recurring=MagicMock(interval="month"),
            ),
        ]

        from main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/subscriptions/plans",
            )

            assert response.status_code == 200
            plans = response.json()
            assert len(plans) == 2
            assert plans[0]["unit_amount"] == 0
            assert plans[1]["unit_amount"] == 2900


@pytest.mark.asyncio
async def test_create_checkout_session(test_tenant_with_user, db: AsyncSession):
    """Test creating a Stripe checkout session."""
    tenant, user = test_tenant_with_user

    # Create a valid JWT token for the user
    from deps import get_current_user
    from config import get_settings
    from jose import jwt

    settings = get_settings()
    token = jwt.encode(
        {"sub": str(user.id)},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    with patch("stripe.checkout.Session.create") as mock_create:
        mock_create.return_value = MagicMock(
            id="cs_test_123",
            url="https://checkout.stripe.com/pay/cs_test_123",
        )

        from main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/subscriptions/checkout-session",
                params={"price_id": "price_pro"},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "sessionId" in data
            assert data["sessionId"] == "cs_test_123"


@pytest.mark.asyncio
async def test_create_portal_session(test_tenant_with_user, db: AsyncSession):
    """Test creating a Stripe customer portal session."""
    tenant, user = test_tenant_with_user
    tenant.stripe_customer_id = "cus_test_123"
    await db.commit()

    from config import get_settings
    from jose import jwt

    settings = get_settings()
    token = jwt.encode(
        {"sub": str(user.id)},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    with patch("stripe.billing_portal.Session.create") as mock_create:
        mock_create.return_value = MagicMock(
            url="https://billing.stripe.com/session/test"
        )

        from main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/subscriptions/portal-session",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "url" in data


@pytest.mark.asyncio
async def test_portal_session_without_customer_id(
    test_tenant_with_user, db: AsyncSession
):
    """Test portal session creation without stripe_customer_id."""
    tenant, user = test_tenant_with_user
    # tenant.stripe_customer_id is None

    from config import get_settings
    from jose import jwt

    settings = get_settings()
    token = jwt.encode(
        {"sub": str(user.id)},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    from main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/subscriptions/portal-session",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "Cliente de Stripe no encontrado" in response.json()["detail"]


@pytest.mark.asyncio
async def test_stripe_webhook_subscription_created(db: AsyncSession):
    """Test Stripe webhook for subscription.created event."""
    from config import get_settings

    settings = get_settings()

    # Create a tenant with stripe_customer_id
    tenant = Tenant(
        id=uuid4(),
        name="Test Operator",
        slug="test-operator",
        is_active=True,
        plan_tier=PlanTier.starter,
        stripe_customer_id="cus_test_123",
    )
    db.add(tenant)
    await db.commit()

    webhook_payload = {
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": "sub_test_123",
                "customer": "cus_test_123",
                "status": "active",
                "items": {
                    "data": [
                        {
                            "price": {
                                "lookup_key": "pro_plan",
                            }
                        }
                    ]
                },
            }
        },
    }

    with patch("stripe.Webhook.construct_event") as mock_construct:
        mock_construct.return_value = webhook_payload

        from main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/webhooks/stripe",
                json=webhook_payload,
                headers={"Stripe-Signature": "test_signature"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

            # Verify tenant was updated
            updated_tenant = await db.get(Tenant, tenant.id)
            assert updated_tenant.plan_tier == PlanTier.pro
            assert updated_tenant.subscription_status == SubscriptionStatus.active


@pytest.mark.asyncio
async def test_stripe_webhook_checkout_completed(db: AsyncSession):
    """Test Stripe webhook for checkout.session.completed event."""
    # Create a tenant without stripe_customer_id
    tenant = Tenant(
        id=uuid4(),
        name="Test Operator",
        slug="test-operator",
        is_active=True,
        plan_tier=PlanTier.starter,
        stripe_customer_id=None,
    )
    db.add(tenant)
    await db.commit()

    webhook_payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "customer": "cus_new_123",
                "client_reference_id": str(tenant.id),
            }
        },
    }

    with patch("stripe.Webhook.construct_event") as mock_construct:
        mock_construct.return_value = webhook_payload

        from main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/webhooks/stripe",
                json=webhook_payload,
                headers={"Stripe-Signature": "test_signature"},
            )

            assert response.status_code == 200

            # Verify tenant was updated with stripe_customer_id
            updated_tenant = await db.get(Tenant, tenant.id)
            assert updated_tenant.stripe_customer_id == "cus_new_123"


@pytest.mark.asyncio
async def test_stripe_webhook_invalid_signature():
    """Test Stripe webhook with invalid signature."""
    from config import get_settings

    settings = get_settings()

    webhook_payload = {
        "type": "customer.subscription.created",
        "data": {"object": {}},
    }

    with patch("stripe.Webhook.construct_event") as mock_construct:
        mock_construct.side_effect = Exception("Invalid signature")

        from main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/webhooks/stripe",
                json=webhook_payload,
                headers={"Stripe-Signature": "invalid_signature"},
            )

            assert response.status_code == 400
