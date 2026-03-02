#!/usr/bin/env python3
"""
Auto-sync with GitHub repository at session start
"""

import subprocess
import sys
from pathlib import Path

def sync_repository():
    """Check for and pull updates from GitHub"""
    workspace = Path('/root/.openclaw/workspace')
    
    print("🔍 Checking for updates from GitHub...")
    
    try:
        # Fetch latest from origin
        result = subprocess.run(
            ['git', 'fetch', 'origin', 'main'],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"⚠️  Could not reach GitHub: {result.stderr}")
            return False
        
        # Get current and remote commit hashes
        local = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=10
        ).stdout.strip()
        
        remote = subprocess.run(
            ['git', 'rev-parse', 'origin/main'],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=10
        ).stdout.strip()
        
        if local != remote:
            print(f"📥 Updates found on GitHub")
            print(f"   Local:  {local[:7]}")
            print(f"   Remote: {remote[:7]}")
            print()
            print("🔄 Pulling updates...")
            
            # Pull updates
            pull_result = subprocess.run(
                ['git', 'pull', 'origin', 'main'],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if pull_result.returncode == 0:
                print()
                print("✅ Sync complete")
                
                # Show recent commits
                print()
                print("📋 Recent changes:")
                log_result = subprocess.run(
                    ['git', 'log', '--oneline', '-3'],
                    cwd=workspace,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                print(log_result.stdout)
                return True
            else:
                print(f"❌ Pull failed: {pull_result.stderr}")
                return False
        else:
            print(f"✅ Already up to date ({local[:7]})")
            return True
            
    except subprocess.TimeoutExpired:
        print("⚠️  Git operation timed out")
        return False
    except Exception as e:
        print(f"⚠️  Sync error: {e}")
        return False

if __name__ == '__main__':
    sync_repository()
