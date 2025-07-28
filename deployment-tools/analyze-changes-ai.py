#!/usr/bin/env python3
"""
AI-powered change analyzer for deployment with security checks
Uses Claude Code to intelligently analyze git changes and detect sensitive files
"""

import subprocess
import json
import sys
import os
import re
from pathlib import Path
import fnmatch

class GitignoreParser:
    """Parse .gitignore files and check if files should be ignored"""
    
    def __init__(self, repo_root=None):
        self.repo_root = repo_root or self._find_repo_root()
        self.ignore_patterns = []
        self.sensitive_patterns = [
            # API keys and secrets (more specific patterns)
            '*_api_key*', '*_apikey*', '*_secret*', '*_token*', '*_password*',
            '*.pem', '*.key', '*.p12', '*.pfx', '*.jks',
            
            # Environment files
            '.env*', '*.env', 'env.*',
            
            # Config files with potential secrets (more specific)
            '*credentials*.json', '*secrets*.json', 
            'GoogleService-Info.plist', 'google-services.json',
            
            # Database files
            '*.db', '*.sqlite', '*.sqlite3',
            
            # Private keys and certificates
            'id_rsa*', 'id_dsa*', '*.ppk', 'id_*.pub',
            
            # AWS/Cloud credentials
            '.aws/*', 'credentials', '*.tfvars',
            
            # Other sensitive files
            '*.log', '*.dump', 'npm-debug.log*', 'yarn-debug.log*',
            '.DS_Store', 'Thumbs.db'
        ]
        self._load_gitignore()
    
    def _find_repo_root(self):
        """Find the git repository root"""
        try:
            result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return os.getcwd()
    
    def _load_gitignore(self):
        """Load all .gitignore files in the repository"""
        # Find all .gitignore files
        for root, dirs, files in os.walk(self.repo_root):
            if '.gitignore' in files:
                gitignore_path = os.path.join(root, '.gitignore')
                self._parse_gitignore_file(gitignore_path, root)
    
    def _parse_gitignore_file(self, gitignore_path, base_dir):
        """Parse a single .gitignore file"""
        try:
            with open(gitignore_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Convert gitignore pattern to glob pattern
                    pattern = line
                    if pattern.startswith('/'):
                        # Absolute path from the gitignore location
                        pattern = os.path.join(base_dir, pattern[1:])
                    else:
                        # Relative pattern
                        pattern = os.path.join(base_dir, '**', pattern)
                    
                    self.ignore_patterns.append(pattern)
        except Exception as e:
            print(f"Warning: Could not parse {gitignore_path}: {e}", file=sys.stderr)
    
    def should_ignore(self, file_path):
        """Check if a file should be ignored based on .gitignore patterns"""
        abs_path = os.path.abspath(file_path)
        
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(abs_path, pattern):
                return True
            # Also check if any parent directory matches
            if '**' in pattern:
                parts = pattern.split('**')
                if len(parts) == 2 and abs_path.startswith(parts[0]) and abs_path.endswith(parts[1]):
                    return True
        
        return False
    
    def is_sensitive(self, file_path):
        """Check if a file might contain sensitive information"""
        file_name = os.path.basename(file_path).lower()
        file_path_lower = file_path.lower()
        
        for pattern in self.sensitive_patterns:
            if fnmatch.fnmatch(file_name, pattern.lower()) or \
               fnmatch.fnmatch(file_path_lower, pattern.lower()):
                return True
        
        # Check for common secret patterns in file path (more specific)
        # Only check basename to reduce false positives
        sensitive_keywords = ['_secret', '_password', '_token', '_key', 'credential', 
                            'private_', 'api_key', 'apikey']
        
        for keyword in sensitive_keywords:
            if keyword in file_name:
                return True
        
        return False

def get_git_changes():
    """Get list of changed files from git status"""
    try:
        # Get modified files
        modified = subprocess.run(['git', 'diff', '--name-only'], 
                                capture_output=True, text=True).stdout.strip().split('\n')
        
        # Get staged files
        staged = subprocess.run(['git', 'diff', '--cached', '--name-only'], 
                              capture_output=True, text=True).stdout.strip().split('\n')
        
        # Get untracked files
        untracked = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], 
                                 capture_output=True, text=True).stdout.strip().split('\n')
        
        # Combine and remove empty strings
        all_files = list(filter(None, set(modified + staged + untracked)))
        
        return all_files
    except Exception as e:
        print(f"Error getting git changes: {e}")
        return []

