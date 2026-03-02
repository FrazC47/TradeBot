#!/usr/bin/env python3
"""
COMPASS Alert Check
Analyzes futures data for trading signals and alerts
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path

def get_workspace():
    """Get workspace path from environment or script location"""
    env_path = os.environ.get('COMPASS_WORKSPACE')
    if env_path:
        return Path(env_path)
    return Path(__file__).resolve().parent

WORKSPACE = get_workspace()
DATA_DIR = WORKSPACE / 'data' / 'binance_futures'
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']

def read_latest_data(symbol, filename):
    """Read the latest record from a CSV file"""
    filepath = DATA_DIR / symbol / filename
    if not filepath.exists():
        return None
    
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return rows[-1] if rows else None

def check_funding_alert(symbol):
    """Check for extreme funding rates"""
    data = read_latest_data(symbol, 'funding_rate.csv')
    if not data:
        return None
    
    funding_rate = float(data.get('fundingRate', 0))
    mark_price = float(data.get('markPrice', 0))
    
    # Funding rate thresholds
    if funding_rate > 0.0005:  # > 0.05%
        return {
            'type': 'FUNDING_HIGH',
            'symbol': symbol,
            'severity': 'WARNING' if funding_rate < 0.001 else 'CRITICAL',
            'message': f"High funding rate: {funding_rate:.6f} ({funding_rate*100:.4f}%)",
            'price': mark_price,
            'suggestion': 'Longs paying shorts - potential short squeeze or overheated market'
        }
    elif funding_rate < -0.0005:  # < -0.05%
        return {
            'type': 'FUNDING_LOW',
            'symbol': symbol,
            'severity': 'WARNING' if funding_rate > -0.001 else 'CRITICAL',
            'message': f"Negative funding rate: {funding_rate:.6f} ({funding_rate*100:.4f}%)",
            'price': mark_price,
            'suggestion': 'Shorts paying longs - potential long squeeze or bearish sentiment'
        }
    return None

def check_sentiment_alert(symbol):
    """Check for extreme long/short ratios"""
    data = read_latest_data(symbol, 'long_short_ratio.csv')
    if not data:
        return None
    
    long_pct = float(data.get('longAccount', 0))
    short_pct = float(data.get('shortAccount', 0))
    ratio = float(data.get('longShortRatio', 1))
    
    # Extreme sentiment thresholds
    if long_pct > 0.70:  # > 70% long
        return {
            'type': 'SENTIMENT_EXTREME_LONG',
            'symbol': symbol,
            'severity': 'WARNING',
            'message': f"Extreme long bias: {long_pct*100:.1f}% long vs {short_pct*100:.1f}% short (ratio: {ratio:.2f})",
            'suggestion': 'Crowded longs - potential for long squeeze if price drops'
        }
    elif short_pct > 0.70:  # > 70% short
        return {
            'type': 'SENTIMENT_EXTREME_SHORT',
            'symbol': symbol,
            'severity': 'WARNING',
            'message': f"Extreme short bias: {long_pct*100:.1f}% long vs {short_pct*100:.1f}% short (ratio: {ratio:.2f})",
            'suggestion': 'Crowded shorts - potential for short squeeze if price rises'
        }
    return None

def check_taker_volume_alert(symbol):
    """Check for taker volume imbalances"""
    data = read_latest_data(symbol, 'taker_volume.csv')
    if not data:
        return None
    
    buy_vol = float(data.get('buyVol', 0))
    sell_vol = float(data.get('sellVol', 0))
    ratio = float(data.get('buySellRatio', 1))
    
    # Use buy_vol and sell_vol in message for clarity
    if ratio > 1.5:
        return {
            'type': 'TAKER_BUY_DOMINANT',
            'symbol': symbol,
            'severity': 'INFO',
            'message': f"Taker buy volume dominant: {buy_vol:.2f} vs {sell_vol:.2f} (ratio {ratio:.2f})",
            'suggestion': 'Aggressive buying pressure detected'
        }
    elif ratio < 0.67:
        return {
            'type': 'TAKER_SELL_DOMINANT',
            'symbol': symbol,
            'severity': 'INFO',
            'message': f"Taker sell volume dominant: {sell_vol:.2f} vs {buy_vol:.2f} (ratio {ratio:.2f})",
            'suggestion': 'Aggressive selling pressure detected'
        }
    return None

def run_alert_check():
    """Run full alert check across all symbols"""
    print("="*70)
    print("COMPASS Alert Check")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    all_alerts = []
    
    for symbol in SYMBOLS:
        print(f"\n📊 Checking {symbol}...")
        
        # Check funding
        alert = check_funding_alert(symbol)
        if alert:
            all_alerts.append(alert)
            print(f"  ⚠️  {alert['type']}: {alert['message']}")
        else:
            print("  ✅ Funding rate normal")
        
        # Check sentiment
        alert = check_sentiment_alert(symbol)
        if alert:
            all_alerts.append(alert)
            print(f"  ⚠️  {alert['type']}: {alert['message']}")
        else:
            print("  ✅ Sentiment balanced")
        
        # Check taker volume
        alert = check_taker_volume_alert(symbol)
        if alert:
            all_alerts.append(alert)
            print(f"  ℹ️  {alert['type']}: {alert['message']}")
        else:
            print("  ✅ Taker volume balanced")
    
    print(f"\n{'='*70}")
    print(f"Alert Summary: {len(all_alerts)} alerts found")
    print('='*70)
    
    # Save alerts to file
    alerts_file = WORKSPACE / 'data' / 'alerts.json'
    alerts_file.parent.mkdir(parents=True, exist_ok=True)
    with open(alerts_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'alerts': all_alerts
        }, f, indent=2)
    
    return all_alerts

if __name__ == '__main__':
    alerts = run_alert_check()
    
    # Print summary for cron
    if alerts:
        critical = [a for a in alerts if a.get('severity') == 'CRITICAL']
        warnings = [a for a in alerts if a.get('severity') == 'WARNING']
        print(f"\n🚨 {len(critical)} CRITICAL, {len(warnings)} WARNINGS")
        exit(1)  # Non-zero exit to signal alerts found
    else:
        print("\n✅ No alerts - all metrics within normal ranges")
        exit(0)
