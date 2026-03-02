#!/usr/bin/env python3
"""
Final Backtest with Proportional Minimum Stop Filter
Min stop = 0.5% * (atr_mult / 2.0)
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

def backtest_with_proportional_filter(symbol, stop_mult, target_mult):
    """Backtest with proportional minimum stop filter"""
    data_1h = load_data(symbol, '1h')
    data_1d = load_data(symbol, '1d')
    
    if not data_1h or not data_1d:
        return None
    
    # Proportional minimum stop: 0.5% at 2x ATR, scaled for other multiples
    min_stop_pct = 0.5 * (stop_mult / 2.0)
    
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
        
        # PROPORTIONAL MINIMUM STOP FILTER
        stop_distance = abs(stop - h1_close) / h1_close * 100
        if stop_distance < min_stop_pct:
            continue
        
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
        'pnl': total_pnl,
        'min_stop_used': min_stop_pct
    }

print("=" * 90)
print("BACKTEST WITH PROPORTIONAL MINIMUM STOP FILTER")
print("=" * 90)
print()
print("Min stop = 0.5% * (atr_mult / 2.0)")
print("  1.0x ATR → 0.25% minimum")
print("  1.5x ATR → 0.375% minimum")
print("  2.0x ATR → 0.50% minimum (original)")
print("  2.5x ATR → 0.625% minimum")
print("  3.0x ATR → 0.75% minimum")
print()

stop_mults = [1.0, 1.5, 2.0, 2.5, 3.0]
symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']

best_results = {}

for symbol in symbols:
    print(f"\n{'=' * 90}")
    print(f"{symbol}")
    print(f"{'=' * 90}")
    print(f"{'Stop':<8} {'Min Stop':<10} {'Trades':<8} {'Wins':<6} {'Win %':<8} {'P&L %':<10} {'Rating'}")
    print("-" * 90)
    
    symbol_results = []
    
    for stop_mult in stop_mults:
        result = backtest_with_proportional_filter(symbol, stop_mult, stop_mult * 2)
        
        if result:
            rating = result['pnl'] * result['win_rate'] / 100
            marker = "✅" if result['pnl'] > 0 else ""
            
            print(f"{stop_mult:<8.1f} {result['min_stop_used']:<10.2f}% {result['trades']:<8} "
                  f"{result['wins']:<6} {result['win_rate']:>6.1f}% {result['pnl']:>+8.2f}% "
                  f"{marker}")
            
            symbol_results.append({
                'stop_mult': stop_mult,
                'result': result,
                'rating': rating
            })
        else:
            print(f"{stop_mult:<8.1f} {0.5 * (stop_mult/2.0):<10.2f}% No trades")
    
    # Find best
    if symbol_results:
        best = max(symbol_results, key=lambda x: x['rating'])
        best_results[symbol] = best
        
        print()
        print(f"🏆 OPTIMAL for {symbol}: {best['stop_mult']}x ATR")
        print(f"   Min stop: {best['result']['min_stop_used']:.2f}%")
        print(f"   Win Rate: {best['result']['win_rate']:.1f}%")
        print(f"   P&L: {best['result']['pnl']:+.2f}%")
        print(f"   Trades: {best['result']['trades']}")

# Summary
print("\n" + "=" * 90)
print("FINAL RECOMMENDATIONS - WITH PROPORTIONAL FILTER")
print("=" * 90)
print()

for symbol, best in best_results.items():
    stop = best['stop_mult']
    target = stop * 2
    min_stop = best['result']['min_stop_used']
    print(f"{symbol}:")
    print(f"  Stop ATR: {stop}x ({min_stop:.2f}% minimum)")
    print(f"  Target: {target}x")
    print(f"  Expected: {best['result']['win_rate']:.1f}% win rate, {best['result']['pnl']:+.2f}% P&L")
    print()

# Save
output = {
    'filter_type': 'proportional',
    'base_min_stop': 0.5,
    'base_atr': 2.0,
    'BTCUSDT': {
        'stop_atr_mult': best_results['BTCUSDT']['stop_mult'],
        'target_atr_mult': best_results['BTCUSDT']['stop_mult'] * 2,
        'min_stop_pct': best_results['BTCUSDT']['result']['min_stop_used']
    },
    'ETHUSDT': {
        'stop_atr_mult': best_results['ETHUSDT']['stop_mult'],
        'target_atr_mult': best_results['ETHUSDT']['stop_mult'] * 2,
        'min_stop_pct': best_results['ETHUSDT']['result']['min_stop_used']
    },
    'BNBUSDT': {
        'stop_atr_mult': best_results['BNBUSDT']['stop_mult'],
        'target_atr_mult': best_results['BNBUSDT']['stop_mult'] * 2,
        'min_stop_pct': best_results['BNBUSDT']['result']['min_stop_used']
    }
}

with open('backtests/final_strategies_proportional.json', 'w') as f:
    json.dump(output, f, indent=2)

print("Saved to: backtests/final_strategies_proportional.json")