def check_sensitive_files(files, gitignore_parser):
    """Check for sensitive files that shouldn't be committed"""
    sensitive_files = []
    ignored_files = []
    
    for file in files:
        if gitignore_parser.should_ignore(file):
            ignored_files.append(file)
        elif gitignore_parser.is_sensitive(file):
            sensitive_files.append(file)
    
    return sensitive_files, ignored_files

def get_file_diff(file_path):
    """Get the diff for a specific file"""
    try:
        # Check if file is tracked
        is_tracked = subprocess.run(['git', 'ls-files', file_path], 
                                  capture_output=True, text=True).stdout.strip()
        
        if is_tracked:
            # Get diff for tracked file
            diff = subprocess.run(['git', 'diff', 'HEAD', file_path], 
                                capture_output=True, text=True).stdout
            if not diff:
                # Try staged diff
                diff = subprocess.run(['git', 'diff', '--cached', file_path], 
                                    capture_output=True, text=True).stdout
        else:
            # For untracked files, show the content (limited)
            try:
                with open(file_path, 'r') as f:
                    content = f.read(1000)  # Read first 1000 chars
                diff = f"New file: {file_path}\n\n{content}"
                if len(content) == 1000:
                    diff += "..."
            except:
                diff = f"New file: {file_path} (binary or unreadable)"
        
        return diff
    except Exception as e:
        return f"Error getting diff for {file_path}: {e}"

def categorize_files(files):
    """Categorize files by their type/location"""
    categories = {
        'iOS': [],
        'Android': [],
        'Backend': [],
        'Website': [],
        'Documentation': [],
        'CI/CD': [],
        'Deployment': [],
        'Other': []
    }
    
    for file in files:
        file_lower = file.lower()
        categorized = False
        
        # Check for deployment tools
        if 'deployment-tools' in file or 'deploy' in file_lower:
            categories['Deployment'].append(file)
            categorized = True
        elif 'drippingwallet/' in file and 'android' not in file_lower:
            if file.endswith('.swift') or 'ios' in file_lower:
                categories['iOS'].append(file)
                categorized = True
        elif 'android' in file_lower or 'dippingwalletandroid' in file_lower:
            categories['Android'].append(file)
            categorized = True
        elif 'firebase' in file_lower or 'functions' in file_lower:
            categories['Backend'].append(file)
            categorized = True
        elif 'website' in file_lower:
            categories['Website'].append(file)
            categorized = True
        elif file.endswith('.md') or 'readme' in file_lower:
            categories['Documentation'].append(file)
            categorized = True
        elif '.github' in file or 'workflow' in file_lower:
            categories['CI/CD'].append(file)
            categorized = True
        
        if not categorized:
            categories['Other'].append(file)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}

