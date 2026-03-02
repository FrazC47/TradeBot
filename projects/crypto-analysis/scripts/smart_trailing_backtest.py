#!/usr/bin/env python3
"""
Smart Trailing Stop Backtest
Based on Fibonacci levels, ATR, and swing highs/lows
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
                'low': float(r['low']), 'close': float(r['close'])} for r in reader]

def calculate_fib_levels(high, low):
    """Calculate Fibonacci retracement levels"""
    diff = high - low
    return {
        '0.0': high,
        '0.236': high - diff * 0.236,
        '0.382': high - diff * 0.382,
        '0.5': high - diff * 0.5,
        '0.618': high - diff * 0.618,
        '0.786': high - diff * 0.786,
        '1.0': low
    }

def backtest_smart_trailing(symbol, data_1h):
    """Backtest with smart trailing stops"""
    
    setups = []
    
    for i in range(50, len(data_1h) - 30):
        candle = data_1h[i]
        h1_close = candle['close']
        
        # Get 1h context
        h1_recent = data_1h[i-20:i+1]
        h1_high = max(c['high'] for c in h1_recent)
        h1_low = min(c['low'] for c in h1_recent)
        atr = (h1_high - h1_low) * 0.1
        
        # Calculate Fib levels
        fib_levels = calculate_fib_levels(h1_high, h1_low)
        
        # Determine trend
        if h1_close > h1_recent[10]['close']:
            trend = 'bullish'
            entry = h1_close
            stop = entry - (atr * 2)
            target = entry + (atr * 4)
            initial_risk = entry - stop
            
            current_stop = stop
            breakeven_moved = False
            
            for j in range(i+1, min(i+31, len(data_1h))):
                future = data_1h[j]
                current_high = future['high']
                current_low = future['low']
                
                # Calculate current profit and R:R
                current_profit = current_high - entry
                current_rr = current_profit / initial_risk if initial_risk > 0 else 0
                
                # Rule 1: Move to breakeven at 1:1 R:R
                if not breakeven_moved and current_rr >= 1.0:
                    new_stop = entry + (atr * 0.3)  # Small buffer above entry
                    if new_stop > current_stop:
                        current_stop = new_stop
                        breakeven_moved = True
                
                # Rule 2: Move to Fib level when crossed
                if breakeven_moved:
                    fib_order = ['0.382', '0.5', '0.618']
                    for idx, fib_name in enumerate(fib_order):
                        fib_level = fib_levels[fib_name]
                        # If price crossed above this Fib
                        if current_high > fib_level:
                            # Move stop to previous Fib (or entry if at 0.382)
                            if idx == 0:
                                new_stop = max(entry, current_stop)
                            else:
                                prev_fib = fib_levels[fib_order[idx-1]]
                                new_stop = prev_fib - (atr * 0.3)
                            
                            if new_stop > current_stop:
                                current_stop = new_stop
                                break  # Only move one Fib level at a time
                
                # Rule 3: Trail at 1x ATR behind recent swing low
                if breakeven_moved:
                    recent_candles = data_1h[max(0, j-3):j+1]
                    swing_low = min(c['low'] for c in recent_candles)
                    atr_trail = swing_low - (atr * 1.0)
                    if atr_trail > current_stop:
                        current_stop = atr_trail
                
                # Check if stopped out
                if current_low <= current_stop:
                    pnl = (current_stop - entry) / entry * 100
                    setups.append({
                        'outcome': 'win' if pnl > 0 else 'loss',
                        'pnl': pnl,
                        'breakeven_moved': breakeven_moved
                    })
                    break
                
                # Check if target hit
                if current_high >= target:
                    pnl = (target - entry) / entry * 100
                    setups.append({
                        'outcome': 'win',
                        'pnl': pnl,
                        'breakeven_moved': breakeven_moved
                    })
                    break
        
        else:
            # Bearish
            trend = 'bearish'
            entry = h1_close
            stop = entry + (atr * 2)
            target = entry - (atr * 4)
            initial_risk = stop - entry
            
            current_stop = stop
            breakeven_moved = False
            
            for j in range(i+1, min(i+31, len(data_1h))):
                future = data_1h[j]
                current_high = future['high']
                current_low = future['low']
                
                current_profit = entry - current_low
                current_rr = current_profit / initial_risk if initial_risk > 0 else 0
                
                # Rule 1: Breakeven at 1:1
                if not breakeven_moved and current_rr >= 1.0:
                    new_stop = entry - (atr * 0.3)
                    if new_stop < current_stop:
                        current_stop = new_stop
                        breakeven_moved = True
                
                # Rule 2: Move to Fib level
                if breakeven_moved:
                    fib_order = ['0.382', '0.5', '0.618']
                    for idx, fib_name in enumerate(fib_order):
                        fib_level = fib_levels[fib_name]
                        if current_low < fib_level:
                            if idx == 0:
                                new_stop = min(entry, current_stop)
                            else:
                                prev_fib = fib_levels[fib_order[idx-1]]
                                new_stop = prev_fib + (atr * 0.3)
                            
                            if new_stop < current_stop:
                                current_stop = new_stop
                                break
                
                # Rule 3: ATR trail
                if breakeven_moved:
                    recent_candles = data_1h[max(0, j-3):j+1]
                    swing_high = max(c['high'] for c in recent_candles)
                    atr_trail = swing_high + (atr * 1.0)
                    if atr_trail < current_stop:
                        current_stop = atr_trail
                
                if current_high >= current_stop:
                    pnl = (entry - current_stop) / entry * 100
                    setups.append({
                        'outcome': 'win' if pnl > 0 else 'loss',
                        'pnl': pnl,
                        'breakeven_moved': breakeven_moved
                    })
                    break
                
                if current_low <= target:
                    pnl = (entry - target) / entry * 100
                    setups.append({
                        'outcome': 'win',
                        'pnl': pnl,
                        'breakeven_moved': breakeven_moved
                    })
                    break
    
    if not setups:
        return None
    
    wins = sum(1 for s in setups if s['outcome'] == 'win')
    breakeven_count = sum(1 for s in setups if s['breakeven_moved'])
    
    return {
        'trades': len(setups),
        'wins': wins,
        'losses': len(setups) - wins,
        'win_rate': wins / len(setups) * 100,
        'pnl': sum(s['pnl'] for s in setups),
        'breakeven_activations': breakeven_count
    }

print("=" * 90)
print("SMART TRAILING STOP BACKTEST")
print("=" * 90)
print()
print("Rules:")
print("  1. Move to breakeven + 0.3x ATR buffer at 1:1 R:R")
print("  2. Move stop to previous Fib level when price crosses Fib")
print("  3. Trail at 1x ATR behind 3-candle swing low/high")
print()

symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']

for symbol in symbols:
    print(f"\n{symbol}:")
    print("-" * 70)
    
    data_1h = load_data(symbol, '1h')
    
    if not data_1h:
        print("  No data available")
        continue
    
    result = backtest_smart_trailing(symbol, data_1h)
    
    if result:
        print(f"  Trades: {result['trades']}")
        print(f"  Wins: {result['wins']} ({result['win_rate']:.1f}%)")
        print(f"  Losses: {result['losses']}")
        print(f"  P&L: {result['pnl']:+.2f}%")
        print(f"  Breakeven activations: {result['breakeven_activations']}")
        
        if result['pnl'] > 0:
            print(f"  ✅ PROFITABLE")
        else:
            print(f"  ❌ UNPROFITABLE")
    else:
        print("  No trades found")

print("\n" + "=" * 90)
