#!/usr/bin/env python3
"""
Binance Kline Data Fetcher - Lightweight Version
No pandas dependency, uses standard library only
"""

import requests
import json
import csv
import os
import time
from datetime import datetime
from pathlib import Path

# Configuration
SYMBOLS = os.getenv('BINANCE_SYMBOLS', 'BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,XRPUSDT').split(',')
INTERVALS = os.getenv('BINANCE_INTERVALS', '5m,15m,1h,4h,1d,1w,1M').split(',')
DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
BASE_URL = 'https://api.binance.com/api/v3/klines'

def fetch_klines(symbol, interval, limit=500):
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
        return []

def process_klines(klines):
    """Process raw kline data into structured format"""
    processed = []
    for k in klines:
        processed.append({
            'open_time': k[0],
            'open': float(k[1]),
            'high': float(k[2]),
            'low': float(k[3]),
            'close': float(k[4]),
            'volume': float(k[5]),
            'close_time': k[6],
            'quote_volume': float(k[7]),
            'trades': int(k[8]),
            'taker_buy_base': float(k[9]),
            'taker_buy_quote': float(k[10])
        })
    return processed

def calculate_stats(data):
    """Calculate rolling statistics"""
    if len(data) < 20:
        return data
    
    # Calculate 20-period rolling averages
    for i in range(len(data)):
        if i >= 19:
            window = data[i-19:i+1]
            volumes = [d['volume'] for d in window]
            closes = [d['close'] for d in window]
            
            data[i]['volume_avg_20'] = sum(volumes) / len(volumes)
            
            # Volatility (std dev of price changes)
            if len(closes) > 1:
                changes = [(closes[j] - closes[j-1]) / closes[j-1] * 100 
                          for j in range(1, len(closes))]
                mean_change = sum(changes) / len(changes)
                variance = sum((c - mean_change) ** 2 for c in changes) / len(changes)
                data[i]['price_volatility_20'] = variance ** 0.5
            else:
                data[i]['price_volatility_20'] = 0
        else:
            data[i]['volume_avg_20'] = data[i]['volume']
            data[i]['price_volatility_20'] = 0
        
        # Price change percentage
        if i > 0:
            prev_close = data[i-1]['close']
            data[i]['price_change_pct'] = (data[i]['close'] - prev_close) / prev_close * 100
        else:
            data[i]['price_change_pct'] = 0
        
        # Price range
        data[i]['price_range'] = data[i]['high'] - data[i]['low']
        data[i]['price_range_pct'] = (data[i]['price_range'] / data[i]['open']) * 100 if data[i]['open'] else 0
    
    return data

def validate_data(data, symbol, interval):
    """Validate data integrity before saving"""
    errors = []
    warnings = []
    
    if not data:
        errors.append("No data to validate")
        return False, errors, warnings
    
    # Check price consistency (high >= low, high >= close >= low, etc.)
    for i, row in enumerate(data):
        if row['high'] < row['low']:
            errors.append(f"Row {i}: high ({row['high']}) < low ({row['low']})")
        
        if row['high'] < row['close']:
            errors.append(f"Row {i}: high ({row['high']}) < close ({row['close']})")
        
        if row['high'] < row['open']:
            errors.append(f"Row {i}: high ({row['high']}) < open ({row['open']})")
        
        if row['low'] > row['close']:
            errors.append(f"Row {i}: low ({row['low']}) > close ({row['close']})")
        
        if row['low'] > row['open']:
            errors.append(f"Row {i}: low ({row['low']}) > open ({row['open']})")
        
        if row['volume'] < 0:
            errors.append(f"Row {i}: negative volume ({row['volume']})")
        
        if row['trades'] < 0:
            errors.append(f"Row {i}: negative trades ({row['trades']})")
        
        # Price range sanity check (alert if > 50% move in one candle)
        price_range_pct = ((row['high'] - row['low']) / row['low'] * 100) if row['low'] > 0 else 0
        if price_range_pct > 50:
            warnings.append(f"Row {i}: unusually large price range ({price_range_pct:.1f}%)")
    
    # Check timestamp sequence (should be ascending)
    for i in range(1, len(data)):
        if data[i]['open_time'] <= data[i-1]['open_time']:
            errors.append(f"Timestamp out of order at row {i}")
    
    return len(errors) == 0, errors, warnings


