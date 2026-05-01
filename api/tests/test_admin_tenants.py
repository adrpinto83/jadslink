"""
Tests para endpoints de administración de tenants (superadmin).
"""
from fastapi.testclient import TestClient
import uuid

from main import app

client = TestClient(app)


def get_csrf_token(auth_token: str, endpoint: str = "/api/v1/admin/overview") -> str:
    """Get CSRF token from a GET request."""
    response = client.get(
        endpoint,
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    return response.headers.get("X-CSRF-Token", "")


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


class TestAdminGlobalOverview:
    """Test endpoint /admin/overview."""

    def test_global_overview_success(self):
        """Test GET /admin/overview returns global statistics."""
        # Get superadmin token (from seed data)
        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@jads.com",
                "password": "admin123456",
            },
        )
        assert login.status_code == 200
        superadmin_token = login.json()["access_token"]

        response = client.get(
            "/api/v1/admin/overview",
            headers={"Authorization": f"Bearer {superadmin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verificar que contiene los campos esperados
        assert "total_tenants" in data
        assert "active_tenants" in data
        assert "total_nodes" in data
        assert "online_nodes" in data
        assert "total_tickets" in data
        assert "active_sessions" in data
        assert "tenants_by_plan" in data
        assert "nodes_by_status" in data

        # Verificar tipos
        assert isinstance(data["total_tenants"], int)
        assert isinstance(data["total_nodes"], int)
        assert isinstance(data["tenants_by_plan"], list)

    def test_global_overview_forbidden_for_operator(self):
        """Test that operator cannot access /admin/overview."""
        unique_id = uuid.uuid4()
        operator_token = register_and_login(
            f"op{unique_id}@test.com",
            f"Operator Company {unique_id}",
        )

        response = client.get(
            "/api/v1/admin/overview",
            headers={"Authorization": f"Bearer {operator_token}"},
        )

        assert response.status_code == 403


class TestAdminListTenants:
    """Test endpoint GET /admin/tenants."""

    def test_list_tenants_detailed_success(self):
        """Test GET /admin/tenants returns detailed tenant list."""
        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@jads.com",
                "password": "admin123456",
            },
        )
        assert login.status_code == 200
        superadmin_token = login.json()["access_token"]

        response = client.get(
            "/api/v1/admin/tenants",
            headers={"Authorization": f"Bearer {superadmin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Should have at least the demo tenant from seed
        if len(data) > 0:
            tenant = data[0]
            assert "id" in tenant
            assert "name" in tenant
            assert "plan_tier" in tenant
            assert "is_active" in tenant
            assert "nodes_count" in tenant
            assert "tickets_count" in tenant
            assert "sessions_count" in tenant


class TestAdminTenantStats:
    """Test endpoint GET /admin/tenants/{id}/stats."""

    def test_tenant_stats_success(self):
        """Test GET /admin/tenants/{id}/stats returns tenant statistics."""
        # Get superadmin token
        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@jads.com",
                "password": "admin123456",
            },
        )
        assert login.status_code == 200
        superadmin_token = login.json()["access_token"]

        # Get list of tenants
        tenants_response = client.get(
            "/api/v1/admin/tenants",
            headers={"Authorization": f"Bearer {superadmin_token}"},
        )
        assert tenants_response.status_code == 200
        tenants = tenants_response.json()

        if len(tenants) > 0:
            tenant_id = tenants[0]["id"]

            # Get stats for this tenant
            response = client.get(
                f"/api/v1/admin/tenants/{tenant_id}/stats",
                headers={"Authorization": f"Bearer {superadmin_token}"},
            )

            assert response.status_code == 200
            data = response.json()

            # Verificar estructura de respuesta
            assert data["tenant_id"] == tenant_id
            assert "tenant_name" in data
            assert "nodes_total" in data
            assert "nodes_online" in data
            assert "tickets_total" in data
            assert "tickets_active" in data
            assert "sessions_active" in data
            assert "revenue_estimate" in data

    def test_tenant_stats_not_found(self):
        """Test GET /admin/tenants/{id}/stats returns 404 for non-existent tenant."""
        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@jads.com",
                "password": "admin123456",
            },
        )
        assert login.status_code == 200
        superadmin_token = login.json()["access_token"]

        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/v1/admin/tenants/{fake_id}/stats",
            headers={"Authorization": f"Bearer {superadmin_token}"},
        )

        assert response.status_code == 404


class TestAdminTenantNodes:
    """Test endpoint GET /admin/tenants/{id}/nodes."""

    def test_tenant_nodes_success(self):
        """Test GET /admin/tenants/{id}/nodes returns list of nodes."""
        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@jads.com",
                "password": "admin123456",
            },
        )
        assert login.status_code == 200
        superadmin_token = login.json()["access_token"]

        # Get list of tenants
        tenants_response = client.get(
            "/api/v1/admin/tenants",
            headers={"Authorization": f"Bearer {superadmin_token}"},
        )
        assert tenants_response.status_code == 200
        tenants = tenants_response.json()

        if len(tenants) > 0:
            tenant_id = tenants[0]["id"]

            response = client.get(
                f"/api/v1/admin/tenants/{tenant_id}/nodes",
                headers={"Authorization": f"Bearer {superadmin_token}"},
            )

            assert response.status_code == 200
            data = response.json()

            assert isinstance(data, list)
            # If there are nodes, verify structure
            if len(data) > 0:
                node = data[0]
                assert "id" in node
                assert "name" in node
                assert "serial" in node
                assert "status" in node


