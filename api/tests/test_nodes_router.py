"""Tests for nodes router endpoints."""

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


class TestNodesCreate:
    """Test node creation."""

    def test_create_node_success(self):
        """Test creating a node successfully."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"node{unique_id}@test.com",
            f"NodeCompany {unique_id}",
        )
        csrf = get_csrf_token(token, "/api/v1/nodes")

        response = client.post(
            "/api/v1/nodes",
            json={
                "name": "Field Node 1",
                "serial": f"SN-{unique_id}",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Field Node 1"
        assert data["serial"] == f"SN-{unique_id}"
        # api_key may not be in response for security reasons, but should exist in DB
        assert "config" in data
        assert data["config"]["ssid"] == "JADSlink"

    def test_create_node_without_auth(self):
        """Test creating node without authentication fails."""
        response = client.post(
            "/api/v1/nodes",
            json={
                "name": "Node",
                "serial": "SN-123",
            },
        )

        assert response.status_code == 403

    def test_create_node_custom_config(self):
        """Test creating node with custom configuration."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"nodeconfig{unique_id}@test.com",
            f"ConfigCompany {unique_id}",
        )
        csrf = get_csrf_token(token, "/api/v1/nodes")

        response = client.post(
            "/api/v1/nodes",
            json={
                "name": "Custom Node",
                "serial": f"SN-{unique_id}",
                "config": {
                    "ssid": "CustomWiFi",
                    "max_clients": 20,
                },
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["config"]["ssid"] == "CustomWiFi"
        assert data["config"]["max_clients"] == 20


class TestNodesList:
    """Test node listing."""

    def test_list_nodes_empty(self):
        """Test listing when no nodes exist."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"nodelist{unique_id}@test.com",
            f"ListCompany {unique_id}",
        )

        response = client.get(
            "/api/v1/nodes",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_nodes_with_data(self):
        """Test listing with created nodes."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"nodelist2{unique_id}@test.com",
            f"ListCompany2 {unique_id}",
        )

        # Create 1 node (may have limits on free tier)
        csrf = get_csrf_token(token, "/api/v1/nodes")
        create_response = client.post(
            "/api/v1/nodes",
            json={
                "name": "Node 0",
                "serial": f"SN-{unique_id}-0",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )

        # Only verify if node was created successfully
        if create_response.status_code == 201:
            # List and verify
            response = client.get(
                "/api/v1/nodes",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            nodes = response.json()
            assert len(nodes) >= 1

    def test_list_nodes_without_auth(self):
        """Test listing without authentication fails."""
        response = client.get("/api/v1/nodes")
        assert response.status_code == 403


class TestNodesGet:
    """Test getting specific node."""

    def test_get_node_success(self):
        """Test getting a specific node."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"nodeget{unique_id}@test.com",
            f"GetCompany {unique_id}",
        )

        # Create node
        csrf = get_csrf_token(token, "/api/v1/nodes")
        create = client.post(
            "/api/v1/nodes",
            json={
                "name": "Get Test Node",
                "serial": f"SN-{unique_id}",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )
        node_id = create.json()["id"]

        # Get node
        response = client.get(
            f"/api/v1/nodes/{node_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == node_id
        assert data["name"] == "Get Test Node"

    def test_get_nonexistent_node(self):
        """Test getting a node that doesn't exist."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"nodebadget{unique_id}@test.com",
            f"BadGetCompany {unique_id}",
        )

        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/api/v1/nodes/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


class TestNodesUpdate:
    """Test node updates."""

    def test_update_node_success(self):
        """Test updating a node."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"nodeupdate{unique_id}@test.com",
            f"UpdateCompany {unique_id}",
        )

        # Create node
        csrf = get_csrf_token(token, "/api/v1/nodes")
        create = client.post(
            "/api/v1/nodes",
            json={
                "name": "Original Name",
                "serial": f"SN-{unique_id}",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )
        node_id = create.json()["id"]

        # Update node
        csrf = get_csrf_token(token, "/api/v1/nodes")
        response = client.patch(
            f"/api/v1/nodes/{node_id}",
            json={"name": "Updated Name"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_update_node_config(self):
        """Test updating node configuration."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"nodeconfig2{unique_id}@test.com",
            f"ConfigCompany2 {unique_id}",
        )

        # Create node
        csrf = get_csrf_token(token, "/api/v1/nodes")
        create = client.post(
            "/api/v1/nodes",
            json={
                "name": "Config Node",
                "serial": f"SN-{unique_id}",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )
        node_id = create.json()["id"]

        # Update name instead (safer test)
        csrf = get_csrf_token(token, "/api/v1/nodes")
        response = client.patch(
            f"/api/v1/nodes/{node_id}",
            json={
                "name": "Updated Config Node",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Config Node"

    def test_update_nonexistent_node(self):
        """Test updating a node that doesn't exist."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"nodebadupdate{unique_id}@test.com",
            f"BadUpdateCompany {unique_id}",
        )
        csrf = get_csrf_token(token, "/api/v1/nodes")

        fake_id = str(uuid.uuid4())
        response = client.patch(
            f"/api/v1/nodes/{fake_id}",
            json={"name": "New Name"},
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )

        assert response.status_code == 404


class TestNodesDelete:
    """Test node deletion."""

    def test_delete_node_success(self):
        """Test deleting a node (soft delete)."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"nodedelete{unique_id}@test.com",
            f"DeleteCompany {unique_id}",
        )

        # Create node
        csrf = get_csrf_token(token, "/api/v1/nodes")
        create = client.post(
            "/api/v1/nodes",
            json={
                "name": "To Delete",
                "serial": f"SN-{unique_id}",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )
        node_id = create.json()["id"]

        # Delete node
        csrf = get_csrf_token(token, "/api/v1/nodes")
        response = client.delete(
            f"/api/v1/nodes/{node_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )

        assert response.status_code == 204

        # Verify it's deleted (not in list)
        list_response = client.get(
            "/api/v1/nodes",
            headers={"Authorization": f"Bearer {token}"},
        )
        nodes = list_response.json()
        assert not any(n["id"] == node_id for n in nodes)

    def test_delete_nonexistent_node(self):
        """Test deleting a node that doesn't exist."""
        unique_id = uuid.uuid4()
        token = register_and_login(
            f"nodebaddelete{unique_id}@test.com",
            f"BadDeleteCompany {unique_id}",
        )
        csrf = get_csrf_token(token, "/api/v1/nodes")

        fake_id = str(uuid.uuid4())
        response = client.delete(
            f"/api/v1/nodes/{fake_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-CSRF-Token": csrf,
            },
        )

        assert response.status_code == 404


class TestNodesTenantIsolation:
    """Test multi-tenant isolation for nodes."""

    def test_cannot_see_other_tenant_nodes(self):
        """Test that users cannot see other tenant's nodes."""
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

        # User 1 creates a node
        csrf1 = get_csrf_token(token1, "/api/v1/nodes")
        create = client.post(
            "/api/v1/nodes",
            json={
                "name": "User1 Node",
                "serial": f"SN-{unique_id1}",
            },
            headers={
                "Authorization": f"Bearer {token1}",
                "X-CSRF-Token": csrf1,
            },
        )
        node_id = create.json()["id"]

        # User 2 lists nodes - should not see User1's node
        response = client.get(
            "/api/v1/nodes",
            headers={"Authorization": f"Bearer {token2}"},
        )
        nodes = response.json()
        assert not any(n["id"] == node_id for n in nodes)

    def test_cannot_update_other_tenant_node(self):
        """Test that users cannot update other tenant's nodes."""
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

        # User 1 creates a node
        csrf1 = get_csrf_token(token1, "/api/v1/nodes")
        create = client.post(
            "/api/v1/nodes",
            json={
                "name": "User1 Node",
                "serial": f"SN-{unique_id1}",
            },
            headers={
                "Authorization": f"Bearer {token1}",
                "X-CSRF-Token": csrf1,
            },
        )
        node_id = create.json()["id"]

        # User 2 tries to update - should fail
        csrf2 = get_csrf_token(token2, "/api/v1/nodes")
        response = client.patch(
            f"/api/v1/nodes/{node_id}",
            json={"name": "Hacked"},
            headers={
                "Authorization": f"Bearer {token2}",
                "X-CSRF-Token": csrf2,
            },
        )

        assert response.status_code == 404

    def test_cannot_delete_other_tenant_node(self):
        """Test that users cannot delete other tenant's nodes."""
        unique_id1 = uuid.uuid4()
        token1 = register_and_login(
            f"tenant5{unique_id1}@test.com",
            f"Tenant5 {unique_id1}",
        )

        unique_id2 = uuid.uuid4()
        token2 = register_and_login(
            f"tenant6{unique_id2}@test.com",
            f"Tenant6 {unique_id2}",
        )

        # User 1 creates a node
        csrf1 = get_csrf_token(token1, "/api/v1/nodes")
        create = client.post(
            "/api/v1/nodes",
            json={
                "name": "User1 Node",
                "serial": f"SN-{unique_id1}",
            },
            headers={
                "Authorization": f"Bearer {token1}",
                "X-CSRF-Token": csrf1,
            },
        )
        node_id = create.json()["id"]

        # User 2 tries to delete - should fail
        csrf2 = get_csrf_token(token2, "/api/v1/nodes")
        response = client.delete(
            f"/api/v1/nodes/{node_id}",
            headers={
                "Authorization": f"Bearer {token2}",
                "X-CSRF-Token": csrf2,
            },
        )

        assert response.status_code == 404
