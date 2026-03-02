#!/usr/bin/env python3
"""
Futures Data Fetcher - Pulls Open Interest and Funding Rate from Binance Futures API
"""

import requests
import csv
import json
import time
from datetime import datetime
from pathlib import Path

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
FUTURES_DATA_DIR = Path('/root/.openclaw/workspace/data/futures')
STATE_FILE = Path('/root/.openclaw/workspace/data/futures_fetcher_state.json')

# Binance Futures API endpoints
FUTURES_BASE_URL = 'https://fapi.binance.com/fapi/v1'
FUTURES_DATA_URL = 'https://fapi.binance.com/futures/data'

SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']

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

def fetch_open_interest(symbol, period='1h', limit=500):
    """
    Fetch Open Interest history from Binance Futures API
    period: 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d
    """
    url = f"{FUTURES_DATA_URL}/openInterestHist"
    params = {
        'symbol': symbol,
        'period': period,
        'limit': limit
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  Error fetching OI for {symbol}: {e}")
        return None

def fetch_funding_rate(symbol, limit=500):
    """
    Fetch Funding Rate history from Binance Futures API
    """
    url = f"{FUTURES_BASE_URL}/fundingRate"
    params = {
        'symbol': symbol,
        'limit': limit
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  Error fetching funding rate for {symbol}: {e}")
        return None

def save_open_interest_csv(symbol, data):
    """Save Open Interest data to CSV"""
    filepath = FUTURES_DATA_DIR / f"{symbol}_open_interest.csv"
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    columns = ['timestamp', 'open_interest', 'sum_open_interest_value']
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in data:
            writer.writerow({
                'timestamp': row['timestamp'],
                'open_interest': row['sumOpenInterest'],
                'sum_open_interest_value': row['sumOpenInterestValue']
            })
    
    return len(data)

def save_funding_rate_csv(symbol, data):
    """Save Funding Rate data to CSV"""
    filepath = FUTURES_DATA_DIR / f"{symbol}_funding_rate.csv"
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    columns = ['funding_time', 'funding_rate', 'mark_price']
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in data:
            writer.writerow({
                'funding_time': row['fundingTime'],
                'funding_rate': row['fundingRate'],
                'mark_price': row.get('markPrice', '')
            })
    
    return len(data)

def get_latest_open_interest(symbol):
    """Get latest Open Interest value for a symbol"""
    data = fetch_open_interest(symbol, period='1h', limit=1)
    if data and len(data) > 0:
        return {
            'open_interest': float(data[0]['sumOpenInterest']),
            'open_interest_value': float(data[0]['sumOpenInterestValue']),
            'timestamp': data[0]['timestamp']
        }
    return None

def get_latest_funding_rate(symbol):
    """Get latest Funding Rate for a symbol"""
    url = f"{FUTURES_BASE_URL}/premiumIndex"
    params = {'symbol': symbol}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return {
            'funding_rate': float(data['lastFundingRate']),
            'next_funding_time': data['nextFundingTime'],
            'mark_price': float(data['markPrice']),
            'index_price': float(data['indexPrice']),
            'estimated_settle_price': float(data['estimatedSettlePrice'])
        }
    except Exception as e:
        print(f"  Error fetching latest funding for {symbol}: {e}")
        return None

def main():
    print("=" * 80)
    print("BINANCE FUTURES DATA FETCHER")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    state = load_state()
    current_time = int(time.time() * 1000)
    
    # Store latest values for indicator calculator
    latest_data = {}
    
    for symbol in SYMBOLS:
        print(f"\n{symbol}:")
        print("-" * 80)
        
        # Fetch Open Interest history
        print(f"  Fetching Open Interest history...")
        oi_data = fetch_open_interest(symbol, period='1h', limit=500)
        if oi_data:
            count = save_open_interest_csv(symbol, oi_data)
            print(f"    ✅ Saved {count} OI records")
        
        # Fetch Funding Rate history
        print(f"  Fetching Funding Rate history...")
        funding_data = fetch_funding_rate(symbol, limit=500)
        if funding_data:
            count = save_funding_rate_csv(symbol, funding_data)
            print(f"    ✅ Saved {count} funding rate records")
        
        # Get latest values
        print(f"  Fetching latest values...")
        latest_oi = get_latest_open_interest(symbol)
        latest_funding = get_latest_funding_rate(symbol)
        
        if latest_oi and latest_funding:
            latest_data[symbol] = {
                'open_interest': latest_oi['open_interest'],
                'open_interest_value': latest_oi['open_interest_value'],
                'funding_rate': latest_funding['funding_rate'],
                'mark_price': latest_funding['mark_price'],
                'index_price': latest_funding['index_price'],
                'timestamp': current_time
            }
            print(f"    ✅ OI: {latest_oi['open_interest']:,.0f} | Funding: {latest_funding['funding_rate']:.4%}")
        
        # Rate limiting
        time.sleep(0.5)
    
    # Save latest data for indicator calculator
    latest_file = FUTURES_DATA_DIR / 'latest_futures_data.json'
    with open(latest_file, 'w') as f:
        json.dump(latest_data, f, indent=2)
    print(f"\n  Saved latest futures data to: {latest_file}")
    
    # Update state
    state['last_fetch'] = current_time
    save_state(state)
    
    print()
    print("=" * 80)
    print("FUTURES DATA FETCH COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