def verify_csv_integrity(filepath, symbol, interval):
    """Verify CSV file has consistent column structure"""
    errors = []
    warnings = []
    
    if not filepath.exists():
        return True, errors, warnings, 0
    
    with open(filepath, 'r', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    if len(rows) < 2:
        return True, errors, warnings, len(rows) - 1  # Just header or empty
    
    header = rows[0]
    header_cols = len(header)
    inconsistent_rows = []
    
    for i, row in enumerate(rows[1:], 1):
        if len(row) != header_cols:
            inconsistent_rows.append((i, len(row)))
    
    if inconsistent_rows:
        errors.append(f"Found {len(inconsistent_rows)} rows with wrong column count (expected {header_cols})")
        errors.append(f"First inconsistent row: {inconsistent_rows[0]}")
    
    # Verify latest row has reasonable values
    latest = rows[-1]
    try:
        close_idx = header.index('close') if 'close' in header else 4
        close_val = float(latest[close_idx])
        
        # Sanity check on price (BTC should be between $1,000 and $1,000,000)
        if symbol == 'BTCUSDT' and (close_val < 1000 or close_val > 1000000):
            errors.append(f"Latest close price (${close_val:,.2f}) seems unreasonable for BTC")
        if symbol == 'ETHUSDT' and (close_val < 100 or close_val > 50000):
            errors.append(f"Latest close price (${close_val:,.2f}) seems unreasonable for ETH")
        if symbol == 'BNBUSDT' and (close_val < 10 or close_val > 10000):
            errors.append(f"Latest close price (${close_val:,.2f}) seems unreasonable for BNB")
            
    except (ValueError, IndexError) as e:
        errors.append(f"Could not parse latest close price: {e}")
    
    return len(errors) == 0, errors, warnings, len(rows) - 1


def reconcile_data(symbol, interval):
    """Remove corrupted rows and return count of valid rows kept"""
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    
    if not filepath.exists():
        return 0
    
    with open(filepath, 'r', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    if len(rows) < 2:
        return len(rows) - 1
    
    header = rows[0]
    header_cols = len(header)
    
    # Keep only rows that match header column count
    good_rows = [header]
    removed_count = 0
    
    for row in rows[1:]:
        if len(row) == header_cols:
            good_rows.append(row)
        else:
            removed_count += 1
    
    if removed_count > 0:
        # Backup corrupted file
        backup_path = filepath.with_suffix('.csv.corrupted')
        filepath.rename(backup_path)
        
        # Write clean data
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(good_rows)
        
        print(f"  RECONCILED: Removed {removed_count} corrupted rows, kept {len(good_rows)-1} valid rows")
    
    return len(good_rows) - 1


def save_to_csv(symbol, interval, data):
    """Save data to CSV file with validation"""
    symbol_dir = DATA_DIR / symbol
    symbol_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = symbol_dir / f"{interval}.csv"
    
    # Validate new data before saving
    is_valid, errors, warnings = validate_data(data, symbol, interval)
    
    if errors:
        print(f"  VALIDATION ERRORS in fetched data:")
        for err in errors[:5]:  # Show first 5 errors
            print(f"    - {err}")
        if len(errors) > 5:
            print(f"    ... and {len(errors) - 5} more errors")
        print(f"  Aborting save for {symbol} {interval}")
        return 0
    
    if warnings:
        print(f"  Validation warnings:")
        for warn in warnings[:3]:
            print(f"    - {warn}")
    
    # Verify existing CSV integrity before appending
    if filepath.exists():
        is_integrity_ok, integrity_errors, integrity_warnings, existing_count = verify_csv_integrity(filepath, symbol, interval)
        
        if not is_integrity_ok:
            print(f"  CSV INTEGRITY ERRORS detected:")
            for err in integrity_errors:
                print(f"    - {err}")
            print(f"  Running reconciliation...")
            reconcile_data(symbol, interval)
    
    # Check for existing data
    existing_timestamps = set()
    if filepath.exists():
        with open(filepath, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    existing_timestamps.add(int(row['open_time']))
                except (ValueError, KeyError):
                    continue  # Skip malformed rows
    
    # Filter out duplicates
    new_data = [d for d in data if d['open_time'] not in existing_timestamps]
    
    if not new_data:
        print(f"No new data for {symbol} {interval}")
        return 0
    
    # Write data
    fieldnames = ['open_time', 'open', 'high', 'low', 'close', 'volume',
                  'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote',
                  'close_time', 'volume_avg_20', 'price_volatility_20',
                  'price_change_pct', 'price_range', 'price_range_pct']
    
    file_exists = filepath.exists()
    with open(filepath, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_data)
    
    # Verify what we just saved
    final_count = 0
    try:
        with open(filepath, 'r', newline='') as f:
            reader = csv.DictReader(f)
            final_rows = list(reader)
            final_count = len(final_rows)
            
            # Quick sanity check on latest saved value
            if final_rows:
                latest = final_rows[-1]
                expected_close = float(new_data[-1]['close'])
                actual_close = float(latest['close'])
                if abs(expected_close - actual_close) > 0.01:
                    print(f"  WARNING: Saved close (${actual_close:,.2f}) doesn't match expected (${expected_close:,.2f})")
    except Exception as e:
        print(f"  WARNING: Could not verify saved data: {e}")
    
    return len(new_data)

def main():
    """Main execution"""
    print(f"Starting Binance Kline Monitor at {datetime.now()}")
    print(f"Symbols: {SYMBOLS}")
    print(f"Intervals: {INTERVALS}")
    
    total_records = 0
    
    for symbol in SYMBOLS:
        symbol = symbol.strip().upper()
        for interval in INTERVALS:
            interval = interval.strip()
            
            print(f"\nFetching {symbol} {interval}...")
            
            # Fetch data
            klines = fetch_klines(symbol, interval)
            if not klines:
                continue
            
            # Process
            data = process_klines(klines)
            data = calculate_stats(data)
            
            # Save
            saved = save_to_csv(symbol, interval, data)
            total_records += saved
            
            print(f"  Saved {saved} new records")
            
            # Rate limiting
            time.sleep(0.1)
    
    print(f"\nTotal records saved: {total_records}")
    print(f"Data directory: {DATA_DIR}")
    
    # Generate summary with validation
    print("\n=== Summary with Validation ===")
    summary = []
    validation_issues = []
    
    for symbol in SYMBOLS:
        symbol = symbol.strip().upper()
        for interval in INTERVALS:
            interval = interval.strip()
            filepath = DATA_DIR / symbol / f"{interval}.csv"
            
            # Verify integrity before generating summary
            is_valid, errors, warnings, row_count = verify_csv_integrity(filepath, symbol, interval)
            
            if not is_valid:
                validation_issues.append(f"{symbol} {interval}: {len(errors)} integrity errors")
                print(f"⚠️  {symbol} {interval}: Integrity issues detected, reconciling...")
                reconcile_data(symbol, interval)
                # Re-check after reconciliation
                is_valid, errors, warnings, row_count = verify_csv_integrity(filepath, symbol, interval)
            
            if filepath.exists():
                try:
                    with open(filepath, 'r') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                        if rows:
                            latest = rows[-1]
                            close_val = float(latest['close'])
                            volume_val = float(latest['volume'])
                            
                            # Final sanity check
                            status_icon = "✅" if is_valid else "⚠️"
                            print(f"{status_icon} {symbol} {interval}: {len(rows)} records, close=${close_val:,.2f}, vol={volume_val:,.2f}")
                            
                            summary.append({
                                'symbol': symbol,
                                'interval': interval,
                                'records': len(rows),
                                'latest_close': close_val,
                                'latest_volume': volume_val,
                                'valid': is_valid
                            })
                except Exception as e:
                    print(f"❌ {symbol} {interval}: Error reading summary - {e}")
                    validation_issues.append(f"{symbol} {interval}: Read error - {e}")
    
    if validation_issues:
        print("\n=== Validation Issues ===")
        for issue in validation_issues:
            print(f"  - {issue}")
    
    print(f"\n=== Data Integrity Status ===")
    print(f"Total symbols/intervals: {len(summary)}")
    print(f"Valid: {sum(1 for s in summary if s['valid'])}")
    print(f"With issues: {sum(1 for s in summary if not s['valid'])}")

if __name__ == '__main__':
    main()
