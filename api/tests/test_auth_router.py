"""Tests for authentication router endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from datetime import datetime, timezone

from main import app
from models.user import User
from models.tenant import Tenant
from database import get_db
from routers.auth import hash_password


# Create test client
client = TestClient(app)


@pytest.fixture
async def test_tenant(db_session: AsyncSession):
    """Create a test tenant."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Test Company",
        slug="test-company",
        is_active=True,
        plan_tier="free",
        subscription_status="trialing",
        free_tickets_limit=50,
        free_tickets_used=0,
    )
    db_session.add(tenant)
    await db_session.commit()
    return tenant


@pytest.fixture
async def test_user(db_session: AsyncSession, test_tenant):
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
        role="operator",
        tenant_id=test_tenant.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


class TestRegister:
    """Tests for user registration endpoint."""

    def test_register_success(self):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": "New Company",
                "email": f"newuser{uuid.uuid4()}@example.com",
                "password": "securepassword123",
            },
        )

        assert response.status_code == 201
        assert response.json()["status"] == "success"
        assert "Plan Free activado" in response.json()["message"]

    def test_register_duplicate_email(self, test_user):
        """Test registration with duplicate email fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": "Another Company",
                "email": test_user.email,  # Duplicate
                "password": "securepassword123",
            },
        )

        assert response.status_code == 400
        assert "ya existe" in response.json()["detail"]

    def test_register_invalid_email(self):
        """Test registration with invalid email fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": "Company",
                "email": "not-an-email",
                "password": "securepassword123",
            },
        )

        assert response.status_code == 422

    def test_register_rate_limiting(self):
        """Test rate limiting on register endpoint."""
        email_base = f"test{uuid.uuid4()}@example.com"

        # Make 5 requests (should all succeed)
        for i in range(5):
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "company_name": f"Company {i}",
                    "email": f"{i}{email_base}",
                    "password": "securepassword123",
                },
            )
            assert response.status_code == 201

        # 6th request within same window should be rate limited
        response = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": "Company 6",
                "email": f"6{email_base}",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 429


class TestLogin:
    """Tests for user login endpoint."""

    def test_login_success(self, test_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "refresh_token" not in data  # Refresh token in cookie only

    def test_login_wrong_password(self, test_user):
        """Test login with wrong password fails."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "Email o contraseña incorrectos" in response.json()["detail"]

    def test_login_nonexistent_user(self):
        """Test login with non-existent user fails."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "password"},
        )

        assert response.status_code == 401

    def test_login_inactive_user(self, db_session, test_tenant):
        """Test login with inactive user fails."""
        user = User(
            id=uuid.uuid4(),
            email="inactive@example.com",
            password_hash=hash_password("password"),
            role="operator",
            tenant_id=test_tenant.id,
            is_active=False,  # Inactive
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "password"},
        )

        assert response.status_code == 401
        assert "Usuario inactivo" in response.json()["detail"]

    def test_login_inactive_tenant(self, db_session, test_user):
        """Test login with inactive tenant fails."""
        # Deactivate tenant
        tenant = db_session.query(Tenant).filter_by(id=test_user.tenant_id).first()
        tenant.is_active = False
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )

        assert response.status_code == 403
        assert "no está activa" in response.json()["detail"]

    def test_login_sets_refresh_token_cookie(self, test_user):
        """Test that login sets refresh_token in HttpOnly cookie."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )

        assert response.status_code == 200

        # Check for refresh_token cookie
        cookies = response.cookies
        assert "refresh_token" in cookies

    def test_login_rate_limiting(self, test_user):
        """Test rate limiting on login endpoint."""
        # Make 5 failed attempts
        for _ in range(5):
            client.post(
                "/api/v1/auth/login",
                json={"email": test_user.email, "password": "wrongpassword"},
            )

        # Next attempt should be rate limited
        response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )

        assert response.status_code == 429


class TestRefresh:
    """Tests for token refresh endpoint."""

    def test_refresh_with_valid_cookie(self, test_user):
        """Test refreshing token with valid refresh_token cookie."""
        # First login to get refresh token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )
        assert login_response.status_code == 200

        # Extract cookie from login response
        refresh_token_cookie = login_response.cookies.get("refresh_token")
        assert refresh_token_cookie is not None

        # Use cookie for refresh
        response = client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": refresh_token_cookie},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_without_cookie(self):
        """Test refresh without refresh_token cookie fails."""
        response = client.post("/api/v1/auth/refresh")

        assert response.status_code == 401
        assert "no encontrado" in response.json()["detail"]

    def test_refresh_with_invalid_token(self):
        """Test refresh with invalid token fails."""
        response = client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 401
        assert "inválido" in response.json()["detail"]

    def test_refresh_updates_cookie(self, test_user):
        """Test that refresh endpoint updates refresh_token cookie."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )
        refresh_token_1 = login_response.cookies.get("refresh_token")

        # Refresh
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": refresh_token_1},
        )

        refresh_token_2 = refresh_response.cookies.get("refresh_token")

        # New refresh token should be different (new one generated)
        assert refresh_token_2 is not None
        assert refresh_token_1 != refresh_token_2


class TestGetMe:
    """Tests for GET /auth/me endpoint."""

    def test_get_me_with_valid_token(self, test_user):
        """Test getting current user info with valid token."""
        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )
        access_token = login_response.json()["access_token"]

        # Get user info
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["role"] == "operator"
        assert str(data["id"]) == str(test_user.id)

    def test_get_me_without_token(self):
        """Test getting user info without token fails."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 403

    def test_get_me_with_invalid_token(self):
        """Test getting user info with invalid token fails."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 403

    def test_get_me_with_expired_token(self, test_user, monkeypatch):
        """Test getting user info with expired token."""
        # Note: Testing true token expiration requires mocking time
        # For now, this is a placeholder for the pattern
        pass


class TestCSRFProtection:
    """Tests for CSRF protection on endpoints."""

    def test_login_no_csrf_required(self, test_user):
        """Test that login endpoint doesn't require CSRF token."""
        # Login endpoint should not require CSRF token
        response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )

        assert response.status_code == 200

    def test_register_no_csrf_required(self):
        """Test that register endpoint doesn't require CSRF token."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": "Test",
                "email": f"test{uuid.uuid4()}@example.com",
                "password": "password",
            },
        )

        assert response.status_code == 201
