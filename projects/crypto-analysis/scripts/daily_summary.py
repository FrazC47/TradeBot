#!/usr/bin/env python3
"""
Daily Summary Report Generator
Creates a summary of all trading activity for the day
"""

from datetime import datetime
from pathlib import Path

LOGS_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/logs')

def main():
    print(f"Daily Summary Report - {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 80)
    
    # Check for setup logs
    setups_log = LOGS_DIR / 'setups.log'
    if setups_log.exists():
        print("\nTrade Setups Found Today:")
        print("-" * 80)
        # Count setups in log
        with open(setups_log, 'r') as f:
            content = f.read()
            if '🎯' in content:
                setups = content.count('🎯')
                print(f"Total setups: {setups}")
            else:
                print("No setups found today")
    
    # Check fetcher activity
    fetcher_log = LOGS_DIR / 'fetcher.log'
    if fetcher_log.exists():
        print("\nData Fetcher Activity:")
        print("-" * 80)
        with open(fetcher_log, 'r') as f:
            content = f.read()
            fetches = content.count('🔄 FETCHING')
            skips = content.count('⏭️  SKIPPED')
            print(f"Fetches: {fetches} | Skips: {fetches}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
