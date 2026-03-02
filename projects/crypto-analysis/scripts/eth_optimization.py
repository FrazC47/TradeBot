#!/usr/bin/env python3
"""
ETH Strategy Optimization - Find Better Balance
Test variations to increase trade count while maintaining profitability
"""

import csv
from pathlib import Path
from datetime import datetime

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')

def load_data(symbol, interval):
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return [{'timestamp': int(r['open_time']), 'high': float(r['high']), 
                'low': float(r['low']), 'close': float(r['close']), 'volume': float(r['volume'])} for r in reader]

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return [None] * len(prices)
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    rsi = [None]
    for i in range(period, len(deltas)):
        gains = [d for d in deltas[i-period:i] if d > 0]
        losses = [-d for d in deltas[i-period:i] if d < 0]
        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0
        if avg_loss == 0:
            rsi.append(100)
        else:
            rsi.append(100 - (100 / (1 + avg_gain / avg_loss)))
    return [None] * period + rsi[period:]

def test_eth_variant(data_1h, data_1d, params):
    """Test ETH with specific parameters"""
    
    setups = []
    
    for i in range(50, len(data_1h) - 20):
        candle = data_1h[i]
        h1_close = candle['close']
        timestamp = candle['timestamp']
        
        # Daily trend
        d_idx = None
        for j, d in enumerate(data_1d):
            if d['timestamp'] <= timestamp:
                d_idx = j
        
        if d_idx is None or d_idx < 5:
            continue
        
        d_recent = data_1d[d_idx-5:d_idx+1]
        d_close = d_recent[-1]['close']
        d_old = d_recent[0]['close']
        
        if d_close > d_old:
            trend = 'bullish'
        elif d_close < d_old:
            trend = 'bearish'
        else:
            continue
        
        # 1h context
        h1_recent = data_1h[i-20:i+1]
        h1_high = max(c['high'] for c in h1_recent)
        h1_low = min(c['low'] for c in h1_recent)
        
        # Fibonacci
        diff = h1_high - h1_low
        fib_levels = {}
        for level in params['fib_levels']:
            if level == '0.618':
                fib_levels[level] = h1_high - diff * 0.618
            elif level == '0.5':
                fib_levels[level] = h1_high - diff * 0.5
            elif level == '0.382':
                fib_levels[level] = h1_high - diff * 0.382
        
        at_fib = None
        for level_name, level_price in fib_levels.items():
            if abs(h1_close - level_price) / h1_close < params['fib_tolerance']:
                at_fib = level_name
                break
        
        if not at_fib:
            continue
        
        # RSI check
        h1_closes = [c['close'] for c in h1_recent]
        rsi_list = calculate_rsi(h1_closes, 14)
        rsi = rsi_list[-1] if rsi_list[-1] else 50
        
        if trend == 'bullish' and rsi > params['rsi_max']:
            continue
        if trend == 'bearish' and rsi < params['rsi_min']:
            continue
        
        # Consecutive candles filter (if enabled)
        if params.get('consecutive_candles', 0) > 0:
            recent_closes = [c['close'] for c in h1_recent[-params['consecutive_candles']-1:]]
            if trend == 'bullish':
                # Check for consecutive higher closes
                consecutive = sum(1 for j in range(1, len(recent_closes)) if recent_closes[j] > recent_closes[j-1])
                if consecutive < params['consecutive_candles']:
                    continue
            else:
                consecutive = sum(1 for j in range(1, len(recent_closes)) if recent_closes[j] < recent_closes[j-1])
                if consecutive < params['consecutive_candles']:
                    continue
        
        # Calculate ATR
        atr = (h1_high - h1_low) * 0.1
        
        # Calculate stop and target
        if trend == 'bearish':
            stop = h1_close + (atr * params['stop_mult'])
            target = h1_close - (atr * params['target_mult'])
        else:
            stop = h1_close - (atr * params['stop_mult'])
            target = h1_close + (atr * params['target_mult'])
        
        # Check outcome
        for j in range(i+1, min(i+21, len(data_1h))):
            future = data_1h[j]
            
            if trend == 'bearish':
                if future['high'] >= stop:
                    setups.append({'outcome': 'loss', 'pnl': (h1_close - stop) / h1_close * 100})
                    break
                if future['low'] <= target:
                    setups.append({'outcome': 'win', 'pnl': (h1_close - target) / h1_close * 100})
                    break
            else:
                if future['low'] <= stop:
                    setups.append({'outcome': 'loss', 'pnl': (stop - h1_close) / h1_close * 100})
                    break
                if future['high'] >= target:
                    setups.append({'outcome': 'win', 'pnl': (target - h1_close) / h1_close * 100})
                    break
    
    if not setups:
        return None
    
    wins = sum(1 for s in setups if s['outcome'] == 'win')
    return {
        'trades': len(setups),
        'wins': wins,
        'losses': len(setups) - wins,
        'win_rate': wins / len(setups) * 100,
        'pnl': sum(s['pnl'] for s in setups)
    }

