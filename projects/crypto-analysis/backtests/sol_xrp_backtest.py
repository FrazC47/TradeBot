#!/usr/bin/env python3
"""
SOL & XRP Backtesting - Parameter Optimization
Tests multiple ATR multipliers, entry methods, and filters
"""

import csv
import json
from pathlib import Path
from datetime import datetime
import itertools

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')

def load_data(symbol, interval):
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return [{'timestamp': int(r['open_time']), 'open': float(r['open']),
                'high': float(r['high']), 'low': float(r['low']), 
                'close': float(r['close']), 'volume': float(r['volume'])} for r in reader]

def calculate_atr(data, period=14, idx=None):
    """Calculate ATR at given index"""
    if idx is None:
        idx = len(data) - 1
    if idx < period:
        return (data[idx]['high'] - data[idx]['low']) * 0.5
    
    tr_sum = 0
    for i in range(idx-period+1, idx+1):
        high = data[i]['high']
        low = data[i]['low']
        prev_close = data[i-1]['close'] if i > 0 else data[i]['open']
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_sum += tr
    return tr_sum / period

def calculate_fib_levels(data, lookback=20, idx=None):
    """Calculate Fibonacci retracement levels"""
    if idx is None:
        idx = len(data) - 1
    if idx < lookback:
        return None
    
    recent = data[idx-lookback:idx+1]
    high = max(c['high'] for c in recent)
    low = min(c['low'] for c in recent)
    diff = high - low
    
    return {
        '0.0': high,
        '0.382': high - diff * 0.382,
        '0.5': high - diff * 0.5,
        '0.618': high - diff * 0.618,
        '1.0': low
    }

def backtest_fib_pullback(symbol, data, params):
    """Backtest Fibonacci pullback strategy"""
    setups = []
    
    for i in range(50, len(data) - 20):
        candle = data[i]
        close = candle['close']
        
        # Get trend
        trend_up = close > data[i-10]['close']
        trend_down = close < data[i-10]['close']
        
        if not (trend_up or trend_down):
            continue
        
        # Calculate Fibonacci levels
        fibs = calculate_fib_levels(data, 20, i)
        if not fibs:
            continue
        
        # Check if at Fib level
        at_fib = None
        for level_name in params['fib_levels']:
            level_price = fibs[level_name]
            if abs(close - level_price) / close < params['fib_tolerance']:
                at_fib = level_name
                break
        
        if not at_fib:
            continue
        
        # Calculate ATR
        atr = calculate_atr(data, 14, i)
        
        # Determine direction
        if trend_up:
            trend = 'bullish'
            entry = close
            stop = entry - (atr * params['stop_mult'])
            target = entry + (atr * params['target_mult'])
        else:
            trend = 'bearish'
            entry = close
            stop = entry + (atr * params['stop_mult'])
            target = entry - (atr * params['target_mult'])
        
        # Check min stop
        stop_pct = abs(stop - entry) / entry * 100
        if stop_pct < params['min_stop_pct']:
            continue
        
        # Simulate trade
        for j in range(i+1, min(i+params['holding_periods']+1, len(data))):
            future = data[j]
            
            if trend == 'bullish':
                if future['low'] <= stop:
                    pnl = (stop - entry) / entry * 100
                    setups.append({'outcome': 'loss', 'pnl': pnl})
                    break
                if future['high'] >= target:
                    pnl = (target - entry) / entry * 100
                    setups.append({'outcome': 'win', 'pnl': pnl})
                    break
            else:
                if future['high'] >= stop:
                    pnl = (entry - stop) / entry * 100
                    setups.append({'outcome': 'loss', 'pnl': pnl})
                    break
                if future['low'] <= target:
                    pnl = (entry - target) / entry * 100
                    setups.append({'outcome': 'win', 'pnl': pnl})
                    break
    
    if not setups:
        return None
    
    wins = sum(1 for s in setups if s['outcome'] == 'win')
    total_pnl = sum(s['pnl'] for s in setups)
    
    return {
        'trades': len(setups),
        'wins': wins,
        'win_rate': wins / len(setups) * 100,
        'pnl': total_pnl,
        'avg_trade': total_pnl / len(setups)
    }

def backtest_breakout(symbol, data, params):
    """Backtest breakout strategy"""
    setups = []
    
    for i in range(50, len(data) - 20):
        candle = data[i]
        close = candle['close']
        
        # Calculate 20-period high/low
        recent = data[i-20:i]
        recent_high = max(c['high'] for c in recent)
        recent_low = min(c['low'] for c in recent)
        
        # Check for breakout
        buffer = params['breakout_buffer']
        trend = None
        
        if close > recent_high * (1 + buffer):
            trend = 'bullish'
            entry = close
            stop = recent_low
            target = entry + (entry - stop) * params['rr_ratio']
        elif close < recent_low * (1 - buffer):
            trend = 'bearish'
            entry = close
            stop = recent_high
            target = entry - (stop - entry) * params['rr_ratio']
        
        if not trend:
            continue
        
        # Simulate trade
        for j in range(i+1, min(i+params['holding_periods']+1, len(data))):
            future = data[j]
            
            if trend == 'bullish':
                if future['low'] <= stop:
                    pnl = (stop - entry) / entry * 100
                    setups.append({'outcome': 'loss', 'pnl': pnl})
                    break
                if future['high'] >= target:
                    pnl = (target - entry) / entry * 100
                    setups.append({'outcome': 'win', 'pnl': pnl})
                    break
            else:
                if future['high'] >= stop:
                    pnl = (entry - stop) / entry * 100
                    setups.append({'outcome': 'loss', 'pnl': pnl})
                    break
                if future['low'] <= target:
                    pnl = (entry - target) / entry * 100
                    setups.append({'outcome': 'win', 'pnl': pnl})
                    break
    
    if not setups:
        return None
    
    wins = sum(1 for s in setups if s['outcome'] == 'win')
    total_pnl = sum(s['pnl'] for s in setups)
    
    return {
        'trades': len(setups),
        'wins': wins,
        'win_rate': wins / len(setups) * 100,
        'pnl': total_pnl,
        'avg_trade': total_pnl / len(setups)
    }

