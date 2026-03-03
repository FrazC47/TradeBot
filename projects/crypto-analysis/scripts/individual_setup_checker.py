#!/usr/bin/env python3
"""
Individual Setup Checker - All 5 Coins with Unique Strategies
BTC: Fibonacci Pullback | ETH: Momentum Breakout | BNB: Extreme Selectivity
SOL: EMA Crossover | XRP: EMA Crossover
"""

import json
import csv
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

def calculate_ema(prices, period):
    """Calculate EMA"""
    if len(prices) < period:
        return [None] * len(prices)
    multiplier = 2 / (period + 1)
    ema = [sum(prices[:period]) / period]
    for p in prices[period:]:
        ema.append((p * multiplier) + (ema[-1] * (1 - multiplier)))
    return [None] * (period - 1) + ema

def calculate_fib_levels(high, low):
    """Calculate Fibonacci retracement levels"""
    diff = high - low
    return {
        '0.618': high - diff * 0.618,
        '0.5': high - diff * 0.5,
        '0.382': high - diff * 0.382
    }

def calculate_atr(data, period=14):
    """Calculate ATR"""
    if len(data) < period:
        return (data[-1]['high'] - data[-1]['low']) * 0.1
    tr_sum = 0
    for i in range(-period, 0):
        high = data[i]['high']
        low = data[i]['low']
        prev_close = data[i-1]['close']
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_sum += tr
    return tr_sum / period

def check_btc_setup(data_1h, data_1d):
    """BTC: Fibonacci Pullback Strategy"""
    if len(data_1h) < 50 or len(data_1d) < 10:
        return None
    
    latest = data_1h[-1]
    close = latest['close']
    
    # Daily trend
    d_close = data_1d[-1]['close']
    d_old = data_1d[-6]['close'] if len(data_1d) >= 6 else data_1d[0]['close']
    
    if d_close > d_old:
        trend = 'bullish'
    elif d_close < d_old:
        trend = 'bearish'
    else:
        return None
    
    # Fibonacci levels
    recent = data_1h[-21:-1]
    h = max(c['high'] for c in recent)
    l = min(c['low'] for c in recent)
    fibs = calculate_fib_levels(h, l)
    
    # Check Fib levels
    at_fib = None
    for level_name, level_price in fibs.items():
        if abs(close - level_price) / close < 0.01:
            at_fib = level_name
            break
    
    if not at_fib:
        return None
    
    # Calculate ATR
    atr = calculate_atr(data_1h)
    
    if trend == 'bullish':
        stop = close - (atr * 3.0)
        target = close + (atr * 6.0)
    else:
        stop = close + (atr * 3.0)
        target = close - (atr * 6.0)
    
    return {
        'symbol': 'BTCUSDT',
        'direction': 'LONG' if trend == 'bullish' else 'SHORT',
        'entry': close,
        'stop': stop,
        'target': target,
        'strategy': 'Fibonacci Pullback',
        'setup_type': f'At {at_fib} Fib'
    }

def check_eth_setup(data_1h):
    """ETH: Momentum Breakout Strategy"""
    if len(data_1h) < 50:
        return None
    
    latest = data_1h[-1]
    close = latest['close']
    
    # 20-period high/low
    recent = data_1h[-21:-1]
    recent_high = max(c['high'] for c in recent)
    recent_low = min(c['low'] for c in recent)
    
    buffer = 0.005
    trend = None
    
    if close > recent_high * (1 + buffer):
        trend = 'bullish'
        stop = recent_low
        target = close + (close - stop) * 2
    elif close < recent_low * (1 - buffer):
        trend = 'bearish'
        stop = recent_high
        target = close - (stop - close) * 2
    
    if not trend:
        return None
    
    return {
        'symbol': 'ETHUSDT',
        'direction': 'LONG' if trend == 'bullish' else 'SHORT',
        'entry': close,
        'stop': stop,
        'target': target,
        'strategy': 'Momentum Breakout',
        'setup_type': '20-period breakout'
    }

def check_sol_setup(data_1h):
    """SOL: EMA Crossover Strategy"""
    if len(data_1h) < 30:
        return None
    
    prices = [c['close'] for c in data_1h]
    ema_12 = calculate_ema(prices, 12)
    ema_26 = calculate_ema(prices, 26)
    
    if ema_12[-1] is None or ema_26[-1] is None:
        return None
    
    # Check for crossover
    prev_12 = ema_12[-2]
    prev_26 = ema_26[-2]
    curr_12 = ema_12[-1]
    curr_26 = ema_26[-1]
    
    trend = None
    if prev_12 < prev_26 and curr_12 > curr_26:
        trend = 'bullish'
    elif prev_12 > prev_26 and curr_12 < curr_26:
        trend = 'bearish'
    
    if not trend:
        return None
    
    latest = data_1h[-1]
    close = latest['close']
    
    # Fixed percentage stop/target
    if trend == 'bullish':
        stop = close * 0.97  # 3% stop
        target = close * 1.04  # 4% target
    else:
        stop = close * 1.03
        target = close * 0.96
    
    return {
        'symbol': 'SOLUSDT',
        'direction': 'LONG' if trend == 'bullish' else 'SHORT',
        'entry': close,
        'stop': stop,
        'target': target,
        'strategy': 'EMA Crossover (12/26)',
        'setup_type': 'EMA crossover',
        'position_factor': 0.5
    }

