#!/bin/bash

# DrippingWallet Deployment Agent
# This script analyzes git changes, updates README, and creates deployment logs

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Configuration
DEPLOYMENT_LOGS_DIR="../DeploymentLogs"
README_FILE="../README.md"
GITDEPLOY_SCRIPT="$SCRIPT_DIR/gitDeploy.py"

# Create deployment logs directory if it doesn't exist
mkdir -p "$DEPLOYMENT_LOGS_DIR"

# Function to get the next deployment number
get_next_deployment_number() {
    if [ -z "$(ls -A $DEPLOYMENT_LOGS_DIR 2>/dev/null)" ]; then
        echo "1.0"
    else
        # Find the highest number from existing deployment files
        last_number=$(ls "$DEPLOYMENT_LOGS_DIR"/Deployment_*.txt 2>/dev/null | \
                      sed -n 's/.*Deployment_\([0-9]*\.[0-9]*\)_.*/\1/p' | \
                      sort -n | tail -1)
        
        if [ -z "$last_number" ]; then
            echo "1.0"
        else
            # Increment by 0.1
            echo "$last_number + 0.1" | bc
        fi
    fi
}

# Function to get formatted date
get_formatted_date() {
    date +"%Y%m%d_%H%M%S"
}

# Function to analyze git changes
analyze_git_changes() {
    echo "=== Git Status Analysis ==="
    echo ""
    
    # Get current branch
    current_branch=$(git branch --show-current)
    echo "Current Branch: $current_branch"
    echo ""
    
    # Get uncommitted changes
    echo "Uncommitted Changes:"
    git status --short
    echo ""
    
    # Get last 5 commits
    echo "Recent Commits:"
    git log --oneline -5
    echo ""
    
    # Get detailed diff statistics
    echo "Change Statistics:"
    git diff --stat
    echo ""
    
    # Get list of changed files
    echo "Changed Files:"
    git diff --name-only
    echo ""
}

# Function to generate change summary using AI
generate_change_summary() {
    local title=""
    local description=""
    
    # Run AI-powered analysis
    echo "Running AI-powered change analysis..." >&2
    
    # Run the Python analyzer which generates intelligent analysis
    python3 "$SCRIPT_DIR/analyze-changes-ai.py" >&2
    
    # Read the AI analysis if available
    if [ -f /tmp/deployment_analysis.json ]; then
        # Extract title and description from JSON
        title=$(python3 -c "import json; data=json.load(open('/tmp/deployment_analysis.json')); print(data.get('title', 'Project Update'))")
        description=$(python3 -c "import json; data=json.load(open('/tmp/deployment_analysis.json')); print(data.get('description', 'Multiple changes across the project.'))")
    fi
    
    # Fallback to basic analysis if AI analysis failed or no title generated
    if [ -z "$title" ]; then
        echo "Falling back to basic change analysis..." >&2
        
        # Count the number of modified files
        modified_count=$(git status --porcelain | grep -c "^ M")
        added_count=$(git status --porcelain | grep -c "^??")
        
        # Get the main areas of change
        if git status --porcelain | grep -q "android"; then
            title="${title}Android Updates, "
        fi
        
        if git status --porcelain | grep -q "drippingWallet/"; then
            title="${title}iOS Updates, "
        fi
        
        if git status --porcelain | grep -q "website/"; then
            title="${title}Website Updates, "
        fi
        
        if git status --porcelain | grep -q ".github/"; then
            title="${title}CI/CD Updates, "
        fi
        
        # Remove trailing comma and space
        title=$(echo "$title" | sed 's/, $//')
        
        # If no specific updates found, use generic title
        if [ -z "$title" ]; then
            title="General Updates"
        fi
        
        # Generate description based on file changes
        description="This deployment includes $modified_count modified files and $added_count new files."
        
        # Add specific change details
        if git status --porcelain | grep -q "analytics"; then
            description="$description Analytics implementation added."
        fi
        
        if git status --porcelain | grep -q "test"; then
            description="$description Test coverage improved."
        fi
        
        if git status --porcelain | grep -q "gradle"; then
            description="$description Android dependencies updated."
        fi
    fi
    
    echo "$title|$description"
}

