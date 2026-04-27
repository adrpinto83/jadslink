"""Tests for tickets router endpoints."""

from fastapi.testclient import TestClient
import uuid

from main import app

client = TestClient(app)


def get_csrf_token(auth_token: str, endpoint: str = "/api/v1/plans") -> str:
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


class TestTicketsGenerate:
    """Test ticket generation."""

    def test_generate_tickets_success(self):
        """Test generating tickets successfully."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"tickets{unique_id}@test.com",
            f"TicketsCompany {unique_id}",
        )
        csrf = get_csrf_token(token)

        # Create a node
        node_response = client.post(
            "/api/v1/nodes",
            json={
                "name": "Test Node",
                "serial": f"SN-{unique_id}",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )
        assert node_response.status_code == 201
        node_id = node_response.json()["id"]

        # Create a plan
        csrf = get_csrf_token(token)
        plan_response = client.post(
            "/api/v1/plans",
            json={
                "name": "30 Minutos",
                "duration_minutes": 30,
                "price_usd": 2.50,
                "is_active": True,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )
        assert plan_response.status_code == 201
        plan_id = plan_response.json()["id"]

        # Generate tickets
        csrf = get_csrf_token(token, "/api/v1/tickets")
        response = client.post(
            "/api/v1/tickets/generate",
            json={
                "node_id": node_id,
                "plan_id": plan_id,
                "quantity": 5,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )

        assert response.status_code == 201
        tickets = response.json()
        assert len(tickets) == 5
        for ticket in tickets:
            assert ticket["code"]
            assert ticket["qr_data"]
            # node_id and plan_id may not be in response depending on serialization
            if "node_id" in ticket:
                assert ticket["node_id"] == node_id
            if "plan_id" in ticket:
                assert ticket["plan_id"] == plan_id

    def test_generate_tickets_invalid_node(self):
        """Test generating tickets with invalid node."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"tickets2{unique_id}@test.com",
            f"TicketsCompany2 {unique_id}",
        )

        # Create a plan
        csrf = get_csrf_token(token)
        plan_response = client.post(
            "/api/v1/plans",
            json={
                "name": "Plan",
                "duration_minutes": 30,
                "price_usd": 2.50,
                "is_active": True,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )
        plan_id = plan_response.json()["id"]

        # Try to generate tickets with invalid node
        csrf = get_csrf_token(token, "/api/v1/tickets")
        response = client.post(
            "/api/v1/tickets/generate",
            json={
                "node_id": str(uuid.uuid4()),
                "plan_id": plan_id,
                "quantity": 5,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )

        assert response.status_code == 404

    def test_generate_tickets_invalid_plan(self):
        """Test generating tickets with invalid plan."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"tickets3{unique_id}@test.com",
            f"TicketsCompany3 {unique_id}",
        )
        csrf = get_csrf_token(token)

        # Create a node
        node_response = client.post(
            "/api/v1/nodes",
            json={
                "name": "Test Node",
                "serial": f"SN-{unique_id}",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )
        node_id = node_response.json()["id"]

        # Try to generate tickets with invalid plan
        csrf = get_csrf_token(token, "/api/v1/tickets")
        response = client.post(
            "/api/v1/tickets/generate",
            json={
                "node_id": node_id,
                "plan_id": str(uuid.uuid4()),
                "quantity": 5,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )

        assert response.status_code == 404

    def test_generate_zero_tickets(self):
        """Test generating 0 tickets."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"tickets4{unique_id}@test.com",
            f"TicketsCompany4 {unique_id}",
        )
        csrf = get_csrf_token(token)

        # Create node and plan
        node_response = client.post(
            "/api/v1/nodes",
            json={
                "name": "Test Node",
                "serial": f"SN-{unique_id}",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )
        node_id = node_response.json()["id"]

        csrf = get_csrf_token(token)
        plan_response = client.post(
            "/api/v1/plans",
            json={
                "name": "Plan",
                "duration_minutes": 30,
                "price_usd": 2.50,
                "is_active": True,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )
        plan_id = plan_response.json()["id"]

        # Try to generate 0 tickets
        csrf = get_csrf_token(token, "/api/v1/tickets")
        response = client.post(
            "/api/v1/tickets/generate",
            json={
                "node_id": node_id,
                "plan_id": plan_id,
                "quantity": 0,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )

        # Should be validation error or empty list
        assert response.status_code in [422, 201]


class TestTicketsList:
    """Test ticket listing."""

    def test_list_tickets_empty(self):
        """Test listing when no tickets exist."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"ticketslist{unique_id}@test.com",
            f"ListCompany {unique_id}",
        )

        response = client.get(
            "/api/v1/tickets",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        tickets = response.json()
        assert isinstance(tickets, list)

    def test_list_tickets_with_data(self):
        """Test listing with generated tickets."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"ticketslist2{unique_id}@test.com",
            f"ListCompany2 {unique_id}",
        )
        csrf = get_csrf_token(token)

        # Create node
        node_response = client.post(
            "/api/v1/nodes",
            json={
                "name": "Test Node",
                "serial": f"SN-{unique_id}",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )
        node_id = node_response.json()["id"]

        # Create plan
        csrf = get_csrf_token(token)
        plan_response = client.post(
            "/api/v1/plans",
            json={
                "name": "Plan",
                "duration_minutes": 30,
                "price_usd": 2.50,
                "is_active": True,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )
        plan_id = plan_response.json()["id"]

        # Generate tickets
        csrf = get_csrf_token(token, "/api/v1/tickets")
        client.post(
            "/api/v1/tickets/generate",
            json={
                "node_id": node_id,
                "plan_id": plan_id,
                "quantity": 3,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )

        # List and verify
        response = client.get(
            "/api/v1/tickets",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        tickets = response.json()
        assert len(tickets) >= 3

    def test_list_tickets_without_auth(self):
        """Test listing without authentication fails."""
        response = client.get("/api/v1/tickets")
        assert response.status_code == 403


class TestTicketsTenantIsolation:
    """Test multi-tenant isolation for tickets."""

    def test_cannot_see_other_tenant_tickets(self):
        """Test that users cannot see other tenant's tickets."""
        # User 1
        unique_id1 = uuid.uuid4()
        token1 = register_and_login(
            f"tenant1{unique_id1}@test.com",
            f"Tenant1 {unique_id1}",
        )

        # User 2
        unique_id2 = uuid.uuid4()
        token2 = register_and_login(
            f"tenant2{unique_id2}@test.com",
            f"Tenant2 {unique_id2}",
        )

        # User 1 creates node and plan
        csrf1 = get_csrf_token(token1)
        node_response = client.post(
            "/api/v1/nodes",
            json={
                "name": "Node 1",
                "serial": f"SN-{unique_id1}",
            },
            headers={
                "Authorization": f"Bearer {token1}",
                "X-CSRF-Token": csrf1,
            },
        )
        node_id = node_response.json()["id"]

        csrf1 = get_csrf_token(token1)
        plan_response = client.post(
            "/api/v1/plans",
            json={
                "name": "Plan 1",
                "duration_minutes": 30,
                "price_usd": 2.50,
                "is_active": True,
            },
            headers={
                "Authorization": f"Bearer {token1}",
                "X-CSRF-Token": csrf1,
            },
        )
        plan_id = plan_response.json()["id"]

        # User 1 generates tickets
        csrf1 = get_csrf_token(token1, "/api/v1/tickets")
        client.post(
            "/api/v1/tickets/generate",
            json={
                "node_id": node_id,
                "plan_id": plan_id,
                "quantity": 3,
            },
            headers={
                "Authorization": f"Bearer {token1}",
                "X-CSRF-Token": csrf1,
            },
        )

        # User 2 lists tickets - should not see User1's tickets
        response = client.get(
            "/api/v1/tickets",
            headers={"Authorization": f"Bearer {token2}"},
        )

        tickets2 = response.json()
        assert len(tickets2) == 0  # Should be empty for user2
