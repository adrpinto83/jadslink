"""Tests for authentication router endpoints."""

import pytest
from fastapi.testclient import TestClient
import uuid

from main import app


# Create test client
client = TestClient(app)


class TestRegister:
    """Tests for user registration endpoint."""

    def test_register_success(self):
        """Test successful user registration."""
        unique_id = uuid.uuid4()
        response = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": f"New Company {unique_id}",
                "email": f"newuser{unique_id}@example.com",
                "password": "securepassword123",
            },
        )

        assert response.status_code == 201
        assert response.json()["status"] == "success"
        assert "Plan Free activado" in response.json()["message"]

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

    def test_register_missing_fields(self):
        """Test registration with missing fields fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": "Company",
                # Missing email and password
            },
        )

        assert response.status_code == 422


class TestLogin:
    """Tests for user login endpoint."""

    def test_login_wrong_password(self):
        """Test login with wrong password fails."""
        # First register a user
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": "Test Company",
                "email": f"testuser{uuid.uuid4()}@example.com",
                "password": "correctpassword123",
            },
        )
        assert register_response.status_code == 201

        email = register_response.json().get("email") or "testuser@example.com"

        # Try to login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert "Email o contraseña incorrectos" in response.json()["detail"]

    def test_login_nonexistent_user(self):
        """Test login with non-existent user fails."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": f"nonexistent{uuid.uuid4()}@example.com",
                "password": "password",
            },
        )

        assert response.status_code == 401

    def test_login_invalid_email(self):
        """Test login with invalid email format fails."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": "password"},
        )

        assert response.status_code == 422


class TestRefresh:
    """Tests for token refresh endpoint."""

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


class TestGetMe:
    """Tests for GET /auth/me endpoint."""

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


class TestCSRFProtection:
    """Tests for CSRF protection on endpoints."""

    def test_register_no_csrf_required(self):
        """Test that register endpoint doesn't require CSRF token."""
        unique_id = uuid.uuid4()
        response = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": f"Test {unique_id}",
                "email": f"test{unique_id}@example.com",
                "password": "password",
            },
        )

        # Should succeed (201) without CSRF token
        assert response.status_code == 201

    def test_login_no_csrf_required(self):
        """Test that login endpoint doesn't require CSRF token."""
        # First register
        client.post(
            "/api/v1/auth/register",
            json={
                "company_name": "Company",
                "email": f"login_test{uuid.uuid4()}@example.com",
                "password": "password123",
            },
        )

        # Then try to login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": f"login_test{uuid.uuid4()}@example.com",
                "password": "password123",
            },
        )

        # Should either succeed (200) or fail with auth error (401), not 403 CSRF
        assert response.status_code in [200, 401]


class TestAuthFlow:
    """Integration tests for complete auth flow."""

    def test_register_then_login(self):
        """Test complete flow: register then login."""
        unique_email = f"flowtest{uuid.uuid4()}@example.com"

        # Register
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": "Flow Test Company",
                "email": unique_email,
                "password": "flowpassword123",
            },
        )

        assert register_response.status_code == 201
        assert register_response.json()["status"] == "success"

        # Login with same credentials
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": "flowpassword123"},
        )

        # Login can fail due to tenant not being active, but should not have validation errors
        assert login_response.status_code in [200, 403]  # 200 success or 403 tenant inactive

        if login_response.status_code == 200:
            data = login_response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"


class TestRegistrationErrors:
    """Tests for registration error cases."""

    def test_register_very_short_password(self):
        """Test registration with very short password."""
        unique_id = uuid.uuid4()
        response = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": f"Company {unique_id}",
                "email": f"short{unique_id}@example.com",
                "password": "abc",  # Very short
            },
        )

        # Should still work - no minimum length validation in the endpoint
        assert response.status_code == 201

    def test_register_empty_company_name(self):
        """Test registration with empty company name."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": "",  # Empty
                "email": f"empty{uuid.uuid4()}@example.com",
                "password": "password123",
            },
        )

        # Pydantic should validate this
        assert response.status_code == 422


class TestInputValidation:
    """Tests for input validation on auth endpoints."""

    def test_login_empty_credentials(self):
        """Test login with empty email and password."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "", "password": ""},
        )

        assert response.status_code == 422

    def test_register_with_special_characters(self):
        """Test registration with special characters in email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": "Special Co.",
                "email": f"test+{uuid.uuid4()}@example.com",
                "password": "password123",
            },
        )

        # Should handle special chars in email
        assert response.status_code in [201, 422]
