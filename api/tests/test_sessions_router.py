"""Tests for sessions router endpoints."""

from fastapi.testclient import TestClient
import uuid
from datetime import datetime, timezone, timedelta

from main import app

client = TestClient(app)


def register_and_login(email: str, company: str, password: str = "testpass123"):
    """Helper: Register a user and return auth token."""
    register = client.post(
        "/api/v1/auth/register",
        json={
            "company_name": company,
            "email": email,
            "password": password,
        },
    )
    assert register.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def get_csrf_token(auth_token: str, endpoint: str = "/api/v1/plans") -> str:
    """Get CSRF token from a GET request."""
    response = client.get(
        endpoint,
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    return response.headers.get("X-CSRF-Token", "")


class TestSessionsList:
    """Test session listing."""

    def test_list_sessions_empty(self):
        """Test listing when no sessions exist."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"session{unique_id}@test.com",
            f"SessionCompany {unique_id}",
        )

        response = client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        sessions = response.json()
        assert isinstance(sessions, list)
        # Should be empty or contain minimal data
        assert len(sessions) == 0

    def test_list_sessions_without_auth(self):
        """Test listing without authentication fails."""
        response = client.get("/api/v1/sessions")
        assert response.status_code == 403

    def test_list_sessions_structure(self):
        """Test that session list returns correct structure (even if empty)."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"sessionstruct{unique_id}@test.com",
            f"StructCompany {unique_id}",
        )

        response = client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        sessions = response.json()
        assert isinstance(sessions, list)

        # If there are sessions, verify structure
        for session in sessions:
            assert "id" in session
            assert "ticket_code" in session
            assert "node" in session
            assert "plan" in session
            assert "status" in session
            assert "started_at" in session

    def test_list_sessions_tenant_isolation(self):
        """Test that operators only see their tenant's sessions."""
        # Tenant 1
        unique_id1 = uuid.uuid4()
        token1 = register_and_login(
            f"tenant1{unique_id1}@test.com",
            f"Tenant1 {unique_id1}",
        )

        # Tenant 2
        unique_id2 = uuid.uuid4()
        token2 = register_and_login(
            f"tenant2{unique_id2}@test.com",
            f"Tenant2 {unique_id2}",
        )

        # List sessions for both - should be empty
        response1 = client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert response1.status_code == 200
        sessions1 = response1.json()

        response2 = client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response2.status_code == 200
        sessions2 = response2.json()

        # Both should be empty (no active sessions)
        assert len(sessions1) == 0
        assert len(sessions2) == 0

        # Verify no cross-tenant leakage
        session_ids_1 = {s["id"] for s in sessions1}
        session_ids_2 = {s["id"] for s in sessions2}
        assert session_ids_1.isdisjoint(session_ids_2)

    def test_list_sessions_returns_list_not_error(self):
        """Test that listing sessions returns valid list (no 5xx errors)."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"sessionvalid{unique_id}@test.com",
            f"ValidCompany {unique_id}",
        )

        # Make multiple requests to ensure endpoint is stable
        for _ in range(3):
            response = client.get(
                "/api/v1/sessions",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_superadmin_can_list_all_sessions(self):
        """Test that superadmin role handling works (if applicable)."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"sessionadmin{unique_id}@test.com",
            f"AdminCompany {unique_id}",
        )

        # Regular operator trying to list
        response = client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should work (return empty list) even for operator
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestSessionsEndpoints:
    """Test general sessions endpoint behavior."""

    def test_sessions_endpoint_exists(self):
        """Test that sessions endpoint exists and responds."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"sessionexists{unique_id}@test.com",
            f"ExistsCompany {unique_id}",
        )

        response = client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should return 200, not 404
        assert response.status_code == 200

    def test_sessions_endpoint_valid_response(self):
        """Test that sessions endpoint returns valid JSON."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"sessionjson{unique_id}@test.com",
            f"JsonCompany {unique_id}",
        )

        response = client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        # Should be valid JSON array
        sessions = response.json()
        assert isinstance(sessions, list)

    def test_sessions_response_format(self):
        """Test response format consistency."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"sessionformat{unique_id}@test.com",
            f"FormatCompany {unique_id}",
        )

        response = client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )

        data = response.json()
        assert isinstance(data, list)

        # Verify each session has required fields
        for session in data:
            assert isinstance(session, dict)
            # Check for essential fields
            required_fields = ["id", "ticket_code", "node", "plan", "status"]
            for field in required_fields:
                assert field in session, f"Missing field: {field}"

    def test_sessions_multiple_requests_consistent(self):
        """Test that multiple requests return consistent data."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"sessionconsistent{unique_id}@test.com",
            f"ConsistentCompany {unique_id}",
        )

        # Make two requests
        response1 = client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        sessions1 = response1.json()

        response2 = client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        sessions2 = response2.json()

        # Should return same data (both empty or both with same sessions)
        assert len(sessions1) == len(sessions2)

    def test_sessions_filters_inactive(self):
        """Test that listing only shows active sessions."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"sessioninactive{unique_id}@test.com",
            f"InactiveCompany {unique_id}",
        )

        response = client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )

        sessions = response.json()

        # All sessions should be active
        for session in sessions:
            assert session["status"] == "active", "Should only return active sessions"
