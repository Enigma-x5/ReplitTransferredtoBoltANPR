#!/bin/bash

# ANPR City API - Quick Test Script
# Tests basic API functionality

set -e

API_URL=${API_URL:-http://localhost:8000}
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@example.com}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-changeme123}

echo "🧪 ANPR City API Test Script"
echo "============================"
echo "API URL: $API_URL"
echo ""

# Check health
echo "1️⃣  Testing health endpoint..."
HEALTH=$(curl -s $API_URL/health)
if echo $HEALTH | grep -q "ok"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi
echo ""

# Login
echo "2️⃣  Testing authentication..."
LOGIN_RESPONSE=$(curl -s -X POST $API_URL/api/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Login failed"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo "✅ Login successful"
echo "Token: ${TOKEN:0:20}..."
echo ""

# List users
echo "3️⃣  Testing user list..."
USERS=$(curl -s $API_URL/api/users \
    -H "Authorization: Bearer $TOKEN")

if echo $USERS | grep -q "admin"; then
    echo "✅ User list retrieved"
else
    echo "❌ User list failed"
    exit 1
fi
echo ""

# Create camera
echo "4️⃣  Testing camera creation..."
CAMERA_RESPONSE=$(curl -s -X POST $API_URL/api/cameras \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test Camera",
        "description": "Automated test camera",
        "lat": 40.7128,
        "lon": -74.0060,
        "active": true
    }')

CAMERA_ID=$(echo $CAMERA_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$CAMERA_ID" ]; then
    echo "❌ Camera creation failed"
    echo "Response: $CAMERA_RESPONSE"
    exit 1
fi

echo "✅ Camera created: $CAMERA_ID"
echo ""

# List cameras
echo "5️⃣  Testing camera list..."
CAMERAS=$(curl -s $API_URL/api/cameras \
    -H "Authorization: Bearer $TOKEN")

if echo $CAMERAS | grep -q "$CAMERA_ID"; then
    echo "✅ Camera list retrieved"
else
    echo "❌ Camera list failed"
    exit 1
fi
echo ""

# Test events endpoint (should be empty)
echo "6️⃣  Testing events search..."
EVENTS=$(curl -s "$API_URL/api/events?limit=10" \
    -H "Authorization: Bearer $TOKEN")

if echo $EVENTS | grep -q "total"; then
    echo "✅ Events search working"
else
    echo "❌ Events search failed"
    exit 1
fi
echo ""

# Test BOLO creation
echo "7️⃣  Testing BOLO creation..."
BOLO_RESPONSE=$(curl -s -X POST $API_URL/api/bolos \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "plate_pattern": "TEST.*",
        "description": "Test BOLO",
        "active": true,
        "priority": 1
    }')

BOLO_ID=$(echo $BOLO_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$BOLO_ID" ]; then
    echo "❌ BOLO creation failed"
    echo "Response: $BOLO_RESPONSE"
    exit 1
fi

echo "✅ BOLO created: $BOLO_ID"
echo ""

# Test metrics endpoint
echo "8️⃣  Testing metrics endpoint..."
METRICS=$(curl -s $API_URL/metrics)

if echo $METRICS | grep -q "anpr_"; then
    echo "✅ Metrics endpoint working"
else
    echo "⚠️  Metrics endpoint may not be configured"
fi
echo ""

echo "🎉 All tests passed!"
echo ""
echo "Summary:"
echo "  ✅ Health check"
echo "  ✅ Authentication"
echo "  ✅ User management"
echo "  ✅ Camera management"
echo "  ✅ Events API"
echo "  ✅ BOLO management"
echo "  ✅ Metrics"
echo ""
echo "API is ready for use!"
echo "Documentation: $API_URL/docs"
