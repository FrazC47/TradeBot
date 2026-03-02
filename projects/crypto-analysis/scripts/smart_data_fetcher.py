#!/usr/bin/env python3
"""
Smart Data Fetcher - Only pulls timeframes when new candles are available
Uses candle timestamps to determine if update is needed
"""

import requests
import csv
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
STATE_FILE = Path('/root/.openclaw/workspace/data/fetcher_state.json')
BASE_URL = 'https://api.binance.com/api/v3/klines'

# Configuration
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']

# Timeframe intervals in milliseconds
TIMEFRAME_INTERVALS = {
    '5m': 5 * 60 * 1000,
    '15m': 15 * 60 * 1000,
    '1h': 60 * 60 * 1000,
    '4h': 4 * 60 * 60 * 1000,
    '1d': 24 * 60 * 60 * 1000,
    '1w': 7 * 24 * 60 * 60 * 1000,
    '1M': 30 * 24 * 60 * 60 * 1000
}

def load_state():
    """Load last fetch timestamps"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    """Save last fetch timestamps"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_last_candle_time(symbol, interval):
    """Get the timestamp of the last candle in the CSV file"""
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    if not filepath.exists():
        return 0
    
    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if rows:
                return int(rows[-1]['open_time'])
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return 0

def should_fetch(symbol, interval, state):
    """Determine if we should fetch new data for this timeframe"""
    last_candle = get_last_candle_time(symbol, interval)
    interval_ms = TIMEFRAME_INTERVALS[interval]
    
    # Get current time in milliseconds
    current_time_ms = int(time.time() * 1000)
    
    # Calculate when the next candle should start
    if last_candle == 0:
        return True, "No existing data"
    
    next_candle_time = last_candle + interval_ms
    
    # Check if enough time has passed for a new candle
    if current_time_ms >= next_candle_time:
        time_since_last = (current_time_ms - last_candle) / 1000
        return True, f"Last candle {time_since_last:.0f}s ago, new candle available"
    else:
        time_until_next = (next_candle_time - current_time_ms) / 1000
        return False, f"Next candle in {time_until_next:.0f}s"

def fetch_klines(symbol, interval, limit=100):
    """Fetch kline data from Binance API"""
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {symbol} {interval}: {e}")
        return None

def update_csv(symbol, interval, new_data):
    """Update CSV file with new data, avoiding duplicates"""
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Standard Binance columns
    standard_columns = [
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
        'taker_buy_quote_volume', 'ignore'
    ]
    
    # Load existing data
    existing_data = {}
    existing_columns = standard_columns
    
    if filepath.exists():
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                existing_columns = reader.fieldnames or standard_columns
                for row in reader:
                    existing_data[int(row['open_time'])] = row
        except Exception as e:
            print(f"Error reading existing data: {e}")
    
    # Add new data (only standard columns)
    for candle in new_data:
        timestamp = int(candle[0])
        existing_data[timestamp] = {
            'open_time': candle[0],
            'open': candle[1],
            'high': candle[2],
            'low': candle[3],
            'close': candle[4],
            'volume': candle[5],
            'close_time': candle[6],
            'quote_volume': candle[7],
            'trades': candle[8],
            'taker_buy_volume': candle[9],
            'taker_buy_quote_volume': candle[10],
            'ignore': candle[11]
        }
    
    # Write updated data with standard columns only
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=standard_columns)
        writer.writeheader()
        for ts in sorted(existing_data.keys()):
            row = {k: existing_data[ts].get(k, '') for k in standard_columns}
            writer.writerow(row)
    
    return len(new_data)

def main():
    print("=" * 80)
    print("SMART DATA FETCHER")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    state = load_state()
    current_time = int(time.time() * 1000)
    
    total_fetches = 0
    total_candles = 0
    
    for symbol in SYMBOLS:
        print(f"\n{symbol}:")
        print("-" * 80)
        
        for interval in TIMEFRAME_INTERVALS.keys():
            should_update, reason = should_fetch(symbol, interval, state)
            
            if should_update:
                print(f"  {interval:3s}: 🔄 FETCHING - {reason}")
                
                # Fetch data
                data = fetch_klines(symbol, interval, limit=100)
                
                if data:
                    # Update CSV
                    new_candles = update_csv(symbol, interval, data)
                    print(f"       ✅ Updated with {new_candles} candles")
                    total_fetches += 1
                    total_candles += new_candles
                    
                    # Update state
                    key = f"{symbol}_{interval}"
                    state[key] = {
                        'last_fetch': current_time,
                        'last_candle': int(data[-1][0])
                    }
                else:
                    print(f"       ❌ Fetch failed")
            else:
                print(f"  {interval:3s}: ⏭️  SKIPPED - {reason}")
    
    # Save state
    save_state(state)
    
    print()
    print("=" * 80)
    print(f"SUMMARY: {total_fetches} fetches, {total_candles} candles added")
    print("=" * 80)

if __name__ == "__main__":
    main()