def check_xrp_setup(data_1h):
    """XRP: EMA Crossover Strategy"""
    if len(data_1h) < 25:
        return None
    
    prices = [c['close'] for c in data_1h]
    ema_9 = calculate_ema(prices, 9)
    ema_21 = calculate_ema(prices, 21)
    
    if ema_9[-1] is None or ema_21[-1] is None:
        return None
    
    # Check for crossover
    prev_9 = ema_9[-2]
    prev_21 = ema_21[-2]
    curr_9 = ema_9[-1]
    curr_21 = ema_21[-1]
    
    trend = None
    if prev_9 < prev_21 and curr_9 > curr_21:
        trend = 'bullish'
    elif prev_9 > prev_21 and curr_9 < curr_21:
        trend = 'bearish'
    
    if not trend:
        return None
    
    latest = data_1h[-1]
    close = latest['close']
    
    # Fixed percentage stop/target
    if trend == 'bullish':
        stop = close * 0.97
        target = close * 1.04
    else:
        stop = close * 1.03
        target = close * 0.96
    
    return {
        'symbol': 'XRPUSDT',
        'direction': 'LONG' if trend == 'bullish' else 'SHORT',
        'entry': close,
        'stop': stop,
        'target': target,
        'strategy': 'EMA Crossover (9/21)',
        'setup_type': 'EMA crossover',
        'position_factor': 0.5
    }

print("=" * 90)
print("INDIVIDUAL SETUP CHECKER - ALL 5 COINS")
print("=" * 90)
print()

symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT']
setups_found = []

for symbol in symbols:
    data_1h = load_data(symbol, '1h')
    
    if not data_1h:
        print(f"{symbol}: No data available")
        continue
    
    setup = None
    
    if symbol == 'BTCUSDT':
        data_1d = load_data(symbol, '1d')
        setup = check_btc_setup(data_1h, data_1d)
    elif symbol == 'ETHUSDT':
        setup = check_eth_setup(data_1h)
    elif symbol == 'SOLUSDT':
        setup = check_sol_setup(data_1h)
    elif symbol == 'XRPUSDT':
        setup = check_xrp_setup(data_1h)
    
    if setup:
        print(f"🎯 {setup['symbol']} {setup['direction']}")
        print(f"   Strategy: {setup['strategy']}")
        print(f"   Setup: {setup['setup_type']}")
        print(f"   Entry: ${setup['entry']:.2f}")
        print(f"   Stop: ${setup['stop']:.2f} ({abs(setup['stop']-setup['entry'])/setup['entry']*100:.2f}%)")
        print(f"   Target: ${setup['target']:.2f} ({abs(setup['target']-setup['entry'])/setup['entry']*100:.2f}%)")
        if 'position_factor' in setup:
            print(f"   Position: {setup['position_factor']*100:.0f}% of normal size")
        print()
        setups_found.append(setup)
    else:
        print(f"{symbol}: No setup found")

print("=" * 90)
print(f"Total setups found: {len(setups_found)}")
print("=" * 90)

# Generate detailed reports with charts for each setup
if setups_found:
    print("\n" + "=" * 90)
    print("GENERATING TRADE REPORTS WITH CHARTS...")
    print("=" * 90)
    
    import sys
    sys.path.insert(0, '/root/.openclaw/workspace/projects/crypto-analysis')
    from trade_reporter import report_trade
    
    for setup in setups_found:
        # Format setup for reporter
        report_setup = {
            'direction': setup['direction'],
            'entry': setup['entry'],
            'entry_low': setup['entry'] * 0.995,
            'entry_high': setup['entry'] * 1.005,
            'stop': setup['stop'],
            'target': setup['target'],
            'strategy': setup['strategy'],
            'position_factor': setup.get('position_factor', 1.0)
        }
        
        try:
            result = report_trade(setup['symbol'], report_setup)
            print(f"\n✅ Report generated for {setup['symbol']}")
        except Exception as e:
            print(f"\n⚠️  Could not generate report for {setup['symbol']}: {e}")
