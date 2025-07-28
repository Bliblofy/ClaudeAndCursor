#!/usr/bin/env python3
"""
Git Deployment Script with Deployment Log Analysis
Automatically reads deployment logs, updates README/gitignore, and creates deployment commits
"""

import subprocess
import sys
import json
import os
from datetime import datetime
from pathlib import Path
import tempfile
import re
import time
import glob

class GitDeploymentScript:
    def __init__(self):
        self.repo_root = self._find_git_root()
        self.changes = {}
        self.claude_analysis = ""
        # Change to git root directory
        os.chdir(self.repo_root)
        
    def _find_git_root(self):
        """Find the root directory of the git repository"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                capture_output=True,
                text=True,
                check=True
            )
            return Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            print("Error: Not in a git repository")
            sys.exit(1)
    
    def _run_command(self, cmd, check=True):
        """Run a shell command and return output"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=check,
                shell=isinstance(cmd, str)
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            if check:
                print(f"Error running command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
                print(f"Error: {e.stderr}")
                sys.exit(1)
            return None
    
    def check_git_status(self):
        """Check current git status and collect changes"""
        print("[*] Checking git status...")
        
        # Get current branch
        self.current_branch = self._run_command(['git', 'branch', '--show-current'])
        print(f"   Current branch: {self.current_branch}")
        
        # Get uncommitted changes
        status = self._run_command(['git', 'status', '--porcelain'])
        if not status:
            print("   No changes to commit")
            return False
        
        # Parse changes
        self.changes = {
            'added': [],
            'modified': [],
            'deleted': [],
            'untracked': []
        }
        
        for line in status.split('\n'):
            if not line:
                continue
            status_code = line[:2]
            file_path = line[3:]
            
            # First character is staging area, second is working tree
            staged = status_code[0]
            working = status_code[1]
            
            if status_code == '??':
                self.changes['untracked'].append(file_path)
            elif staged == 'M' or working == 'M':
                self.changes['modified'].append(file_path)
            elif staged == 'A' or working == 'A':
                self.changes['added'].append(file_path)
            elif staged == 'D' or working == 'D':
                # Only add to deleted list if not already staged
                if staged != 'D':
                    self.changes['deleted'].append(file_path)
        
        print(f"   Found {sum(len(v) for v in self.changes.values())} changes")
        return True
    
    def get_latest_deployment_file(self):
        """Find the latest deployment file in DeploymentLogs directory"""
        # Look for DeploymentLogs in multiple possible locations
        possible_dirs = [
            self.repo_root / 'DeploymentLogs',
            self.repo_root / 'drippingWallet' / 'DeploymentLogs',
            self.repo_root / 'DrippingWallet' / 'DeploymentLogs',
            Path.cwd() / 'DeploymentLogs',
            Path.cwd().parent / 'DeploymentLogs'
        ]
        
        deployment_logs_dir = None
        for dir_path in possible_dirs:
            if dir_path.exists():
                deployment_logs_dir = dir_path
                break
        
        if not deployment_logs_dir:
            print("\n[!] DeploymentLogs directory not found")
            print("    Please run deployment-agent.sh first to generate a deployment log")
            print("    Searched in:")
            for dir_path in possible_dirs:
                print(f"      - {dir_path}")
            return None
        
        # Find all deployment files
        deployment_files = list(deployment_logs_dir.glob('Deployment_*.txt'))
        
        if not deployment_files:
            print("\n[!] No deployment files found in DeploymentLogs directory")
            print("    Please run deployment-agent.sh first to generate a deployment log")
            return None
        
        # Sort by modification time and get the latest
        latest_file = max(deployment_files, key=lambda f: f.stat().st_mtime)
        return latest_file
    
    def parse_deployment_file(self, deployment_file):
        """Parse the deployment file to extract relevant information"""
        print(f"\n[*] Reading deployment file: {deployment_file.name}")
        
        try:
            with open(deployment_file, 'r') as f:
                content = f.read()
            
            # Initialize analysis dictionary
            self.deployment_info = {
                'deployment_number': '',
                'deployment_date': '',
                'deployed_by': '',
                'title': '',
                'description': '',
                'changes': {}
            }
            
            # Parse the file line by line
            lines = content.split('\n')
            for i, line in enumerate(lines):
                # Extract deployment number
                if line.startswith('Deployment Number:'):
                    self.deployment_info['deployment_number'] = line.split(':', 1)[1].strip()
                
                # Extract deployment date
                elif line.startswith('Deployment Date:'):
                    self.deployment_info['deployment_date'] = line.split(':', 1)[1].strip()
                
                # Extract deployed by
                elif line.startswith('Deployed By:'):
                    self.deployment_info['deployed_by'] = line.split(':', 1)[1].strip()
                
                # Extract title
                elif line.startswith('Title:'):
                    self.deployment_info['title'] = line.split(':', 1)[1].strip()
                
                # Extract description
                elif line.startswith('Description:'):
                    self.deployment_info['description'] = line.split(':', 1)[1].strip()
            
            print(f"    Deployment: {self.deployment_info['deployment_number']}")
            print(f"    Title: {self.deployment_info['title']}")
            print(f"    Description: {self.deployment_info['description']}")
            
            return True
            
        except Exception as e:
            print(f"\n[!] Error parsing deployment file: {e}")
            return False
    
    def analyze_with_deployment_log(self):
        """Analyze changes using the latest deployment log"""
        print("\n[*] Analyzing changes from deployment log...")
        
        # Get the latest deployment file
        deployment_file = self.get_latest_deployment_file()
        if not deployment_file:
            return False
        
        # Parse the deployment file
        if not self.parse_deployment_file(deployment_file):
            return False
        
        # Convert deployment info to claude_analysis format for compatibility
        self.claude_analysis = {
            'deployment_comment': self.deployment_info['title'][:72],  # Limit to 72 chars
            'summary': self.deployment_info['description'],
            'readme_updates': [],  # Can be extended if needed
            'gitignore_updates': [],  # Can be extended if needed
            'should_update_readme': False,  # README is already updated by deployment-agent.sh
            'should_update_gitignore': False  # .gitignore updates can be handled separately
        }
        
        # Check if we should update README (deployment-agent.sh already does this)
        # We'll skip README updates since deployment-agent.sh handles it
        
        print("\n[*] Analysis complete!")
        print(f"    Using deployment {self.deployment_info['deployment_number']}")
        return True
    
    def update_readme(self):
        """Update README.md based on Claude's suggestions"""
        if not self.claude_analysis.get('should_update_readme'):
            return
        
        print("\n[*] Updating README.md...")
        readme_path = self.repo_root / 'README.md'
        
        if readme_path.exists():
            content = readme_path.read_text()
        else:
            content = f"# {self.repo_root.name}\n\n"
        
        # Add Claude's suggested updates
        updates = self.claude_analysis.get('readme_updates', [])
        if updates:
            content += f"\n\n## Recent Updates ({datetime.now().strftime('%Y-%m-%d')})\n"
            for update in updates:
                content += f"- {update}\n"
        
        readme_path.write_text(content)
        self._run_command(['git', 'add', 'README.md'])
        print("   README.md updated")
    
    def update_gitignore(self):
        """Update .gitignore based on Claude's suggestions"""
        if not self.claude_analysis.get('should_update_gitignore'):
            return
        
        print("\n[*] Updating .gitignore...")
        gitignore_path = self.repo_root / '.gitignore'
        
        if gitignore_path.exists():
            content = gitignore_path.read_text()
        else:
            content = ""
        
        # Add Claude's suggested patterns
        patterns = self.claude_analysis.get('gitignore_updates', [])
        if patterns:
            if content and not content.endswith('\n'):
                content += '\n'
            content += f"\n# Added by automated deployment - {datetime.now().strftime('%Y-%m-%d')}\n"
            for pattern in patterns:
                if pattern not in content:
                    content += f"{pattern}\n"
        
        gitignore_path.write_text(content)
        self._run_command(['git', 'add', '.gitignore'])
        print("   .gitignore updated")
    
    def stage_changes(self):
        """Stage all changes for commit"""
        print("\n[*] Staging changes...")
        
        # Add all modified and new files
        for file_list in [self.changes['modified'], self.changes['added'], self.changes['untracked']]:
            for file_path in file_list:
                # Check if file exists before trying to add it
                full_path = self.repo_root / file_path
                if full_path.exists():
                    self._run_command(['git', 'add', file_path])
                else:
                    print(f"   Warning: Skipping non-existent file: {file_path}")
        
        # Handle deleted files
        for file_path in self.changes['deleted']:
            # Check if file is tracked in git before trying to remove
            check_result = self._run_command(
                ['git', 'ls-files', '--error-unmatch', file_path], 
                check=False
            )
            if check_result is not None:
                # File is tracked, so we can remove it
                self._run_command(['git', 'rm', '--cached', file_path])
        
        print("   All changes staged")
    
    def create_deployment_commit(self):
        """Create the deployment commit with deployment log message"""
        print("\n[*] Creating deployment commit...")
        
        # Get commit message from deployment info
        if hasattr(self, 'deployment_info') and self.deployment_info.get('title'):
            commit_message = f"Deployment {self.deployment_info['deployment_number']}: {self.deployment_info['title']}"
        elif self.claude_analysis:
            commit_message = self.claude_analysis.get('deployment_comment', 'Automated deployment')
        else:
            commit_message = f"Automated deployment - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Add metadata to commit message
        full_message = f"{commit_message}\n\n"
        full_message += f"Branch: {self.current_branch}\n"
        full_message += f"Automated by: gitDeploy.py\n"
        full_message += f"Timestamp: {datetime.now().isoformat()}\n"
        
        if hasattr(self, 'deployment_info'):
            full_message += f"Deployment Log: {self.deployment_info['deployment_number']}\n"
            full_message += f"\nSummary: {self.deployment_info['description']}\n"
        elif self.claude_analysis:
            full_message += f"\nSummary: {self.claude_analysis.get('summary', 'N/A')}\n"
        
        # Create commit
        self._run_command(['git', 'commit', '-m', full_message])
        print(f"   Commit created: {commit_message}")
    
    def push_to_remote(self):
        """Push changes to remote repository"""
        print("\n[*] Pushing to remote...")
        
        # Check if we need to set upstream
        upstream = self._run_command(
            ['git', 'rev-parse', '--abbrev-ref', f'{self.current_branch}@{{upstream}}'],
            check=False
        )
        
        if upstream:
            self._run_command(['git', 'push'])
        else:
            self._run_command(['git', 'push', '-u', 'origin', self.current_branch])
        
        print("   Changes pushed successfully!")
    
    def run(self):
        """Main deployment workflow"""
        print("[*] Git Deployment Script Started")
        print("=" * 50)
        
        # Check git status
        if not self.check_git_status():
            print("\n[+] Nothing to deploy")
            return
        
        # Analyze with deployment log
        print("\n[*] Looking for deployment log...")
        print("    Please ensure you have run deployment-agent.sh before running this script")
        deployment_success = self.analyze_with_deployment_log()
        
        if not deployment_success:
            print("\n[!] Deployment cancelled due to deployment log analysis failure")
            sys.exit(1)
        
        # Stage existing changes
        self.stage_changes()
        
        # Update files based on analysis (skip README as deployment-agent.sh handles it)
        # self.update_readme()  # Commented out as deployment-agent.sh already updates README
        self.update_gitignore()
        
        # Create deployment commit
        self.create_deployment_commit()
        
        # Push to remote
        try:
            self.push_to_remote()
            print("\n[+] Deployment completed successfully!")
        except Exception as e:
            print(f"\n[!] Push failed: {e}")
            print("   You can manually push with: git push")

def main():
    """Main entry point"""
    try:
        script = GitDeploymentScript()
        script.run()
    except KeyboardInterrupt:
        print("\n\n[!] Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()