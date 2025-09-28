#!/bin/bash

# Curl Examples for Multimodal Database Session Demo API
# 
# These examples show how to use the API with curl commands.
# Make sure the API server is running: docker compose exec app python api_server.py

BASE_URL="http://localhost:8000"

echo "🚀 Multimodal Database Session Demo API - Curl Examples"
echo "====================================================="
echo ""

# Test health endpoint
echo "1. Testing health endpoint..."
curl -X GET "$BASE_URL/health" | jq .
echo ""

# Test root endpoint
echo "2. Testing root endpoint..."
curl -X GET "$BASE_URL/" | jq .
echo ""

# Test text-only chat
echo "3. Testing text-only chat..."
curl -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "user_input=Hello! What time is it?" \
  -d "user_id=curl_test_user" | jq .
echo ""

# Test file upload
echo "4. Testing file upload..."
echo "Creating test file..."
echo "This is a test file for curl upload!" > test_file.txt

curl -X POST "$BASE_URL/chat" \
  -F "user_input=Please analyze this file" \
  -F "user_id=curl_test_user" \
  -F "file=@test_file.txt" | jq .
echo ""

# Test base64 data URI
echo "5. Testing base64 data URI..."
# Create base64 encoded content
echo -n "This is base64 encoded content for testing!" | base64 -w 0 > base64_content.txt
BASE64_CONTENT=$(cat base64_content.txt)
DATA_URI="data:text/plain;base64,$BASE64_CONTENT"

curl -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "user_input=Please analyze this base64 content" \
  -d "user_id=curl_test_user" \
  -d "data_uri=$DATA_URI" | jq .
echo ""

# Test session listing
echo "6. Testing session listing..."
curl -X GET "$BASE_URL/sessions/curl_test_user" | jq .
echo ""

# Test new session flag
echo "7. Testing new session creation..."
curl -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "user_input=This should create a new session" \
  -d "user_id=curl_test_user" \
  -d "new_session=true" | jq .
echo ""

# Clean up test files
echo "Cleaning up test files..."
rm -f test_file.txt base64_content.txt

echo ""
echo "✅ All curl examples completed!"
echo ""
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔗 Health Check: http://localhost:8000/health"
echo ""
echo "💡 Tips:"
echo "• Use jq for pretty JSON output: curl ... | jq ."
echo "• For file uploads, use -F instead of -d"
echo "• Check the API docs for more examples"
echo "• Sessions persist across API calls"
