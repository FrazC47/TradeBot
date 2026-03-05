#!/usr/bin/env python3
"""
Futures OHLCV Fetcher with Spot-Futures Divergence Detection
Fetches futures candles and compares to spot for early warning signals
"""

import requests
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Configuration
DATA_DIR = Path('/root/.openclaw/workspace/data/binance_futures_ohlcv')
SPOT_DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
DIVERGENCE_DIR = Path('/root/.openclaw/workspace/data/divergence_alerts')

SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
TIMEFRAMES = ['1h', '4h']  # Most useful for divergence detection

# Binance Futures API
FUTURES_BASE_URL = 'https://fapi.binance.com'

def fetch_futures_ohlcv(symbol: str, interval: str, limit: int = 500) -> List[Dict]:
    """Fetch futures OHLCV data from Binance"""
    url = f"{FUTURES_BASE_URL}/fapi/v1/klines"
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        processed = []
        for k in data:
            processed.append({
                'open_time': int(k[0]),
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5]),
                'close_time': int(k[6]),
                'quote_volume': float(k[7]),
                'trades': int(k[8]),
                'taker_buy_base': float(k[9]),
                'taker_buy_quote': float(k[10])
            })
        return processed
    except Exception as e:
        print(f"Error fetching futures OHLCV for {symbol} {interval}: {e}")
        return []

def load_spot_ohlcv(symbol: str, interval: str) -> List[Dict]:
    """Load spot OHLCV data from local CSV"""
    filepath = SPOT_DATA_DIR / symbol / f"{interval}.csv"
    
    if not filepath.exists():
        return []
    
    data = []
    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append({
                    'open_time': int(row['open_time']),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume'])
                })
    except Exception as e:
        print(f"Error loading spot data for {symbol} {interval}: {e}")
    
    return data

def calculate_divergence(spot_data: List[Dict], futures_data: List[Dict]) -> List[Dict]:
    """Calculate spot-futures divergence for matching timestamps"""
    # Create lookup by timestamp
    spot_by_time = {d['open_time']: d for d in spot_data}
    futures_by_time = {d['open_time']: d for d in futures_data}
    
    divergences = []
    
    # Find common timestamps
    common_times = set(spot_by_time.keys()) & set(futures_by_time.keys())
    
    for timestamp in sorted(common_times):
        spot = spot_by_time[timestamp]
        futures = futures_by_time[timestamp]
        
        # Calculate price divergence
        price_diff = futures['close'] - spot['close']
        price_diff_pct = (price_diff / spot['close']) * 100
        
        # Calculate volume divergence
        volume_diff_pct = 0
        if spot['volume'] > 0:
            volume_diff_pct = ((futures['volume'] - spot['volume']) / spot['volume']) * 100
        
        divergences.append({
            'timestamp': timestamp,
            'datetime': datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M'),
            'spot_close': spot['close'],
            'futures_close': futures['close'],
            'price_diff': round(price_diff, 2),
            'price_diff_pct': round(price_diff_pct, 4),
            'spot_volume': spot['volume'],
            'futures_volume': futures['volume'],
            'volume_diff_pct': round(volume_diff_pct, 2)
        })
    
    return divergences

def detect_divergence_signals(divergences: List[Dict], symbol: str, interval: str) -> List[Dict]:
    """Detect significant divergence signals"""
    if not divergences:
        return []
    
    signals = []
    
    # Get latest divergence
    latest = divergences[-1]
    
    # Price divergence thresholds
    PRICE_THRESHOLD = 0.1  # 0.1% difference is notable
    VOLUME_THRESHOLD = 50  # 50% volume difference is notable
    
    # Check for significant price divergence
    if abs(latest['price_diff_pct']) > PRICE_THRESHOLD:
        direction = "FUTURES_PREMIUM" if latest['price_diff_pct'] > 0 else "FUTURES_DISCOUNT"
        
        signal = {
            'timestamp': latest['timestamp'],
            'datetime': latest['datetime'],
            'symbol': symbol,
            'interval': interval,
            'type': direction,
            'price_diff_pct': latest['price_diff_pct'],
            'spot_price': latest['spot_close'],
            'futures_price': latest['futures_close'],
            'severity': 'HIGH' if abs(latest['price_diff_pct']) > 0.5 else 'MEDIUM',
            'interpretation': ''
        }
        
        if direction == "FUTURES_PREMIUM":
            signal['interpretation'] = "Leverage longs paying premium. Risk of long squeeze if price drops."
        else:
            signal['interpretation'] = "Leverage shorts dominant. Risk of short squeeze if price rises."
        
        signals.append(signal)
    
    # Check for significant volume divergence
    if abs(latest['volume_diff_pct']) > VOLUME_THRESHOLD:
        direction = "FUTURES_VOLUME_HIGH" if latest['volume_diff_pct'] > 0 else "SPOT_VOLUME_HIGH"
        
        signals.append({
            'timestamp': latest['timestamp'],
            'datetime': latest['datetime'],
            'symbol': symbol,
            'interval': interval,
            'type': direction,
            'volume_diff_pct': latest['volume_diff_pct'],
            'severity': 'HIGH' if abs(latest['volume_diff_pct']) > 100 else 'MEDIUM',
            'interpretation': "Speculation driving futures volume" if direction == "FUTURES_VOLUME_HIGH" else "Real spot buying/selling dominant"
        })
    
    return signals

