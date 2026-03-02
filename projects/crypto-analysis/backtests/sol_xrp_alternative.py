#!/usr/bin/env python3
"""
SOL & XRP Alternative Strategy Testing
Tests mean reversion and trend following approaches
"""

import csv
from pathlib import Path
from datetime import datetime

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')

def load_data(symbol, interval):
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return [{'timestamp': int(r['open_time']), 'open': float(r['open']),
                'high': float(r['high']), 'low': float(r['low']), 
                'close': float(r['close']), 'volume': float(r['volume'])} for r in reader]

def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    if len(prices) < period + 1:
        return [50] * len(prices)
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    rsi = [50]
    
    for i in range(period, len(deltas)):
        gains = [d for d in deltas[i-period:i] if d > 0]
        losses = [-d for d in deltas[i-period:i] if d < 0]
        avg_gain = sum(gains) / period if gains else 0.001
        avg_loss = sum(losses) / period if losses else 0.001
        rs = avg_gain / avg_loss
        rsi.append(100 - (100 / (1 + rs)))
    
    return [50] * period + rsi[period:]

def calculate_ema(prices, period):
    """Calculate EMA"""
    if len(prices) < period:
        return [None] * len(prices)
    multiplier = 2 / (period + 1)
    ema = [sum(prices[:period]) / period]
    for p in prices[period:]:
        ema.append((p * multiplier) + (ema[-1] * (1 - multiplier)))
    return [None] * (period - 1) + ema

def backtest_mean_reversion(data, rsi_low=30, rsi_high=70, stop_pct=2.0, target_pct=4.0):
    """Mean reversion: Buy oversold, Sell overbought"""
    setups = []
    prices = [c['close'] for c in data]
    rsi = calculate_rsi(prices)
    
    for i in range(50, len(data) - 20):
        candle = data[i]
        close = candle['close']
        current_rsi = rsi[i] if i < len(rsi) else 50
        
        # Entry conditions
        if current_rsi < rsi_low:
            trend = 'bullish'  # Buy oversold
            entry = close
            stop = entry * (1 - stop_pct/100)
            target = entry * (1 + target_pct/100)
        elif current_rsi > rsi_high:
            trend = 'bearish'  # Sell overbought
            entry = close
            stop = entry * (1 + stop_pct/100)
            target = entry * (1 - target_pct/100)
        else:
            continue
        
        # Simulate trade
        for j in range(i+1, min(i+20, len(data))):
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
    return {
        'trades': len(setups),
        'wins': wins,
        'win_rate': wins / len(setups) * 100,
        'pnl': sum(s['pnl'] for s in setups)
    }

def backtest_ema_crossover(data, fast=9, slow=21, stop_pct=2.0):
    """EMA Crossover strategy"""
    setups = []
    prices = [c['close'] for c in data]
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    
    for i in range(slow+10, len(data) - 20):
        if ema_fast[i] is None or ema_slow[i] is None:
            continue
        
        candle = data[i]
        close = candle['close']
        
        # Check for crossover
        prev_fast = ema_fast[i-1]
        prev_slow = ema_slow[i-1]
        
        if prev_fast < prev_slow and ema_fast[i] > ema_slow[i]:
            trend = 'bullish'
            entry = close
            stop = entry * (1 - stop_pct/100)
            target = entry * 1.04  # 4% target
        elif prev_fast > prev_slow and ema_fast[i] < ema_slow[i]:
            trend = 'bearish'
            entry = close
            stop = entry * (1 + stop_pct/100)
            target = entry * 0.96
        else:
            continue
        
        # Simulate trade
        for j in range(i+1, min(i+20, len(data))):
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
    return {
        'trades': len(setups),
        'wins': wins,
        'win_rate': wins / len(setups) * 100,
        'pnl': sum(s['pnl'] for s in setups)
    }

print("=" * 90)
print("SOL & XRP ALTERNATIVE STRATEGY TESTING")
print("=" * 90)
print()

sol_data = load_data('SOLUSDT', '1h')
xrp_data = load_data('XRPUSDT', '1h')

print(f"SOL data: {len(sol_data)} candles")
print(f"XRP data: {len(xrp_data)} candles")
print()

# Test Mean Reversion
print("MEAN REVERSION STRATEGY (RSI Oversold/Overbought)")
print("-" * 70)
print(f"{'Symbol':<8} {'RSI Low':<10} {'RSI High':<10} {'Stop%':<8} {'Target%':<10} {'Trades':<8} {'Win%':<8} {'P&L%':<10}")
print("-" * 70)

for symbol, data in [('SOL', sol_data), ('XRP', xrp_data)]:
    for rsi_l, rsi_h, stop, target in [(30, 70, 2, 4), (25, 75, 2, 4), (20, 80, 2, 4), (30, 70, 1.5, 3)]:
        result = backtest_mean_reversion(data, rsi_l, rsi_h, stop, target)
        if result:
            print(f"{symbol:<8} {rsi_l:<10} {rsi_h:<10} {stop:<8} {target:<10} {result['trades']:<8} {result['win_rate']:<8.1f} {result['pnl']:<10.2f}")

print()

# Test EMA Crossover
print("EMA CROSSOVER STRATEGY")
print("-" * 70)
print(f"{'Symbol':<8} {'Fast':<8} {'Slow':<8} {'Stop%':<8} {'Trades':<8} {'Win%':<8} {'P&L%':<10}")
print("-" * 70)

for symbol, data in [('SOL', sol_data), ('XRP', xrp_data)]:
    for fast, slow in [(9, 21), (12, 26), (8, 20)]:
        for stop in [2.0, 3.0]:
            result = backtest_ema_crossover(data, fast, slow, stop)
            if result:
                print(f"{symbol:<8} {fast:<8} {slow:<8} {stop:<8} {result['trades']:<8} {result['win_rate']:<8.1f} {result['pnl']:<10.2f}")

print()
print("=" * 90)
print("RECOMMENDATION")
print("=" * 90)
print()
print("Based on the backtests:")
print("- Fibonacci pullback and Breakout strategies showed negative P&L")
print("- Mean reversion and EMA crossover also underperforming")
print()
print("SUGGESTIONS:")
print("1. SOL and XRP may need longer lookback periods (4h or daily)")
print("2. Consider different entry triggers (volume spikes, news events)")
print("3. May need to avoid these pairs until better strategies found")
print("4. Alternatively, use very conservative position sizing")
print()
print("RECOMMENDED ACTION: Skip SOL/XRP for now, focus on BTC/ETH/BNB")
