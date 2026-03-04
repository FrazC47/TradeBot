#!/usr/bin/env python3
"""
ETHUSDT Dynamic Data Puller
Switches between 5m (normal) and 1m (setup active) based on agent state
Saves API calls while providing granular data when needed
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict
import sys

# Configuration
DYNAMIC_CONFIG = {
    'symbol': 'ETHUSDT',
    'normal_interval': '5m',
    'granular_interval': '1m',
    
    # Paths
    'state_file': '/root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/state/agent_state.json',
    'data_dir': '/root/.openclaw/workspace/data/binance/ETHUSDT',
    'log_file': '/root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/dynamic_puller.log',
    
    # Timing
    'setup_max_age_minutes': 30,  # How long to stay in granular mode after setup
    'granular_cooldown_minutes': 5,  # Min time between 1m pulls
}

class DynamicDataPuller:
    """
    Dynamically switches data pull frequency based on setup status
    """
    
    def __init__(self):
        self.config = DYNAMIC_CONFIG
        self.setup_logging()
        
    def setup_logging(self):
        """Setup simple logging"""
        self.log_file = Path(self.config['log_file'])
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
    def log(self, message: str):
        """Log message"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] {message}\n"
        with open(self.log_file, 'a') as f:
            f.write(log_line)
        print(log_line.strip())
        
    def load_agent_state(self) -> Dict:
        """Load current agent state"""
        state_file = Path(self.config['state_file'])
        if state_file.exists():
            with open(state_file, 'r') as f:
                return json.load(f)
        return {
            'active_setup': None,
            'last_setup_time': None,
        }
    
    def is_setup_active(self, state: Dict) -> bool:
        """
        Check if there's an active setup that needs granular data
        """
        # Check if granular mode is explicitly activated by agent
        if state.get('granular_mode_active'):
            activated_at = state.get('granular_mode_activated_at')
            if activated_at:
                activated_dt = datetime.fromisoformat(activated_at)
                age_minutes = (datetime.now() - activated_dt).total_seconds() / 60
                
                # Stay granular for 30 minutes after activation
                if age_minutes < self.config['setup_max_age_minutes']:
                    return True
                else:
                    # Granular mode expired
                    return False
        
        # Fallback: Check if agent has identified a setup
        if state.get('active_setup'):
            setup = state['active_setup']
            setup_time = setup.get('timestamp')
            
            if setup_time:
                setup_dt = datetime.fromisoformat(setup_time)
                age_minutes = (datetime.now() - setup_dt).total_seconds() / 60
                
                # Stay granular for 30 minutes after setup identified
                if age_minutes < self.config['setup_max_age_minutes']:
                    return True
                    
        return False
    
    def pull_data(self, interval: str):
        """
        Pull specific interval data using smart fetcher logic
        """
        self.log(f"Pulling {interval} data for {self.config['symbol']}")
        
        # Use the existing smart data fetcher but for specific interval
        # This is a simplified version - in production would call actual fetcher
        
        import csv
        import requests
        import time
        
        # Binance API endpoint
        url = "https://api.binance.com/api/v3/klines"
        
        params = {
            'symbol': self.config['symbol'],
            'interval': interval,
            'limit': 100
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            # Save to CSV
            output_file = Path(self.config['data_dir']) / f"{interval}.csv"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists to determine mode
            file_exists = output_file.exists()
            
            with open(output_file, 'a' if file_exists else 'w', newline='') as f:
                writer = csv.writer(f)
                
                if not file_exists:
                    # Write header
                    writer.writerow([
                        'open_time', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
                        'taker_buy_quote_volume', 'ignore'
                    ])
                
                # Write data
                for candle in data:
                    writer.writerow(candle)
            
            self.log(f"✅ Successfully pulled {len(data)} {interval} candles")
            return True
            
        except Exception as e:
            self.log(f"❌ Error pulling {interval} data: {e}")
            return False
    
    def run(self):
        """Main execution - decide which interval to pull"""
        self.log("="*60)
        self.log("DYNAMIC DATA PULLER STARTING")
        self.log("="*60)
        
        # Load agent state
        state = self.load_agent_state()
        
        # Determine mode
        if self.is_setup_active(state):
            mode = 'GRANULAR'
            interval = self.config['granular_interval']  # 1m
        else:
            mode = 'NORMAL'
            interval = self.config['normal_interval']  # 5m
        
        self.log(f"Mode: {mode} (pulling {interval} data)")
        
        # Pull data
        success = self.pull_data(interval)
        
        # Log completion
        self.log("="*60)
        if success:
            self.log(f"✅ {mode} mode complete - {interval} data updated")
        else:
            self.log(f"⚠️ {mode} mode failed - will retry next cycle")
        self.log("="*60)

if __name__ == '__main__':
    puller = DynamicDataPuller()
    puller.run()