print("=" * 90)
print("SOL & XRP BACKTEST - PARAMETER OPTIMIZATION")
print("=" * 90)
print()

# Load data
sol_data = load_data('SOLUSDT', '1h')
xrp_data = load_data('XRPUSDT', '1h')

print(f"SOL data: {len(sol_data)} candles")
print(f"XRP data: {len(xrp_data)} candles")
print()

# Test parameter combinations
stop_mults = [1.5, 2.0, 2.5, 3.0]
target_mults = [3.0, 4.0, 5.0, 6.0]
fib_tolerances = [0.005, 0.01, 0.015]
holding_periods = [10, 15, 20]

print("Testing Fibonacci Pullback Strategy on SOL...")
print("-" * 70)

sol_results = []
for stop, target, fib_tol, hold in itertools.product(stop_mults, target_mults, fib_tolerances, holding_periods):
    if target <= stop * 1.5:  # Minimum 1.5:1 R:R
        continue
    
    params = {
        'fib_levels': ['0.618', '0.5'],
        'fib_tolerance': fib_tol,
        'stop_mult': stop,
        'target_mult': target,
        'min_stop_pct': 1.0,
        'holding_periods': hold
    }
    
    result = backtest_fib_pullback('SOLUSDT', sol_data, params)
    if result and result['trades'] >= 5:
        sol_results.append({
            'params': params,
            'result': result
        })

# Sort by P&L
sol_results.sort(key=lambda x: x['result']['pnl'], reverse=True)

print(f"{'Stop':<6} {'Target':<8} {'Fib':<6} {'Hold':<6} {'Trades':<8} {'Win%':<8} {'P&L%':<10} {'Avg%':<8}")
print("-" * 70)
for r in sol_results[:10]:
    p = r['params']
    res = r['result']
    print(f"{p['stop_mult']:<6} {p['target_mult']:<8} {p['fib_tolerance']:<6} {p['holding_periods']:<6} {res['trades']:<8} {res['win_rate']:<8.1f} {res['pnl']:<10.2f} {res['avg_trade']:<8.2f}")

print()
print("Testing Breakout Strategy on XRP...")
print("-" * 70)

xrp_results = []
buffers = [0.002, 0.003, 0.005]
rr_ratios = [2.0, 2.5, 3.0, 3.5]

for buffer, rr, hold in itertools.product(buffers, rr_ratios, holding_periods):
    params = {
        'breakout_buffer': buffer,
        'rr_ratio': rr,
        'holding_periods': hold
    }
    
    result = backtest_breakout('XRPUSDT', xrp_data, params)
    if result and result['trades'] >= 5:
        xrp_results.append({
            'params': params,
            'result': result
        })

# Sort by P&L
xrp_results.sort(key=lambda x: x['result']['pnl'], reverse=True)

print(f"{'Buffer':<8} {'R:R':<6} {'Hold':<6} {'Trades':<8} {'Win%':<8} {'P&L%':<10} {'Avg%':<8}")
print("-" * 70)
for r in xrp_results[:10]:
    p = r['params']
    res = r['result']
    print(f"{p['breakout_buffer']:<8} {p['rr_ratio']:<6} {p['holding_periods']:<6} {res['trades']:<8} {res['win_rate']:<8.1f} {res['pnl']:<10.2f} {res['avg_trade']:<8.2f}")

print()
print("=" * 90)
print("OPTIMAL PARAMETERS")
print("=" * 90)

if sol_results:
    best_sol = sol_results[0]
    print(f"\nSOL Best:")
    print(f"  Stop: {best_sol['params']['stop_mult']}x ATR")
    print(f"  Target: {best_sol['params']['target_mult']}x ATR")
    print(f"  Fib Tolerance: {best_sol['params']['fib_tolerance']}")
    print(f"  Holding: {best_sol['params']['holding_periods']} periods")
    print(f"  Result: {best_sol['result']['trades']} trades, {best_sol['result']['win_rate']:.1f}% win, {best_sol['result']['pnl']:+.2f}% P&L")

if xrp_results:
    best_xrp = xrp_results[0]
    print(f"\nXRP Best:")
    print(f"  Buffer: {best_xrp['params']['breakout_buffer']}")
    print(f"  R:R Ratio: {best_xrp['params']['rr_ratio']}:1")
    print(f"  Holding: {best_xrp['params']['holding_periods']} periods")
    print(f"  Result: {best_xrp['result']['trades']} trades, {best_xrp['result']['win_rate']:.1f}% win, {best_xrp['result']['pnl']:+.2f}% P&L")
