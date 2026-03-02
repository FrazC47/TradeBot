#!/usr/bin/env python3
"""
COMPASS Futures Data Fetcher
Extends binance_kline_simple.py with futures-specific data:
- Open Interest (OI)
- Funding Rate
- Long/Short Ratio
- Taker Buy/Sell Volume
"""

import requests
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
import time

# Configuration
DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
FUTURES_DATA_DIR = Path('/root/.openclaw/workspace/data/binance_futures')
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
TIMEFRAMES = ['15m', '1h', '4h', '1d']

# Binance Futures API endpoints
BASE_URL = 'https://fapi.binance.com'

def fetch_open_interest(symbol, period='1h', limit=500):
    """Fetch open interest history"""
    url = f"{BASE_URL}/futures/data/openInterestHist"
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
        print(f"Error fetching OI for {symbol}: {e}")
        return []

def fetch_funding_rate(symbol, limit=100):
    """Fetch funding rate history"""
    url = f"{BASE_URL}/fapi/v1/fundingRate"
    params = {
        'symbol': symbol,
        'limit': limit
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching funding for {symbol}: {e}")
        return []

def fetch_long_short_ratio(symbol, period='1h', limit=500):
    """Fetch long/short account ratio"""
    url = f"{BASE_URL}/futures/data/globalLongShortAccountRatio"
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
        print(f"Error fetching L/S ratio for {symbol}: {e}")
        return []

def fetch_taker_volume(symbol, period='1h', limit=500):
    """Fetch taker buy/sell volume"""
    url = f"{BASE_URL}/futures/data/takerlongshortRatio"
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
        print(f"Error fetching taker volume for {symbol}: {e}")
        return []

def save_oi_data(symbol, data):
    """Save open interest data to CSV"""
    FUTURES_DATA_DIR.mkdir(parents=True, exist_ok=True)
    filepath = FUTURES_DATA_DIR / symbol / 'open_interest.csv'
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing data
    existing = {}
    if filepath.exists():
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[row['timestamp']] = row
    
    # Update with new data
    for item in data:
        ts = str(item.get('timestamp', ''))
        existing[ts] = {
            'timestamp': ts,
            'sumOpenInterest': item.get('sumOpenInterest', ''),
            'sumOpenInterestValue': item.get('sumOpenInterestValue', ''),
            'symbol': symbol
        }
    
    # Write back
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'sumOpenInterest', 'sumOpenInterestValue', 'symbol'])
        writer.writeheader()
        for ts in sorted(existing.keys()):
            writer.writerow(existing[ts])

def save_funding_data(symbol, data):
    """Save funding rate data to CSV"""
    filepath = FUTURES_DATA_DIR / symbol / 'funding_rate.csv'
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    existing = {}
    if filepath.exists():
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[row['fundingTime']] = row
    
    for item in data:
        ft = str(item.get('fundingTime', ''))
        existing[ft] = {
            'fundingTime': ft,
            'fundingRate': item.get('fundingRate', ''),
            'markPrice': item.get('markPrice', ''),
            'symbol': symbol
        }
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['fundingTime', 'fundingRate', 'markPrice', 'symbol'])
        writer.writeheader()
        for ft in sorted(existing.keys()):
            writer.writerow(existing[ft])

def save_ls_ratio(symbol, data):
    """Save long/short ratio data"""
    filepath = FUTURES_DATA_DIR / symbol / 'long_short_ratio.csv'
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    existing = {}
    if filepath.exists():
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[row['timestamp']] = row
    
    for item in data:
        ts = str(item.get('timestamp', ''))
        existing[ts] = {
            'timestamp': ts,
            'longAccount': item.get('longAccount', ''),
            'shortAccount': item.get('shortAccount', ''),
            'longShortRatio': item.get('longShortRatio', ''),
            'symbol': symbol
        }
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'longAccount', 'shortAccount', 'longShortRatio', 'symbol'])
        writer.writeheader()
        for ts in sorted(existing.keys()):
            writer.writerow(existing[ts])

def save_taker_volume(symbol, data):
    """Save taker volume data"""
    filepath = FUTURES_DATA_DIR / symbol / 'taker_volume.csv'
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    existing = {}
    if filepath.exists():
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[row['timestamp']] = row
    
    for item in data:
        ts = str(item.get('timestamp', ''))
        existing[ts] = {
            'timestamp': ts,
            'buyVol': item.get('buyVol', ''),
            'sellVol': item.get('sellVol', ''),
            'buySellRatio': item.get('buySellRatio', ''),
            'symbol': symbol
        }
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'buyVol', 'sellVol', 'buySellRatio', 'symbol'])
        writer.writeheader()
        for ts in sorted(existing.keys()):
            writer.writerow(existing[ts])

def fetch_all_futures_data():
    """Main function to fetch all futures data"""
    print("="*70)
    print("COMPASS Futures Data Fetcher")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    total_records = 0
    
    for symbol in SYMBOLS:
        print(f"\n{'='*70}")
        print(f"Fetching futures data for {symbol}")
        print('='*70)
        
        # Open Interest
        print(f"  Fetching Open Interest...", end=' ')
        oi_data = fetch_open_interest(symbol, period='1h', limit=100)
        if oi_data:
            save_oi_data(symbol, oi_data)
            print(f"✓ ({len(oi_data)} records)")
            total_records += len(oi_data)
        else:
            print("✗ failed")
        time.sleep(0.5)
        
        # Funding Rate
        print(f"  Fetching Funding Rate...", end=' ')
        funding_data = fetch_funding_rate(symbol, limit=100)
        if funding_data:
            save_funding_data(symbol, funding_data)
            print(f"✓ ({len(funding_data)} records)")
            total_records += len(funding_data)
        else:
            print("✗ failed")
        time.sleep(0.5)
        
        # Long/Short Ratio
        print(f"  Fetching Long/Short Ratio...", end=' ')
        ls_data = fetch_long_short_ratio(symbol, period='1h', limit=100)
        if ls_data:
            save_ls_ratio(symbol, ls_data)
            print(f"✓ ({len(ls_data)} records)")
            total_records += len(ls_data)
        else:
            print("✗ failed")
        time.sleep(0.5)
        
        # Taker Volume
        print(f"  Fetching Taker Volume...", end=' ')
        taker_data = fetch_taker_volume(symbol, period='1h', limit=100)
        if taker_data:
            save_taker_volume(symbol, taker_data)
            print(f"✓ ({len(taker_data)} records)")
            total_records += len(taker_data)
        else:
            print("✗ failed")
        time.sleep(0.5)
    
    print(f"\n{'='*70}")
    print(f"Total records saved: {total_records}")
    print(f"Data directory: {FUTURES_DATA_DIR}")
    print('='*70)
    
    return total_records

if __name__ == '__main__':
    fetch_all_futures_data()
