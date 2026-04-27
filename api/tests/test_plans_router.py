"""Tests for plans router endpoints."""

from fastapi.testclient import TestClient
import uuid

from main import app

client = TestClient(app)


def get_csrf_token(auth_token: str) -> str:
    """Get CSRF token from a GET request."""
    response = client.get(
        "/api/v1/plans",
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


class TestPlansCreate:
    """Test plan creation."""

    def test_create_plan_success(self):
        """Test creating a plan successfully."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"plan{unique_id}@test.com",
            f"Company {unique_id}",
        )
        csrf = get_csrf_token(token)

        response = client.post(
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

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "30 Minutos"
        assert data["duration_minutes"] == 30
        assert float(data["price_usd"]) == 2.50
        assert data["is_active"] is True

    def test_create_plan_without_auth(self):
        """Test creating a plan without authentication fails."""
        response = client.post(
            "/api/v1/plans",
            json={
                "name": "Plan",
                "duration_minutes": 30,
                "price_usd": 2.50,
                "is_active": True,
            },
        )
        assert response.status_code == 403  # CSRF + no auth

    def test_create_plan_missing_field(self):
        """Test creating plan with missing required field."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"plan2{unique_id}@test.com",
            f"Company2 {unique_id}",
        )
        csrf = get_csrf_token(token)

        response = client.post(
            "/api/v1/plans",
            json={
                "duration_minutes": 30,  # Missing name
                "price_usd": 2.50,
                "is_active": True,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )

        assert response.status_code == 422


class TestPlansList:
    """Test plan listing."""

    def test_list_plans_empty(self):
        """Test listing plans when none exist."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"planlist{unique_id}@test.com",
            f"ListCompany {unique_id}",
        )

        response = client.get(
            "/api/v1/plans",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_plans_with_data(self):
        """Test listing plans with created plans."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"planlist2{unique_id}@test.com",
            f"ListCompany2 {unique_id}",
        )

        # Create 2 plans
        for i in range(2):
            csrf = get_csrf_token(token)
            client.post(
                "/api/v1/plans",
                json={
                    "name": f"Plan {i}",
                    "duration_minutes": 30 * (i + 1),
                    "price_usd": 2.50,
                    "is_active": True,
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": csrf,
                },
            )

        # List and verify
        response = client.get(
            "/api/v1/plans",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        plans = response.json()
        assert len(plans) >= 2

    def test_list_plans_without_auth(self):
        """Test listing plans without auth fails."""
        response = client.get("/api/v1/plans")
        assert response.status_code == 403


class TestPlansUpdate:
    """Test plan updates."""

    def test_update_plan_success(self):
        """Test updating a plan."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"planupdate{unique_id}@test.com",
            f"UpdateCompany {unique_id}",
        )

        # Create plan
        csrf = get_csrf_token(token)
        create = client.post(
            "/api/v1/plans",
            json={
                "name": "Original",
                "duration_minutes": 30,
                "price_usd": 2.50,
                "is_active": True,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )
        plan_id = create.json()["id"]

        # Update plan
        csrf = get_csrf_token(token)
        response = client.patch(
            f"/api/v1/plans/{plan_id}",
            json={"name": "Updated", "price_usd": 3.50},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert float(data["price_usd"]) == 3.50

    def test_update_nonexistent_plan(self):
        """Test updating a plan that doesn't exist."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"planbadupdate{unique_id}@test.com",
            f"BadUpdateCompany {unique_id}",
        )
        csrf = get_csrf_token(token)

        fake_id = str(uuid.uuid4())
        response = client.patch(
            f"/api/v1/plans/{fake_id}",
            json={"name": "New Name"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )

        assert response.status_code == 404


class TestPlansDelete:
    """Test plan deletion."""

    def test_delete_plan_success(self):
        """Test deleting a plan (soft delete)."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"plandelete{unique_id}@test.com",
            f"DeleteCompany {unique_id}",
        )

        # Create plan
        csrf = get_csrf_token(token)
        create = client.post(
            "/api/v1/plans",
            json={
                "name": "To Delete",
                "duration_minutes": 30,
                "price_usd": 2.50,
                "is_active": True,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )
        plan_id = create.json()["id"]

        # Delete plan
        csrf = get_csrf_token(token)
        response = client.delete(
            f"/api/v1/plans/{plan_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )

        assert response.status_code == 204

        # Verify it's deleted (not in list)
        list_response = client.get(
            "/api/v1/plans",
            headers={"Authorization": f"Bearer {token}"},
        )
        plans = list_response.json()
        assert not any(p["id"] == plan_id for p in plans)

    def test_delete_nonexistent_plan(self):
        """Test deleting a plan that doesn't exist."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"planbaddelete{unique_id}@test.com",
            f"BadDeleteCompany {unique_id}",
        )
        csrf = get_csrf_token(token)

        fake_id = str(uuid.uuid4())
        response = client.delete(
            f"/api/v1/plans/{fake_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )

        assert response.status_code == 404


class TestPlansTenantIsolation:
    """Test multi-tenant isolation for plans."""

    def test_cannot_see_other_tenant_plans(self):
        """Test that users cannot see other tenant's plans."""
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

        # User 1 creates a plan
        csrf1 = get_csrf_token(token1)
        create = client.post(
            "/api/v1/plans",
            json={
                "name": "User1 Plan",
                "duration_minutes": 30,
                "price_usd": 2.50,
                "is_active": True,
            },
            headers={
                "Authorization": f"Bearer {token1}",
                "X-CSRF-Token": csrf1,
            },
        )
        plan_id = create.json()["id"]

        # User 2 lists plans - should not see User1's plan
        list2 = client.get(
            "/api/v1/plans",
            headers={"Authorization": f"Bearer {token2}"},
        )
        plans2 = list2.json()
        assert not any(p["id"] == plan_id for p in plans2)

    def test_cannot_update_other_tenant_plan(self):
        """Test that users cannot update other tenant's plans."""
        unique_id1 = uuid.uuid4()
        token1 = register_and_login(
            f"tenant3{unique_id1}@test.com",
            f"Tenant3 {unique_id1}",
        )

        unique_id2 = uuid.uuid4()
        token2 = register_and_login(
            f"tenant4{unique_id2}@test.com",
            f"Tenant4 {unique_id2}",
        )

        # User 1 creates a plan
        csrf1 = get_csrf_token(token1)
        create = client.post(
            "/api/v1/plans",
            json={
                "name": "User1 Plan",
                "duration_minutes": 30,
                "price_usd": 2.50,
                "is_active": True,
            },
            headers={
                "Authorization": f"Bearer {token1}",
                "X-CSRF-Token": csrf1,
            },
        )
        plan_id = create.json()["id"]

        # User 2 tries to update - should fail
        csrf2 = get_csrf_token(token2)
        response = client.patch(
            f"/api/v1/plans/{plan_id}",
            json={"name": "Hacked"},
            headers={
                "Authorization": f"Bearer {token2}",
                "X-CSRF-Token": csrf2,
            },
        )

        assert response.status_code == 404
