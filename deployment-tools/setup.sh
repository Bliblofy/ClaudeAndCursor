#!/bin/bash

# Setup script for deployment tools
echo "=== Deployment Tools Setup ==="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if bc is installed
if ! command -v bc &> /dev/null; then
    echo "❌ bc is not installed. Please install bc (usually part of basic unix tools)."
    exit 1
fi

echo "✓ All required tools are installed"
echo ""

# Make scripts executable
echo "Making scripts executable..."
chmod +x *.sh *.py
echo "✓ Scripts are now executable"
echo ""

# Check git configuration
echo "Checking git configuration..."
git_user=$(git config --global user.name)
git_email=$(git config --global user.email)

if [ -z "$git_user" ] || [ -z "$git_email" ]; then
    echo "❌ Git user information not configured"
    echo ""
    echo "Please configure git with your information:"
    echo "  git config --global user.name \"Your Name\""
    echo "  git config --global user.email \"your.email@example.com\""
    echo ""
    read -p "Would you like to configure it now? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your name: " name
        read -p "Enter your email: " email
        git config --global user.name "$name"
        git config --global user.email "$email"
        echo "✓ Git configured successfully"
    else
        echo "Please configure git before using deployment tools"
        exit 1
    fi
else
    echo "✓ Git user: $git_user <$git_email>"
fi
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository"
    echo ""
    read -p "Would you like to initialize a git repository? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git init
        echo "✓ Git repository initialized"
    else
        echo "Please run this setup from within a git repository"
        exit 1
    fi
fi
echo ""

# Check for remote repository
if ! git remote -v | grep -q origin; then
    echo "⚠️  No remote repository configured"
    echo ""
    echo "To connect to GitHub:"
    echo "1. Create a repository on GitHub"
    echo "2. Run: git remote add origin https://github.com/username/repository.git"
    echo ""
else
    remote_url=$(git remote get-url origin)
    echo "✓ Remote repository: $remote_url"
fi
echo ""

# Create DeploymentLogs directory if it doesn't exist
if [ ! -d "../DeploymentLogs" ]; then
    mkdir -p ../DeploymentLogs
    echo "✓ Created DeploymentLogs directory"
fi

# Check README.md
if [ ! -f "../README.md" ]; then
    echo "⚠️  No README.md found in parent directory"
    echo "   A README.md will be created when you run the deployment agent"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To run your first deployment:"
echo "  cd .."
echo "  ./deployment-tools/deployment-agent.sh"
echo ""
echo "For more information, see deployment-tools/README.md"