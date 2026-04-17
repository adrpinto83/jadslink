
import httpx
import random
import string

BASE_URL = "http://localhost:8000/api/v1"
OPERATOR_EMAIL = "operator@test.io"
OPERATOR_PASSWORD = "operator123"

def get_random_serial():
    return "SN" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

def main():
    try:
        # 1. Login to get token
        with httpx.Client() as client:
            login_data = {
                "username": OPERATOR_EMAIL,
                "password": OPERATOR_PASSWORD,
            }
            login_response = client.post(f"{BASE_URL}/auth/login", data=login_data)
            login_response.raise_for_status()
            token = login_response.json()["access_token"]
            
            headers = {"Authorization": f"Bearer {token}"}

            # 2. Create a new node
            node_name = f"Test Node {random.randint(100, 999)}"
            node_serial = get_random_serial()
            node_data = {"name": node_name, "serial": node_serial}
            
            print(f"Creating node: {node_data}")
            
            node_response = client.post(f"{BASE_URL}/nodes", headers=headers, json=node_data)
            
            if 200 <= node_response.status_code < 300:
                print("✅ Node created successfully!")
                print(node_response.json())
            else:
                print(f"❌ Error creating node: {node_response.status_code}")
                try:
                    print(node_response.json())
                except Exception:
                    print(node_response.text)

    except httpx.RequestError as e:
        print(f"An error occurred while requesting {e.request.url!r}.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