def create_ai_prompt(categories, sample_diffs, sensitive_files):
    """Create a prompt for Claude Code to analyze the changes"""
    prompt = f"""Analyze the following git changes for the DrippingWallet project and provide:
1. A concise, descriptive title (max 80 chars) summarizing the main changes
2. A detailed description (2-3 sentences) explaining what was changed and why it matters
3. A list of key improvements or features added
4. Any potential risks or breaking changes

"""
    
    if sensitive_files:
        prompt += f"⚠️  WARNING: {len(sensitive_files)} potentially sensitive files detected!\n"
        prompt += "These files might contain secrets or sensitive information:\n"
        for file in sensitive_files[:10]:  # Show first 10
            prompt += f"  - {file}\n"
        if len(sensitive_files) > 10:
            prompt += f"  ... and {len(sensitive_files) - 10} more files\n"
        prompt += "\n"
    
    prompt += "Changed files by category:\n"
    
    for category, files in categories.items():
        if files:
            prompt += f"\n{category}:\n"
            for file in files[:5]:  # Limit to first 5 files per category
                prompt += f"  - {file}\n"
            if len(files) > 5:
                prompt += f"  ... and {len(files) - 5} more files\n"
    
    prompt += "\nSample diffs from key files:\n"
    
    for file, diff in sample_diffs[:3]:  # Show up to 3 sample diffs
        prompt += f"\n--- {file} ---\n"
        prompt += diff[:500] + "...\n" if len(diff) > 500 else diff + "\n"
    
    return prompt

