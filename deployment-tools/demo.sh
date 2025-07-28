#!/bin/bash

# Demonstration script for deployment tools

echo "=== Deployment Tools Demo ==="
echo ""
echo "This demo shows how the deployment tools work with security features."
echo ""

# Create some test files
echo "Creating test files..."
echo "Normal code file" > test_code.js
echo "API_KEY=secret123" > test_api_key.txt
echo "password=admin" > config_password.json

# Add files to git staging
git add test_code.js test_api_key.txt config_password.json 2>/dev/null

echo ""
echo "Created 3 test files:"
echo "- test_code.js (normal file)"
echo "- test_api_key.txt (contains API key)"
echo "- config_password.json (contains password)"
echo ""
echo "Press Enter to run the deployment agent..."
read

# Run deployment agent
echo ""
echo "Running deployment agent..."
./deployment-agent.sh

# Cleanup
echo ""
echo "Cleaning up test files..."
rm -f test_code.js test_api_key.txt config_password.json
git reset HEAD test_code.js test_api_key.txt config_password.json 2>/dev/null

echo ""
echo "Demo complete!"