# Function to update README
update_readme() {
    local deployment_number=$1
    local deployment_date=$2
    local title=$3
    
    # Check if README exists
    if [ ! -f "$README_FILE" ]; then
        echo "README.md not found. Skipping README update."
        return
    fi
    
    # Create a temporary file
    temp_file=$(mktemp)
    
    # Flag to track if we've found the deployment history section
    found_section=false
    
    # Read README line by line
    while IFS= read -r line; do
        echo "$line" >> "$temp_file"
        
        # Look for deployment history section
        if [[ "$line" == "## Deployment History"* ]] || [[ "$line" == "## Recent Deployments"* ]]; then
            found_section=true
            echo "" >> "$temp_file"
            echo "- **v$deployment_number** ($(date +"%Y-%m-%d %H:%M")) - $title" >> "$temp_file"
        fi
    done < "$README_FILE"
    
    # If section doesn't exist, add it at the end
    if [ "$found_section" = false ]; then
        echo "" >> "$temp_file"
        echo "## Deployment History" >> "$temp_file"
        echo "" >> "$temp_file"
        echo "- **v$deployment_number** ($(date +"%Y-%m-%d %H:%M")) - $title" >> "$temp_file"
    fi
    
    # Replace original README with updated version
    mv "$temp_file" "$README_FILE"
    echo "README.md updated with deployment v$deployment_number"
}

# Main execution
echo "DrippingWallet Deployment Agent"
echo "==============================="
echo ""

# Get deployment number and date
deployment_number=$(get_next_deployment_number)
deployment_date=$(get_formatted_date)
deployment_filename="Deployment_${deployment_number}_${deployment_date}.txt"
deployment_filepath="$DEPLOYMENT_LOGS_DIR/$deployment_filename"

echo "Creating deployment log: $deployment_filename"
echo ""

# Generate change summary
change_data=$(generate_change_summary)
IFS='|' read -r title description <<< "$change_data"

# Check if AI analysis detected sensitive files
if [ -f /tmp/deployment_analysis.json ]; then
    security_warnings=$(python3 -c "
import json
try:
    with open('/tmp/deployment_analysis.json') as f:
        data = json.load(f)
        warnings = data.get('security_warnings', [])
        if warnings:
            for w in warnings:
                if w['type'] == 'sensitive_files':
                    print(f\"WARNING: {w['message']}\")
                    for file in w['files'][:3]:
                        print(f\"  - {file}\")
                    if len(w['files']) > 3:
                        print(f\"  ... and {len(w['files']) - 3} more\")
except:
    pass
")
    
    if [ -n "$security_warnings" ]; then
        echo ""
        echo "⚠️  Security Warning:"
        echo "$security_warnings"
        echo ""
        read -p "Do you want to continue with deployment? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Deployment cancelled due to security concerns."
            rm -f /tmp/deployment_analysis.json /tmp/deployment_prompt.txt
            exit 1
        fi
    fi
fi

# Create deployment log file
{
    echo "DrippingWallet Deployment Log"
    echo "============================"
    echo ""
    echo "Deployment Number: v$deployment_number"
    echo "Deployment Date: $(date +"%Y-%m-%d %H:%M:%S")"
    echo "Deployed By: $(git config user.name)"
    echo ""
    echo "Title: $title"
    echo "Description: $description"
    echo ""
    
    # Add AI analysis details if available
    if [ -f /tmp/deployment_analysis.json ]; then
        echo "AI Analysis Details:"
        echo "-------------------"
        python3 -c "
import json
try:
    with open('/tmp/deployment_analysis.json') as f:
        data = json.load(f)
        details = data.get('details', {})
        
        if 'key_features' in details and details['key_features']:
            print('\nKey Features:')
            for feature in details['key_features']:
                print(f'  • {feature}')
        
        if 'technical_changes' in details and details['technical_changes']:
            print('\nTechnical Changes:')
            for change in details['technical_changes']:
                print(f'  • {change}')
        
        if 'breaking_changes' in details and details['breaking_changes']:
            print('\n⚠️  Breaking Changes:')
            for change in details['breaking_changes']:
                print(f'  • {change}')
                
        warnings = data.get('security_warnings', [])
        if warnings:
            print('\n🔒 Security Notes:')
            for w in warnings:
                print(f'  • {w[\"message\"]}')
except:
    pass
"
        echo ""
    fi
    
    echo "----------------------------------------"
    echo ""
    analyze_git_changes
    echo ""
    echo "----------------------------------------"
    echo ""
    echo "Detailed Changes:"
    echo ""
    git diff
} > "$deployment_filepath"

echo "Deployment log created: $deployment_filepath"
echo ""

# Update README
update_readme "$deployment_number" "$deployment_date" "$title"

# Clean up temporary files
rm -f /tmp/deployment_analysis.json /tmp/deployment_prompt.txt

echo ""
echo "Deployment agent completed successfully!"
echo "- Deployment Number: v$deployment_number"
echo "- Log File: $deployment_filepath"
echo "- README.md updated"

# Call gitDeploy.py script if it exists
if [ -f "$GITDEPLOY_SCRIPT" ]; then
    echo ""
    echo "Executing gitDeploy.py script..."
    python3 "$GITDEPLOY_SCRIPT"
else
    echo ""
    echo "Note: gitDeploy.py script not found at $GITDEPLOY_SCRIPT"
    echo "Skipping automatic git deployment."
fi