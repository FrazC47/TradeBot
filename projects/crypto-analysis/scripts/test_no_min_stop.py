#!/usr/bin/env python3
"""
Find Optimal ATR - WITHOUT minimum stop filter
"""

import csv
import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')

def load_data(symbol, interval):
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    if not filepath.exists():
        return []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return [{'timestamp': int(r['open_time']), 'open': float(r['open']), 
                'high': float(r['high']), 'low': float(r['low']), 
                'close': float(r['close']), 'volume': float(r['volume'])} for r in reader]

def backtest_symbol(symbol, stop_mult, target_mult):
    """Backtest WITHOUT minimum stop filter"""
    data_1h = load_data(symbol, '1h')
    data_1d = load_data(symbol, '1d')
    
    if not data_1h or not data_1d:
        return None
    
    setups = []
    
    for i in range(50, len(data_1h) - 20):
        candle = data_1h[i]
        timestamp = candle['timestamp']
        
        # Daily trend
        d_idx = next((j for j, d in enumerate(data_1d) if d['timestamp'] > timestamp), len(data_1d)) - 1
        if d_idx < 20:
            continue
        
        d_recent = data_1d[d_idx-5:d_idx+1]
        d_close = d_recent[-1]['close']
        
        if d_close > d_recent[2]['close']:
            trend = 'bullish'
        else:
            trend = 'bearish'
        
        # 1h context
        h1_recent = data_1h[i-20:i+1]
        h1_high = max(c['high'] for c in h1_recent)
        h1_low = min(c['low'] for c in h1_recent)
        h1_close = candle['close']
        
        # Fibonacci
        diff = h1_high - h1_low
        fib_levels = {
            '0.618': h1_high - diff * 0.618,
            '0.5': h1_high - diff * 0.5,
            '0.382': h1_high - diff * 0.382
        }
        
        at_fib = None
        for level_name, level_price in fib_levels.items():
            if abs(h1_close - level_price) / h1_close < 0.01:
                at_fib = level_name
                break
        
        if not at_fib:
            continue
        
        if trend == 'bullish' and at_fib not in ['0.618', '0.5', '0.382']:
            continue
        if trend == 'bearish' and at_fib not in ['0.382', '0.5', '0.618']:
            continue
        
        # Calculate ATR
        atr = (h1_high - h1_low) * 0.1
        
        # Calculate stop and target
        if trend == 'bearish':
            stop = h1_close + (atr * stop_mult)
            target = h1_close - (atr * target_mult)
        else:
            stop = h1_close - (atr * stop_mult)
            target = h1_close + (atr * target_mult)
        
        # NO MINIMUM STOP FILTER - accept all trades
        
        # Check outcome
        outcome = 'open'
        pnl = 0
        
        for j in range(i+1, min(i+21, len(data_1h))):
            future = data_1h[j]
            
            if trend == 'bearish':
                if future['high'] >= stop:
                    outcome = 'loss'
                    pnl = (h1_close - stop) / h1_close * 100
                    break
                if future['low'] <= target:
                    outcome = 'win'
                    pnl = (h1_close - target) / h1_close * 100
                    break
            else:
                if future['low'] <= stop:
                    outcome = 'loss'
                    pnl = (stop - h1_close) / h1_close * 100
                    break
                if future['high'] >= target:
                    outcome = 'win'
                    pnl = (target - h1_close) / h1_close * 100
                    break
        
        if outcome != 'open':
            setups.append({
                'outcome': outcome,
                'pnl': pnl
            })
    
    if not setups:
        return None
    
    wins = sum(1 for s in setups if s['outcome'] == 'win')
    total_pnl = sum(s['pnl'] for s in setups)
    
    return {
        'trades': len(setups),
        'wins': wins,
        'losses': len(setups) - wins,
        'win_rate': wins / len(setups) * 100,
        'pnl': total_pnl
    }

print("=" * 80)
print("OPTIMAL ATR - WITHOUT MINIMUM STOP FILTER")
print("=" * 80)
print()

stop_mults = [1.0, 1.5, 2.0, 2.5, 3.0]
symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']

for symbol in symbols:
    print(f"\n{symbol}:")
    print("-" * 60)
    print(f"{'Stop':<8} {'Trades':<8} {'Wins':<6} {'Win %':<8} {'P&L %':<10}")
    print("-" * 60)
    
    for stop_mult in stop_mults:
        result = backtest_symbol(symbol, stop_mult, stop_mult * 2)
        
        if result:
            marker = ""
            if result['pnl'] > 0:
                marker = "✅"
            print(f"{stop_mult:<8.1f} {result['trades']:<8} {result['wins']:<6} "
                  f"{result['win_rate']:>6.1f}% {result['pnl']:>+8.2f}% {marker}")
        else:
            print(f"{stop_mult:<8.1f} No trades")

print()
print("OBSERVATION:")
print("=" * 80)
print("Without the minimum stop filter, trade count should be")
print("SIMILAR across all ATR multiples (same entry criteria).")
print()
print("The difference is only in stop placement and outcome.")