def save_futures_ohlcv(symbol: str, interval: str, data: List[Dict]):
    """Save futures OHLCV data to CSV"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing data
    existing = {}
    if filepath.exists():
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[int(row['open_time'])] = row
    
    # Merge new data
    for d in data:
        existing[d['open_time']] = d
    
    # Write merged data
    fieldnames = ['open_time', 'open', 'high', 'low', 'close', 'volume', 
                  'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote']
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for timestamp in sorted(existing.keys()):
            writer.writerow(existing[timestamp])
    
    print(f"  Saved {len(data)} candles to {filepath}")

def save_divergence_data(symbol: str, interval: str, divergences: List[Dict]):
    """Save divergence analysis to CSV"""
    DIVERGENCE_DIR.mkdir(parents=True, exist_ok=True)
    filepath = DIVERGENCE_DIR / f"{symbol}_{interval}_divergence.csv"
    
    fieldnames = ['timestamp', 'datetime', 'spot_close', 'futures_close', 
                  'price_diff', 'price_diff_pct', 'spot_volume', 'futures_volume', 'volume_diff_pct']
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(divergences)
    
    print(f"  Saved divergence data to {filepath}")

def save_divergence_signals(signals: List[Dict]):
    """Save divergence signals to JSON for alerting"""
    DIVERGENCE_DIR.mkdir(parents=True, exist_ok=True)
    filepath = DIVERGENCE_DIR / 'latest_signals.json'
    
    with open(filepath, 'w') as f:
        json.dump(signals, f, indent=2)
    
    if signals:
        print(f"  ⚠️  {len(signals)} divergence signals detected!")
        for sig in signals:
            print(f"     {sig['symbol']} {sig['interval']}: {sig['type']} ({sig['severity']})")
            print(f"     → {sig['interpretation']}")
    else:
        print(f"  ✓ No significant divergence signals")

def run_divergence_analysis():
    """Main function to fetch futures OHLCV and detect divergence"""
    print("="*70)
    print("FUTURES OHLCV FETCHER & DIVERGENCE DETECTOR")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    all_signals = []
    
    for symbol in SYMBOLS:
        print(f"\n{symbol}:")
        print("-" * 40)
        
        for interval in TIMEFRAMES:
            print(f"\n  {interval}:")
            
            # Fetch futures OHLCV
            futures_data = fetch_futures_ohlcv(symbol, interval)
            if not futures_data:
                print(f"    ✗ Failed to fetch futures data")
                continue
            
            # Save futures data
            save_futures_ohlcv(symbol, interval, futures_data)
            
            # Load spot data
            spot_data = load_spot_ohlcv(symbol, interval)
            if not spot_data:
                print(f"    ✗ No spot data available")
                continue
            
            # Calculate divergence
            divergences = calculate_divergence(spot_data, futures_data)
            if divergences:
                save_divergence_data(symbol, interval, divergences)
                
                # Show latest divergence
                latest = divergences[-1]
                print(f"    Latest: {latest['datetime']}")
                print(f"    Spot: ${latest['spot_close']:,.2f} | Futures: ${latest['futures_close']:,.2f}")
                print(f"    Diff: {latest['price_diff_pct']:+.4f}% | Vol diff: {latest['volume_diff_pct']:+.1f}%")
                
                # Detect signals
                signals = detect_divergence_signals(divergences, symbol, interval)
                all_signals.extend(signals)
            else:
                print(f"    ✗ No matching timestamps for divergence calculation")
    
    # Save all signals
    print(f"\n{'='*70}")
    print("DIVERGENCE SIGNAL SUMMARY")
    print("="*70)
    save_divergence_signals(all_signals)
    
    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    return all_signals

if __name__ == '__main__':
    run_divergence_analysis()