class TestAdminTenantTickets:
    """Test endpoint GET /admin/tenants/{id}/tickets."""

    def test_tenant_tickets_pagination(self):
        """Test GET /admin/tenants/{id}/tickets returns paginated tickets."""
        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@jads.com",
                "password": "admin123456",
            },
        )
        assert login.status_code == 200
        superadmin_token = login.json()["access_token"]

        # Get list of tenants
        tenants_response = client.get(
            "/api/v1/admin/tenants",
            headers={"Authorization": f"Bearer {superadmin_token}"},
        )
        assert tenants_response.status_code == 200
        tenants = tenants_response.json()

        if len(tenants) > 0:
            tenant_id = tenants[0]["id"]

            response = client.get(
                f"/api/v1/admin/tenants/{tenant_id}/tickets?skip=0&limit=100",
                headers={"Authorization": f"Bearer {superadmin_token}"},
            )

            assert response.status_code == 200
            data = response.json()

            # Verificar estructura de respuesta paginada
            assert "tickets" in data
            assert "total" in data
            assert "page" in data
            assert "pages" in data
            assert isinstance(data["tickets"], list)


class TestAdminTenantSessions:
    """Test endpoint GET /admin/tenants/{id}/sessions."""

    def test_tenant_sessions_success(self):
        """Test GET /admin/tenants/{id}/sessions returns list of sessions."""
        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@jads.com",
                "password": "admin123456",
            },
        )
        assert login.status_code == 200
        superadmin_token = login.json()["access_token"]

        # Get list of tenants
        tenants_response = client.get(
            "/api/v1/admin/tenants",
            headers={"Authorization": f"Bearer {superadmin_token}"},
        )
        assert tenants_response.status_code == 200
        tenants = tenants_response.json()

        if len(tenants) > 0:
            tenant_id = tenants[0]["id"]

            response = client.get(
                f"/api/v1/admin/tenants/{tenant_id}/sessions?active_only=false",
                headers={"Authorization": f"Bearer {superadmin_token}"},
            )

            assert response.status_code == 200
            data = response.json()

            assert isinstance(data, list)
            # If there are sessions, verify structure
            if len(data) > 0:
                session = data[0]
                assert "id" in session
                assert "ticket_id" in session
                assert "device_mac" in session
                assert "is_active" in session


class TestAdminTenantActions:
    """Test admin action endpoints."""

    def test_suspend_tenant_success(self):
        """Test PATCH /admin/tenants/{id}/suspend suspends a tenant."""
        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@jads.com",
                "password": "admin123456",
            },
        )
        assert login.status_code == 200
        superadmin_token = login.json()["access_token"]

        # Create a new tenant to suspend
        unique_id = uuid.uuid4()
        register = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": f"Company to Suspend {unique_id}",
                "email": f"suspend{unique_id}@test.com",
                "password": "testpass123",
            },
        )
        assert register.status_code == 201

        # Get new tenant ID
        tenants_response = client.get(
            "/api/v1/admin/tenants",
            headers={"Authorization": f"Bearer {superadmin_token}"},
        )
        assert tenants_response.status_code == 200
        tenants = tenants_response.json()
        new_tenant = next(
            (t for t in tenants if t["name"] == f"Company to Suspend {unique_id}"), None
        )

        if new_tenant:
            response = client.patch(
                f"/api/v1/admin/tenants/{new_tenant['id']}/suspend",
                headers={"Authorization": f"Bearer {superadmin_token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_active"] is False

    def test_activate_tenant_success(self):
        """Test PATCH /admin/tenants/{id}/activate reactivates a suspended tenant."""
        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@jads.com",
                "password": "admin123456",
            },
        )
        assert login.status_code == 200
        superadmin_token = login.json()["access_token"]

        # Create a new tenant
        unique_id = uuid.uuid4()
        register = client.post(
            "/api/v1/auth/register",
            json={
                "company_name": f"Company to Activate {unique_id}",
                "email": f"activate{unique_id}@test.com",
                "password": "testpass123",
            },
        )
        assert register.status_code == 201

        # Get new tenant ID
        tenants_response = client.get(
            "/api/v1/admin/tenants",
            headers={"Authorization": f"Bearer {superadmin_token}"},
        )
        assert tenants_response.status_code == 200
        tenants = tenants_response.json()
        new_tenant = next(
            (t for t in tenants if t["name"] == f"Company to Activate {unique_id}"), None
        )

        if new_tenant:
            # First suspend it
            suspend_response = client.patch(
                f"/api/v1/admin/tenants/{new_tenant['id']}/suspend",
                headers={"Authorization": f"Bearer {superadmin_token}"},
            )
            assert suspend_response.status_code == 200

            # Then activate it
            activate_response = client.patch(
                f"/api/v1/admin/tenants/{new_tenant['id']}/activate",
                headers={"Authorization": f"Bearer {superadmin_token}"},
            )

            assert activate_response.status_code == 200
            data = activate_response.json()
            assert data["is_active"] is True


class TestAdminPermissions:
    """Test admin endpoint permissions."""

    def test_admin_endpoints_require_superadmin(self):
        """Test that admin endpoints require superadmin role."""
        unique_id = uuid.uuid4()
        operator_token = register_and_login(
            f"op_perm{unique_id}@test.com",
            f"Operator Permission Test {unique_id}",
        )

        endpoints = [
            "/api/v1/admin/overview",
            "/api/v1/admin/tenants",
        ]

        for endpoint in endpoints:
            response = client.get(
                endpoint,
                headers={"Authorization": f"Bearer {operator_token}"},
            )
            assert response.status_code == 403, f"Endpoint {endpoint} should return 403 for operator"
