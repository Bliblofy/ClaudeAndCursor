# Deployment Tools

An intelligent deployment system that uses AI to analyze code changes, detect sensitive files, create meaningful deployment logs, and automatically commit/push to GitHub.

## Features

- **AI-Powered Analysis**: Intelligently analyzes git changes to generate meaningful deployment titles and descriptions
- **Security Checks**: Automatically detects potentially sensitive files using .gitignore parsing and pattern matching
- **Comprehensive Logging**: Creates detailed deployment logs with categorized changes and AI insights
- **Automatic Git Integration**: Commits and pushes changes with meaningful commit messages
- **Portable**: All scripts use relative paths and can be copied to any project
- **GitHub Integration**: Automatically pushes deployments to your GitHub repository

## Installation

1. Copy the entire `deployment-tools` folder to your project root
2. Make scripts executable:
   ```bash
   chmod +x deployment-tools/*.sh deployment-tools/*.py
   ```
3. Ensure Python 3 is installed on your system
4. Ensure Git is configured with your GitHub credentials (see GitHub Setup below)

## Quick Start

From your project root:
```bash
./deployment-tools/deployment-agent.sh
```

This will:
1. Analyze all git changes using AI
2. Check for sensitive files that shouldn't be committed
3. Generate a deployment log with meaningful descriptions
4. Update your README.md with deployment history
5. Commit all changes with a descriptive message
6. Push to your GitHub repository

## GitHub Setup

### 1. Configure Git User Information
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 2. Set Up GitHub Authentication

#### Option A: Using Personal Access Token (Recommended)
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (full control of private repositories)
4. Copy the generated token
5. Configure git to use the token:
   ```bash
   git config --global credential.helper store
   # Next git push will prompt for username and password
   # Use your GitHub username and the token as password
   ```

#### Option B: Using SSH Keys
1. Generate SSH key:
   ```bash
   ssh-keygen -t ed25519 -C "your.email@example.com"
   ```
2. Add to SSH agent:
   ```bash
   eval "$(ssh-agent -s)"
   ssh-add ~/.ssh/id_ed25519
   ```
3. Copy public key:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```
4. Add to GitHub: Settings → SSH and GPG keys → New SSH key
5. Update remote URL to use SSH:
   ```bash
   git remote set-url origin git@github.com:username/repository.git
   ```

### 3. Connect Your Project to GitHub

If your project isn't already connected to GitHub:
```bash
# Create a new repository on GitHub first, then:
git remote add origin https://github.com/username/repository.git
# or for SSH:
git remote add origin git@github.com:username/repository.git
```

## Configuration

Edit the following variables in `deployment-agent.sh`:

```bash
# Configuration
DEPLOYMENT_LOGS_DIR="../DeploymentLogs"    # Where to store deployment logs
README_FILE="../README.md"                 # README file to update
```

## File Structure

```
deployment-tools/
├── deployment-agent.sh       # Main deployment script
├── analyze-changes-ai.py     # AI-powered change analyzer with security checks
├── claude-analyze-wrapper.sh # Wrapper for Claude Code integration
├── gitDeploy.py             # Git automation script (commit & push)
├── demo.sh                  # Demonstration script
└── README.md                # This file
```

## How It Works

### 1. Change Detection
- Scans all modified, staged, and untracked files in your git repository
- Uses `git status` to identify what has changed

### 2. Security Analysis
- Parses all .gitignore files in the repository
- Checks for sensitive file patterns (API keys, passwords, tokens, etc.)
- Prompts for action if sensitive files are found
- Automatically excludes sensitive files from deployment

### 3. AI Analysis
- Categorizes files by component (iOS, Android, Backend, etc.)
- Identifies key features based on file patterns
- Generates meaningful titles and descriptions
- Detects breaking changes and technical updates

### 4. Deployment Log
Creates a comprehensive log with:
- AI-generated summary
- Security warnings
- Key features and technical changes
- Detailed git status and diffs
- Timestamp and author information

### 5. README Update
Automatically maintains deployment history in your README.md

### 6. Git Operations
- Stages all safe changes
- Creates a commit with deployment information
- Pushes to the configured remote repository

## Security Features

### Sensitive File Patterns
The system checks for files containing:
- API keys, secrets, tokens, passwords
- Environment files (.env, *.env)
- Configuration files with credentials
- Private keys and certificates (*.pem, *.key, *.p12)
- Database files (*.db, *.sqlite)
- Cloud credentials (.aws/*, *.tfvars)
- Log files and dumps

### Interactive Security Prompts
When sensitive files are detected:
- In interactive mode: Prompts to add files to .gitignore
- In non-interactive mode: Automatically excludes files
- Shows security warnings in deployment logs

## Example Workflow

```bash
# 1. Make your code changes
vim src/api.js

# 2. Run deployment agent
./deployment-tools/deployment-agent.sh

# 3. Review the output
[*] AI-Powered Change Analyzer with Security Checks
==================================================
Found 15 changed files

⚠️  WARNING: Found 1 potentially sensitive file!
   - config/api_key.json

Non-interactive mode: Excluding sensitive files from deployment

Title: Update: API Integration, Security Fixes
Description: Implements new API endpoints for user management. Fixes authentication vulnerabilities.

# 4. Deployment automatically continues
Creating deployment log: Deployment_1.2_20250728_120000.txt
Staging changes...
Creating deployment commit...
Pushing to remote...

[+] Deployment completed successfully!
```

## Troubleshooting

### "Command not found" Error
Make sure scripts are executable:
```bash
chmod +x deployment-tools/*.sh deployment-tools/*.py
```

### "Not in a git repository" Error
Initialize git in your project:
```bash
git init
```

### "No remote repository" Error
Add a remote repository:
```bash
git remote add origin https://github.com/username/repository.git
```

### Push Authentication Failed
1. Check your git credentials:
   ```bash
   git config --list | grep credential
   ```
2. Update stored credentials:
   ```bash
   git config --global --unset credential.helper
   git config --global credential.helper store
   ```
3. Try pushing manually first:
   ```bash
   git push -u origin main
   ```

### Sensitive Files Detected
1. Review the files listed as sensitive
2. Add legitimate sensitive files to .gitignore
3. Remove or encrypt actual sensitive data
4. Re-run the deployment agent

## Advanced Usage

### Custom Ignore Patterns
Add patterns to your `.gitignore`:
```
# API Keys
*_api_key.json
*.secrets

# Environment
.env.local
.env.production
```

### Manual Deployment Without Push
To create deployment logs without pushing:
1. Comment out the gitDeploy.py call in deployment-agent.sh
2. Run the deployment agent
3. Manually commit and push when ready

### Integration with CI/CD
The deployment tools can be integrated with GitHub Actions:
```yaml
- name: Run Deployment Agent
  run: |
    ./deployment-tools/deployment-agent.sh
```

## Best Practices

1. **Always Review Changes**: Check the deployment log before it pushes
2. **Keep Secrets Secure**: Never commit API keys or passwords
3. **Use .gitignore**: Add sensitive file patterns proactively
4. **Regular Deployments**: Deploy frequently with small changes
5. **Meaningful Descriptions**: The AI generates good summaries, but you can edit the deployment log before pushing

## Requirements

- Git 2.0+
- Python 3.6+
- Bash 4.0+
- bc (for version calculations)
- Active internet connection (for pushing to GitHub)

## License

This deployment system is provided as-is for use in your projects.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review git and GitHub documentation
3. Ensure all prerequisites are installed
4. Verify your GitHub authentication is working
