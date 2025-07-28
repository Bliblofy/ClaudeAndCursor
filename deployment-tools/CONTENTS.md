# Deployment Tools Contents

This folder contains a complete deployment automation system that can be copied to any project.

## Files Included

### Core Scripts
- **deployment-agent.sh** - Main deployment orchestrator
- **analyze-changes-ai.py** - AI-powered change analyzer with security checks  
- **gitDeploy.py** - Git automation (commit & push)
- **claude-analyze-wrapper.sh** - Claude Code integration wrapper

### Utilities
- **setup.sh** - Initial setup and configuration checker
- **demo.sh** - Interactive demonstration of features

### Documentation
- **README.md** - Complete user guide with GitHub setup instructions
- **CONTENTS.md** - This file

## Key Features

1. **Security First**
   - Automatic .gitignore parsing
   - Sensitive file detection
   - Interactive security prompts

2. **AI Analysis**
   - Intelligent change categorization
   - Meaningful deployment descriptions
   - Breaking change detection

3. **Full Automation**
   - Deployment log generation
   - README history updates
   - Git commit creation
   - Automatic push to GitHub

4. **Portability**
   - All paths are relative
   - No hardcoded project references
   - Single folder contains everything

## Usage

1. Copy this entire folder to your project root
2. Run `./deployment-tools/setup.sh` to verify configuration
3. Run `./deployment-tools/deployment-agent.sh` to deploy

## Requirements

- Git 2.0+
- Python 3.6+
- Bash 4.0+
- bc (basic calculator)
- GitHub account with configured authentication