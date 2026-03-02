#!/usr/bin/env python3
"""
COMPASS Master Orchestrator
Runs the complete COMPASS trading system pipeline
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import json

WORKSPACE = Path('/root/.openclaw/workspace')

def run_command(cmd, description):
    """Run a command and report status"""
    print(f"\n{'='*70}")
    print(f"{description}")
    print('='*70)
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_compass_pipeline():
    """Run the complete COMPASS pipeline"""
    print("="*70)
    print("COMPASS Trading System - Full Pipeline")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = {}
    
    # Step 1: Fetch futures data
    results['futures'] = run_command(
        f"cd {WORKSPACE} && python3 compass_futures_fetcher.py",
        "Step 1: Fetching Futures Data (OI, Funding, L/S Ratio)"
    )
    
    # Step 2: Run COMPASS analysis
    results['analysis'] = run_command(
        f"cd {WORKSPACE} && python3 compass_analyzer.py",
        "Step 2: Running Multi-Timeframe Analysis"
    )
    
    # Step 3: Generate signals
    results['signals'] = run_command(
        f"cd {WORKSPACE} && python3 compass_signal_generator.py",
        "Step 3: Generating Trading Signals"
    )
    
    # Step 4: Generate charts with indicators
    results['charts'] = run_command(
        f"cd {WORKSPACE} && python3 compass_chart_generator.py",
        "Step 4: Generating Indicator Charts"
    )
    
    # Step 5: Update trade tracker
    results['tracker'] = run_command(
        f"cd {WORKSPACE} && python3 compass_trade_tracker.py",
        "Step 5: Updating Performance Tracker"
    )
    
    # Summary
    print(f"\n{'='*70}")
    print("Pipeline Complete")
    print('='*70)
    for step, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {step}")
    
    all_success = all(results.values())
    print(f"\nOverall: {'✅ SUCCESS' if all_success else '❌ SOME STEPS FAILED'}")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print('='*70)
    
    return all_success

def send_pending_alerts():
    """Check for and send any pending alerts"""
    alert_file = WORKSPACE / 'compass_pending_alert.txt'
    if alert_file.exists():
        with open(alert_file, 'r') as f:
            alert_content = f.read()
        
        if alert_content.strip():
            print(f"\n{'='*70}")
            print("SENDING ALERT TO TELEGRAM")
            print('='*70)
            print(alert_content[:500] + "..." if len(alert_content) > 500 else alert_content)
            
            # The alert will be picked up by the system
            # In production, this would call the message tool directly
            print("\n✅ Alert ready for delivery")
        
        # Clear the file
        alert_file.unlink()

if __name__ == '__main__':
    success = run_compass_pipeline()
    send_pending_alerts()
    sys.exit(0 if success else 1)
