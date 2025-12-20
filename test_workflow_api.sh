#!/bin/bash

# Test script to debug GitHub workflow dispatch API call

echo "=== Testing GitHub Workflow Dispatch API ==="
echo ""

# You need to set your GitHub PAT here temporarily for testing
# Get it from Vercel environment variables
GITHUB_PAT="YOUR_GITHUB_PAT_HERE"
REPO_OWNER="KenHuang21"
REPO_NAME="strategic-cockpit-backend"
WORKFLOW_FILE="update_data.yml"

echo "1. Testing with workflow filename..."
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: Bearer ${GITHUB_PAT}" \
  -H "Content-Type: application/json" \
  "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${WORKFLOW_FILE}/dispatches" \
  -d '{"ref":"main"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -v 2>&1 | grep -A 5 "HTTP\|message\|error"

echo ""
echo "2. Getting workflow ID..."
WORKFLOW_ID=$(curl -s \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${WORKFLOW_FILE}" \
  | grep '"id"' | head -1 | grep -o '[0-9]*')

echo "Workflow ID: ${WORKFLOW_ID}"

echo ""
echo "3. Testing with workflow ID..."
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: Bearer ${GITHUB_PAT}" \
  -H "Content-Type: application/json" \
  "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${WORKFLOW_ID}/dispatches" \
  -d '{"ref":"main"}' \
  -w "\nHTTP Status: %{http_code}\n"

echo ""
echo "4. Checking workflow permissions..."
curl -s \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${WORKFLOW_FILE}" \
  | grep -A 2 "state\|path"
