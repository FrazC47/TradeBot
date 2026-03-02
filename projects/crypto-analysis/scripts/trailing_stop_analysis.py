#!/usr/bin/env python3
"""
Trailing Stop Analysis
Test if trailing stops would have saved losing trades
"""

import csv
import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')

def load_data(symbol, interval):
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return [{'timestamp': int(r['open_time']), 'high': float(r['high']), 
                'low': float(r['low']), 'close': float(r['close'])} for r in reader]

def backtest_with_trailing_stop(symbol, stop_mult, target_mult, trailing_activation=1.0, trailing_pct=0.5):
    """
    Backtest with trailing stop:
    - trailing_activation: Move stop to breakeven at this profit %
    - trailing_pct: Trail price by this %
    """
    data_1h = load_data(symbol, '1h')
    data_1d = load_data(symbol, '1d')
    
    if not data_1h or not data_1d:
        return None
    
    setups = []
    
    for i in range(50, len(data_1h) - 30):
        candle = data_1h[i]
        timestamp = candle['timestamp']
        
        # Daily trend
        d_idx = None
        for j, d in enumerate(data_1d):
            if d['timestamp'] <= timestamp:
                d_idx = j
        
        if d_idx is None or d_idx < 20:
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
        fib_levels = {'0.618': h1_high - diff * 0.618, '0.5': h1_high - diff * 0.5, '0.382': h1_high - diff * 0.382}
        
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
        
        # Calculate ATR and initial stop/target
        atr = (h1_high - h1_low) * 0.1
        
        if trend == 'bearish':
            initial_stop = h1_close + (atr * stop_mult)
            target = h1_close - (atr * target_mult)
            trailing_active = False
            best_price = h1_close  # Track best price for shorts (lowest)
            
            for j in range(i+1, min(i+31, len(data_1h))):
                future = data_1h[j]
                current_low = future['low']
                current_high = future['high']
                
                # Update best price for short
                if current_low < best_price:
                    best_price = current_low
                
                # Calculate current profit %
                current_profit = (h1_close - current_low) / h1_close * 100
                
                # Activate trailing stop
                if not trailing_active and current_profit >= trailing_activation:
                    trailing_active = True
                    # Move stop to breakeven or better
                    new_stop = h1_close - (h1_close * trailing_pct / 100)
                    if new_stop < initial_stop:
                        initial_stop = new_stop
                
                # Update trailing stop if active
                if trailing_active:
                    # Trail at trailing_pct below best price
                    trail_stop = best_price + (best_price * trailing_pct / 100)
                    if trail_stop < initial_stop:
                        initial_stop = trail_stop
                
                # Check if stop hit
                if current_high >= initial_stop:
                    pnl = (h1_close - initial_stop) / h1_close * 100
                    setups.append({
                        'outcome': 'loss' if pnl < 0 else 'win',
                        'pnl': pnl,
                        'trailing_used': trailing_active
                    })
                    break
                
                # Check if target hit
                if current_low <= target:
                    pnl = (h1_close - target) / h1_close * 100
                    setups.append({
                        'outcome': 'win',
                        'pnl': pnl,
                        'trailing_used': trailing_active
                    })
                    break
        else:
            # Bullish - similar logic
            initial_stop = h1_close - (atr * stop_mult)
            target = h1_close + (atr * target_mult)
            trailing_active = False
            best_price = h1_close
            
            for j in range(i+1, min(i+31, len(data_1h))):
                future = data_1h[j]
                current_high = future['high']
                current_low = future['low']
                
                if current_high > best_price:
                    best_price = current_high
                
                current_profit = (current_high - h1_close) / h1_close * 100
                
                if not trailing_active and current_profit >= trailing_activation:
                    trailing_active = True
                    new_stop = h1_close + (h1_close * trailing_pct / 100)
                    if new_stop > initial_stop:
                        initial_stop = new_stop
                
                if trailing_active:
                    trail_stop = best_price - (best_price * trailing_pct / 100)
                    if trail_stop > initial_stop:
                        initial_stop = trail_stop
                
                if current_low <= initial_stop:
                    pnl = (initial_stop - h1_close) / h1_close * 100
                    setups.append({
                        'outcome': 'loss' if pnl < 0 else 'win',
                        'pnl': pnl,
                        'trailing_used': trailing_active
                    })
                    break
                
                if current_high >= target:
                    pnl = (target - h1_close) / h1_close * 100
                    setups.append({
                        'outcome': 'win',
                        'pnl': pnl,
                        'trailing_used': trailing_active
                    })
                    break
    
    if not setups:
        return None
    
    wins = sum(1 for s in setups if s['outcome'] == 'win')
    total_pnl = sum(s['pnl'] for s in setups)
    trailing_used = sum(1 for s in setups if s['trailing_used'])
    
    return {
        'trades': len(setups),
        'wins': wins,
        'losses': len(setups) - wins,
        'win_rate': wins / len(setups) * 100,
        'pnl': total_pnl,
        'trailing_activations': trailing_used
    }

print("=" * 90)
print("TRAILING STOP ANALYSIS")
print("=" * 90)
print()
print("Testing: Activate trailing at 1% profit, trail by 0.5%")
print()

symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']

for symbol in symbols:
    print(f"\n{symbol}:")
    print("-" * 70)
    
    # Without trailing stop
    result_no_trail = backtest_with_trailing_stop(symbol, 2.0, 4.0, trailing_activation=999, trailing_pct=0.5)
    
    # With trailing stop
    result_with_trail = backtest_with_trailing_stop(symbol, 2.0, 4.0, trailing_activation=1.0, trailing_pct=0.5)
    
    if result_no_trail and result_with_trail:
        print(f"{'Strategy':<25} {'Trades':<8} {'Wins':<6} {'Win %':<8} {'P&L %':<10} {'Trail Used'}")
        print("-" * 70)
        
        print(f"{'Fixed Stop':<25} {result_no_trail['trades']:<8} {result_no_trail['wins']:<6} "
              f"{result_no_trail['win_rate']:>6.1f}% {result_no_trail['pnl']:>+8.2f}% {'N/A'}")
        
        print(f"{'Trailing Stop (1%/0.5%)':<25} {result_with_trail['trades']:<8} {result_with_trail['wins']:<6} "
              f"{result_with_trail['win_rate']:>6.1f}% {result_with_trail['pnl']:>+8.2f}% {result_with_trail['trailing_activations']}")
        
        improvement = result_with_trail['pnl'] - result_no_trail['pnl']
        if improvement > 0:
            print(f"\n✅ Trailing stop helps: +{improvement:.2f}% improvement")
        elif improvement < 0:
            print(f"\n❌ Trailing stop hurts: {improvement:.2f}% worse")
        else:
            print(f"\n➡️ No significant difference")

print("\n" + "=" * 90)
print("CONCLUSION")
print("=" * 90)
print()
print("Trailing stops can help when:")
print("  - Price moves in your favor then reverses")
print("  - You want to lock in profits")
print("  - Market is choppy")
print()
print("Trailing stops can hurt when:")
print("  - Price whipsaws before continuing trend")
print("  - You get stopped out too early on normal retracements")
print("  - Market is trending strongly")
print()
print("Recommendation: Test on live trades, not just backtests.")
