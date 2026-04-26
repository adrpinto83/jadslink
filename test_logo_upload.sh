#!/bin/bash

# Test logo upload functionality
echo "=== Testing Logo Upload Feature ==="
echo ""

# 1. Register with Free plan
echo "1. Registering user with Free plan..."
FREE_USER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Free Company",
    "email": "free@test.com",
    "password": "Password123"
  }')
echo "Response: $FREE_USER_RESPONSE"
echo ""

# 2. Login with Free plan
echo "2. Logging in with Free plan user..."
FREE_LOGIN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "free@test.com",
    "password": "Password123"
  }')
FREE_TOKEN=$(echo $FREE_LOGIN | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "Access Token: ${FREE_TOKEN:0:20}..."
echo ""

# 3. Try to upload logo with Free plan (should fail)
echo "3. Attempting logo upload with Free plan (should fail)..."
cd /tmp
echo "P3,3,1" > test.pnm
FREE_UPLOAD=$(curl -s -X POST http://localhost:8000/api/v1/tenants/me/logo \
  -H "Authorization: Bearer $FREE_TOKEN" \
  -F "file=@test.pnm")
echo "Response: $FREE_UPLOAD"
echo ""

# 4. Check tenant info
echo "4. Checking tenant info..."
curl -s -X GET http://localhost:8000/api/v1/tenants/me \
  -H "Authorization: Bearer $FREE_TOKEN" | grep -o '"plan_tier":"[^"]*' || echo "Could not retrieve plan tier"

echo ""
echo "=== Test Complete ==="