print("=" * 90)
print("ETH STRATEGY OPTIMIZATION")
print("=" * 90)
print()

# Load data
data_1h = load_data('ETHUSDT', '1h')
data_1d = load_data('ETHUSDT', '1d')

if not data_1h or not data_1d:
    print("No data available")
    exit()

# Test variations
test_variants = [
    {'name': 'Current (too strict)', 'fib_levels': ['0.618', '0.5'], 'fib_tolerance': 0.01, 'stop_mult': 1.5, 'target_mult': 3.0, 'rsi_max': 70, 'rsi_min': 30, 'consecutive_candles': 3},
    {'name': 'No consecutive filter', 'fib_levels': ['0.618', '0.5'], 'fib_tolerance': 0.01, 'stop_mult': 1.5, 'target_mult': 3.0, 'rsi_max': 70, 'rsi_min': 30, 'consecutive_candles': 0},
    {'name': 'Wider Fib tolerance', 'fib_levels': ['0.618', '0.5'], 'fib_tolerance': 0.015, 'stop_mult': 1.5, 'target_mult': 3.0, 'rsi_max': 70, 'rsi_min': 30, 'consecutive_candles': 0},
    {'name': 'Add 0.382 Fib', 'fib_levels': ['0.618', '0.5', '0.382'], 'fib_tolerance': 0.01, 'stop_mult': 1.5, 'target_mult': 3.0, 'rsi_max': 70, 'rsi_min': 30, 'consecutive_candles': 0},
    {'name': 'Wider RSI range', 'fib_levels': ['0.618', '0.5'], 'fib_tolerance': 0.01, 'stop_mult': 1.5, 'target_mult': 3.0, 'rsi_max': 75, 'rsi_min': 25, 'consecutive_candles': 0},
    {'name': 'Wider stop (2x)', 'fib_levels': ['0.618', '0.5'], 'fib_tolerance': 0.01, 'stop_mult': 2.0, 'target_mult': 4.0, 'rsi_max': 70, 'rsi_min': 30, 'consecutive_candles': 0},
    {'name': 'Combined loose', 'fib_levels': ['0.618', '0.5', '0.382'], 'fib_tolerance': 0.015, 'stop_mult': 2.0, 'target_mult': 4.0, 'rsi_max': 75, 'rsi_min': 25, 'consecutive_candles': 0},
]

print(f"{'Variant':<25} {'Trades':<8} {'Wins':<6} {'Win %':<8} {'P&L %':<10} {'Status'}")
print("-" * 90)

results = []

for variant in test_variants:
    name = variant.pop('name')
    result = test_eth_variant(data_1h, data_1d, variant)
    
    if result:
        marker = "✅" if result['pnl'] > 0 and result['trades'] >= 10 else "⚠️" if result['pnl'] > 0 else "❌"
        print(f"{name:<25} {result['trades']:<8} {result['wins']:<6} {result['win_rate']:>6.1f}% {result['pnl']:>+8.2f}% {marker}")
        results.append({'name': name, 'result': result, 'params': variant})
    else:
        print(f"{name:<25} No trades")

# Find best balanced result
print("\n" + "=" * 90)
print("RECOMMENDATION:")
print("=" * 90)
print()

# Sort by trades first, then by P&L
balanced = [r for r in results if r['result']['trades'] >= 10 and r['result']['pnl'] > 0]
if balanced:
    best = max(balanced, key=lambda x: x['result']['pnl'])
    print(f"🏆 BEST BALANCED: {best['name']}")
    print(f"   Trades: {best['result']['trades']}")
    print(f"   Win Rate: {best['result']['win_rate']:.1f}%")
    print(f"   P&L: {best['result']['pnl']:+.2f}%")
    print()
    print("Parameters:")
    for k, v in best['params'].items():
        print(f"   {k}: {v}")
else:
    print("No variant with 10+ trades and positive P&L found.")
    print("Need to relax filters further or accept fewer trades.")