def write_analysis_file(title, description, details, security_warnings):
    """Write the AI analysis to a temporary file"""
    analysis = {
        'title': title,
        'description': description,
        'details': details,
        'security_warnings': security_warnings
    }
    
    analysis_file = '/tmp/deployment_analysis.json'
    with open(analysis_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    return analysis_file

def main():
    print("[*] AI-Powered Change Analyzer with Security Checks")
    print("=" * 50)
    
    # Initialize gitignore parser
    gitignore_parser = GitignoreParser()
    
    # Get changed files
    changed_files = get_git_changes()
    if not changed_files:
        print("No changes detected")
        sys.exit(1)
    
    print(f"Found {len(changed_files)} changed files")
    
    # Check for sensitive files
    sensitive_files, ignored_files = check_sensitive_files(changed_files, gitignore_parser)
    
    security_warnings = []
    
    if sensitive_files:
        print(f"\n⚠️  WARNING: Found {len(sensitive_files)} potentially sensitive files!")
        for file in sensitive_files[:5]:
            print(f"   - {file}")
        if len(sensitive_files) > 5:
            print(f"   ... and {len(sensitive_files) - 5} more")
        
        security_warnings.append({
            'type': 'sensitive_files',
            'message': f'Found {len(sensitive_files)} potentially sensitive files',
            'files': sensitive_files
        })
        
        # Check if running in interactive mode
        if sys.stdin.isatty():
            # Ask for confirmation
            response = input("\nDo you want to add these files to .gitignore? (y/N): ")
            if response.lower() == 'y':
                with open('.gitignore', 'a') as f:
                    f.write("\n# Automatically added sensitive files\n")
                    for file in sensitive_files:
                        f.write(f"{file}\n")
                print("Added sensitive files to .gitignore")
                
                # Remove sensitive files from the changed files list
                changed_files = [f for f in changed_files if f not in sensitive_files]
        else:
            # Non-interactive mode - just warn and exclude files
            print("\nNon-interactive mode: Excluding sensitive files from deployment")
            changed_files = [f for f in changed_files if f not in sensitive_files]
    
    if ignored_files:
        print(f"\nNote: {len(ignored_files)} files are already in .gitignore and will be skipped")
        # Remove ignored files from the list
        changed_files = [f for f in changed_files if f not in ignored_files]
    
    if not changed_files:
        print("No files to analyze after filtering")
        sys.exit(1)
    
    # Categorize files
    categories = categorize_files(changed_files)
    
    # Get sample diffs from important files
    sample_diffs = []
    important_patterns = ['.swift', '.kt', '.ts', '.tsx', '.py', 'gradle', 'package.json']
    
    for file in changed_files[:10]:  # Limit to first 10 files
        if any(pattern in file for pattern in important_patterns):
            diff = get_file_diff(file)
            if diff and "Error" not in diff:
                sample_diffs.append((file, diff))
    
    # Create prompt for AI analysis
    prompt = create_ai_prompt(categories, sample_diffs, sensitive_files)
    
    # Save prompt to file for Claude Code to read
    prompt_file = '/tmp/deployment_prompt.txt'
    with open(prompt_file, 'w') as f:
        f.write(prompt)
    
    print(f"\nPrompt saved to: {prompt_file}")
    
    # Analyze the changes to generate a meaningful title and description
    title_parts = []
    
    # Check for major features based on file patterns
    has_analytics = any('analytics' in f.lower() for f in changed_files)
    has_auth = any('auth' in f.lower() or 'superadmin' in f.lower() for f in changed_files)
    has_android_update = any('gradle' in f or 'android' in f.lower() for f in changed_files)
    has_deployment = any('deploy' in f.lower() or 'workflow' in f.lower() for f in changed_files)
    
    # Build title based on actual changes
    if has_analytics:
        title_parts.append("Analytics")
    if has_android_update and len([f for f in changed_files if 'android' in f.lower()]) > 10:
        title_parts.append("Android SDK Update")
    if has_auth:
        title_parts.append("Auth System")
    if has_deployment:
        title_parts.append("CI/CD")
    
    # Add category-based parts
    if len(categories.get('iOS', [])) > 3:
        title_parts.append("iOS Updates")
    if len(categories.get('Website', [])) > 3:
        title_parts.append("Web Updates")
    
    # Generate title
    if title_parts:
        title = "Update: " + ", ".join(title_parts[:3])  # Limit to 3 main features
        if len(title) > 80:
            title = title[:77] + "..."
    else:
        title = f"Project Update: {len(changed_files)} Files Changed"
    
    # Add security warning to title if needed
    if sensitive_files and len(title) < 60:
        title = "⚠️  " + title
    
    # Generate description based on the changes
    descriptions = []
    if has_analytics:
        descriptions.append("Introduces Simple Analytics integration for privacy-friendly user tracking")
    if has_android_update:
        descriptions.append(f"Updates Android platform with {len(categories.get('Android', []))} file changes")
    if has_auth:
        descriptions.append("Implements enhanced authentication with role-based access control")
    if has_deployment:
        descriptions.append("Adds automated deployment workflows")
    
    description = ". ".join(descriptions[:2]) + "." if descriptions else f"Updates {len(changed_files)} files across multiple components."
    
    # Build detailed feature list
    key_features = []
    technical_changes = []
    breaking_changes = []
    
    # Analyze specific file patterns for features
    if has_analytics:
        key_features.append("Simple Analytics integration for iOS and Android")
    if any('room' in f.lower() or 'database' in f.lower() for f in changed_files):
        technical_changes.append("Database schema updates with Room persistence")
    if any('test' in f.lower() for f in changed_files):
        technical_changes.append(f"Test coverage improvements ({len([f for f in changed_files if 'test' in f.lower()])} test files)")
    if any('auth' in f.lower() for f in changed_files):
        key_features.append("Firebase authentication with superadmin support")
    if any('.yml' in f for f in changed_files):
        key_features.append("GitHub Actions CI/CD workflows")
    if any('legal' in f.lower() for f in changed_files):
        key_features.append("Multi-language legal documentation (DE, FR, IT, GSW)")
    
    # Check for breaking changes
    if any('security' in f.lower() or 'rules' in f.lower() for f in changed_files):
        breaking_changes.append("Security rules updated - may affect API access")
    if any('migration' in f.lower() for f in changed_files):
        breaking_changes.append("Database migrations required")
    
    details = {
        "key_features": key_features[:6],  # Limit to 6 features
        "technical_changes": technical_changes[:6],
        "breaking_changes": breaking_changes,
        "categories_affected": list(categories.keys())
    }
    
    # Write analysis results
    analysis_file = write_analysis_file(title, description, details, security_warnings)
    print(f"\nAnalysis saved to: {analysis_file}")
    
    # Exit with error code if sensitive files were found
    if sensitive_files:
        sys.exit(1)

if __name__ == "__main__":
    main()