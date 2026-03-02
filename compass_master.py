#!/usr/bin/env python3
"""
COMPASS Master Orchestrator
Runs the complete COMPASS trading system pipeline
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

# Get workspace path dynamically
def get_workspace():
    """Get workspace path from environment or derive from script location"""
    # Option 1: From environment variable
    env_path = os.environ.get('COMPASS_WORKSPACE')
    if env_path:
        return Path(env_path)
    
    # Option 2: Derive from script location
    # Script is in workspace root
    return Path(__file__).resolve().parent

WORKSPACE = get_workspace()

# Required scripts for pipeline
REQUIRED_SCRIPTS = [
    'compass_futures_fetcher.py',
    'compass_alert_check.py',
    'compass_trade_tracker.py'
]

def validate_scripts():
    """Validate that all required scripts exist"""
    missing = []
    for script in REQUIRED_SCRIPTS:
        script_path = WORKSPACE / script
        if not script_path.exists():
            missing.append(script)
    
    if missing:
        print(f"ERROR: Missing required scripts: {', '.join(missing)}")
        print(f"Workspace: {WORKSPACE}")
        return False
    return True

def run_command(cmd_list, description, timeout=300):
    """
    Run a command using argument list (safer than shell=True)
    
    Args:
        cmd_list: List of command arguments (not shell string)
        description: Description of the step
        timeout: Timeout in seconds
    """
    print(f"\n{'='*70}")
    print(f"{description}")
    print('='*70)
    
    try:
        # Use shell=False with argument list (safer)
        result = subprocess.run(
            cmd_list,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=WORKSPACE
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"ERROR: Command timed out after {timeout}s")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_compass_pipeline():
    """Run the complete COMPASS pipeline"""
    print("="*70)
    print("COMPASS Trading System - Full Pipeline")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Workspace: {WORKSPACE}")
    print("="*70)
    
    # Validate scripts exist
    if not validate_scripts():
        return False
    
    results = {}
    
    # Step 1: Fetch futures data
    results['futures'] = run_command(
        [sys.executable, 'compass_futures_fetcher.py'],
        "Step 1: Fetching Futures Data (OI, Funding, L/S Ratio)"
    )
    
    # Step 2: Check for alerts
    results['alerts'] = run_command(
        [sys.executable, 'compass_alert_check.py'],
        "Step 2: Checking Alert Conditions"
    )
    
    # Step 3: Update trade tracker
    results['tracker'] = run_command(
        [sys.executable, 'compass_trade_tracker.py'],
        "Step 3: Updating Performance Tracker"
    )
    
    # Summary
    print(f"\n{'='*70}")
    print("Pipeline Complete")
    print('='*70)
    for step, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {step}")
    
    all_success = all(results.values())
    overall_msg = 'SUCCESS' if all_success else 'SOME STEPS FAILED'
    print(f"\nOverall: {overall_msg}")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print('='*70)
    
    return all_success

def send_pending_alerts():
    """Check for and send any pending alerts"""
    alert_file = WORKSPACE / 'compass_pending_alert.txt'
    if alert_file.exists():
        try:
            with open(alert_file, 'r') as f:
                alert_content = f.read()
            
            if alert_content.strip():
                print(f"\n{'='*70}")
                print("PENDING ALERT FOUND")
                print('='*70)
                print(alert_content[:500] + "..." if len(alert_content) > 500 else alert_content)
                print("\n✅ Alert ready for delivery")
        except Exception as e:
            print(f"Warning: Could not read alert file: {e}")

if __name__ == '__main__':
    success = run_compass_pipeline()
    send_pending_alerts()
    sys.exit(0 if success else 1)
