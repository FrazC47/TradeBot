#!/usr/bin/env python3
"""
BTC Complete Multi-Timeframe Analysis Pipeline
Uses ALL timeframes: 5m, 15m, 1h, 4h, 1d, 1w, 1M
"""

import csv
from pathlib import Path
from datetime import datetime

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')

def load_data(symbol, interval):
    """Load OHLCV data for any timeframe"""
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return [{
            'timestamp': int(r['open_time']),
            'open': float(r['open']),
            'high': float(r['high']),
            'low': float(r['low']),
            'close': float(r['close']),
            'volume': float(r['volume'])
        } for r in reader]

def calculate_ema(prices, period):
    """Calculate EMA"""
    if len(prices) < period:
        return [None] * len(prices)
    multiplier = 2 / (period + 1)
    ema = [sum(prices[:period]) / period]
    for p in prices[period:]:
        ema.append((p * multiplier) + (ema[-1] * (1 - multiplier)))
    return [None] * (period - 1) + ema

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

def calculate_fib_levels(high, low):
    """Calculate Fibonacci levels"""
    diff = high - low
    return {
        '0.0%': high,
        '23.6%': high - diff * 0.236,
        '38.2%': high - diff * 0.382,
        '50.0%': high - diff * 0.5,
        '61.8%': high - diff * 0.618,
        '78.6%': high - diff * 0.786,
        '100.0%': low
    }

def get_trend(data, lookback=10):
    """Determine trend direction"""
    if len(data) < lookback:
        return 'NEUTRAL'
    current = data[-1]['close']
    previous = data[-lookback]['close']
    if current > previous * 1.01:
        return 'BULLISH'
    elif current < previous * 0.99:
        return 'BEARISH'
    return 'NEUTRAL'

print("=" * 90)
print("BTC COMPLETE MULTI-TIMEFRAME ANALYSIS")
print("=" * 90)
print()

# =============================================================================
# STEP 1: LOAD ALL TIMEFRAMES
# =============================================================================
print("STEP 1: LOAD ALL TIMEFRAME DATA")
print("-" * 90)

timeframes = ['5m', '15m', '1h', '4h', '1d', '1w', '1M']
btc_data = {}

for tf in timeframes:
    btc_data[tf] = load_data('BTCUSDT', tf)
    latest = btc_data[tf][-1]
    print(f"✅ {tf:3s}: {len(btc_data[tf]):4d} candles | Close: ${latest['close']:,.2f} | Volume: {latest['volume']:,.2f}")

print()

# =============================================================================
# STEP 2: MULTI-TIMEFRAME TREND ANALYSIS
# =============================================================================
print("STEP 2: MULTI-TIMEFRAME TREND ANALYSIS")
print("-" * 90)

trend_analysis = {}
for tf in timeframes:
    data = btc_data[tf]
    # Use appropriate lookback for each timeframe
    lookback = {'5m': 12, '15m': 8, '1h': 10, '4h': 6, '1d': 5, '1w': 4, '1M': 3}[tf]
    trend = get_trend(data, lookback)
    trend_analysis[tf] = trend
    icon = '📈' if trend == 'BULLISH' else '📉' if trend == 'BEARISH' else '➡️'
    print(f"   {tf:3s}: {icon} {trend}")

# Overall trend alignment
bullish_count = sum(1 for t in trend_analysis.values() if t == 'BULLISH')
bearish_count = sum(1 for t in trend_analysis.values() if t == 'BEARISH')
neutral_count = sum(1 for t in trend_analysis.values() if t == 'NEUTRAL')

print()
print(f"   Trend Alignment: {bullish_count} Bullish | {bearish_count} Bearish | {neutral_count} Neutral")

if bullish_count >= 5:
    overall_trend = "STRONG BULLISH"
elif bearish_count >= 5:
    overall_trend = "STRONG BEARISH"
elif bullish_count >= 3 and bearish_count <= 2:
    overall_trend = "BULLISH"
elif bearish_count >= 3 and bullish_count <= 2:
    overall_trend = "BEARISH"
else:
    overall_trend = "MIXED/NEUTRAL"

print(f"   Overall: {overall_trend}")
print()

# =============================================================================
# STEP 3: HIGHER TIMEFRAME STRUCTURE (1d, 1w, 1M)
# =============================================================================
print("STEP 3: HIGHER TIMEFRAME STRUCTURE")
print("-" * 90)

# Daily structure
daily = btc_data['1d']
d_high = max(c['high'] for c in daily[-20:])
d_low = min(c['low'] for c in daily[-20:])
d_fib = calculate_fib_levels(d_high, d_low)

print("   Daily (20-day) Structure:")
print(f"   High: ${d_high:,.2f} | Low: ${d_low:,.2f}")
print(f"   Key Levels: 61.8%=${d_fib['61.8%']:,.2f}, 50%=${d_fib['50.0%']:,.2f}, 38.2%=${d_fib['38.2%']:,.2f}")

# Weekly structure
weekly = btc_data['1w']
w_high = max(c['high'] for c in weekly[-10:])
w_low = min(c['low'] for c in weekly[-10:])

print()
print("   Weekly (10-week) Structure:")
print(f"   High: ${w_high:,.2f} | Low: ${w_low:,.2f}")

# Monthly structure
monthly = btc_data['1M']
m_high = max(c['high'] for c in monthly[-6:])
m_low = min(c['low'] for c in monthly[-6:])

print()
print("   Monthly (6-month) Structure:")
print(f"   High: ${m_high:,.2f} | Low: ${m_low:,.2f}")
print()

# =============================================================================
# STEP 4: INTERMEDIATE TIMEFRAME ANALYSIS (4h, 1h)
# =============================================================================
print("STEP 4: INTERMEDIATE TIMEFRAME ANALYSIS")
print("-" * 90)

# 4h analysis
h4 = btc_data['4h']
h4_closes = [c['close'] for c in h4]
h4_ema9 = calculate_ema(h4_closes, 9)[-1]
h4_ema21 = calculate_ema(h4_closes, 21)[-1]
h4_atr = calculate_atr(h4)

print("   4-Hour:")
print(f"   EMA 9: ${h4_ema9:,.2f} | EMA 21: ${h4_ema21:,.2f}")
print(f"   ATR: ${h4_atr:,.2f} ({h4_atr/h4[-1]['close']*100:.2f}%)")
print(f"   Trend: {'Above' if h4[-1]['close'] > h4_ema9 else 'Below'} EMA 9")

# 1h analysis
h1 = btc_data['1h']
h1_closes = [c['close'] for c in h1]
h1_ema9 = calculate_ema(h1_closes, 9)[-1]
h1_ema25 = calculate_ema(h1_closes, 25)[-1]
h1_atr = calculate_atr(h1)

print()
print("   1-Hour:")
print(f"   EMA 9: ${h1_ema9:,.2f} | EMA 25: ${h1_ema25:,.2f}")
print(f"   ATR: ${h1_atr:,.2f} ({h1_atr/h1[-1]['close']*100:.2f}%)")
print(f"   Price vs EMA 9: {((h1[-1]['close']/h1_ema9)-1)*100:+.2f}%")
print()

# =============================================================================
# STEP 5: LOWER TIMEFRAME PRECISION (15m, 5m)
# =============================================================================
print("STEP 5: LOWER TIMEFRAME PRECISION")
print("-" * 90)

# 15m analysis
m15 = btc_data['15m']
m15_recent = m15[-20:]
m15_high = max(c['high'] for c in m15_recent)
m15_low = min(c['low'] for c in m15_recent)

print("   15-Minute (last 20 candles):")
print(f"   Range: ${m15_low:,.2f} - ${m15_high:,.2f}")
print(f"   Current: ${m15[-1]['close']:,.2f}")

# 5m analysis
m5 = btc_data['5m']
m5_recent = m5[-20:]
m5_high = max(c['high'] for c in m5_recent)
m5_low = min(c['low'] for c in m5_recent)

print()
print("   5-Minute (last 20 candles):")
print(f"   Range: ${m5_low:,.2f} - ${m5_high:,.2f}")
print(f"   Current: ${m5[-1]['close']:,.2f}")
print()

# =============================================================================
# STEP 6: MULTI-TIMEFRAME CONFLUENCE CHECK
# =============================================================================
print("STEP 6: MULTI-TIMEFRAME CONFLUENCE CHECK")
print("-" * 90)

current_price = h1[-1]['close']

# Check alignment
alignments = []

# 1. Trend alignment
if trend_analysis['1d'] == trend_analysis['4h'] == trend_analysis['1h']:
    alignments.append("✅ Strong trend alignment (1d/4h/1h)")
else:
    alignments.append("⚠️ Mixed trend signals")

# 2. Price vs Daily Fib
for level_name, level_price in d_fib.items():
    if abs(current_price - level_price) / current_price < 0.01:
        alignments.append(f"✅ Price at Daily Fib {level_name} (${level_price:,.2f})")
        break

# 3. EMA alignment on 1h
if h1[-1]['close'] > h1_ema9 > h1_ema25:
    alignments.append("✅ Bullish EMA stack (Price > EMA9 > EMA25)")
elif h1[-1]['close'] < h1_ema9 < h1_ema25:
    alignments.append("✅ Bearish EMA stack (Price < EMA9 < EMA25)")
else:
    alignments.append("⚠️ EMAs not aligned")

# 4. Volume check
h1_volume = h1[-1]['volume']
h1_vol_avg = sum(c['volume'] for c in h1[-20:]) / 20
if h1_volume > h1_vol_avg * 1.2:
    alignments.append(f"✅ High volume ({h1_volume/h1_vol_avg:.1f}x average)")

for alignment in alignments:
    print(f"   {alignment}")
print()

# =============================================================================
# STEP 7: TRADE SETUP IDENTIFICATION
# =============================================================================
print("STEP 7: TRADE SETUP IDENTIFICATION")
print("-" * 90)

# Check for Fibonacci pullback setup on 1h
h1_recent = h1[-21:-1]
h1_swing_high = max(c['high'] for c in h1_recent)
h1_swing_low = min(c['low'] for c in h1_recent)
h1_fib = calculate_fib_levels(h1_swing_high, h1_swing_low)

setup_found = False
setup_direction = None

# Check if price is at a Fib level
for level_name, level_price in h1_fib.items():
    if abs(current_price - level_price) / current_price < 0.01:
        # Check trend alignment
        if trend_analysis['1d'] == 'BULLISH' and trend_analysis['1h'] in ['BULLISH', 'NEUTRAL']:
            setup_found = True
            setup_direction = 'LONG'
            entry_fib = level_name
            break
        elif trend_analysis['1d'] == 'BEARISH' and trend_analysis['1h'] in ['BEARISH', 'NEUTRAL']:
            setup_found = True
            setup_direction = 'SHORT'
            entry_fib = level_name
            break

if setup_found:
    print(f"   🎯 SETUP FOUND: {setup_direction}")
    print(f"   Entry Fib Level: {entry_fib}")
    print(f"   Entry Price: ${current_price:,.2f}")
    
    # Calculate stops and targets using 1h ATR
    if setup_direction == 'LONG':
        stop = current_price - (h1_atr * 3.0)
        target = current_price + (h1_atr * 6.0)
    else:
        stop = current_price + (h1_atr * 3.0)
        target = current_price - (h1_atr * 6.0)
    
    risk = abs(current_price - stop) / current_price * 100
    reward = abs(target - current_price) / current_price * 100
    
    print(f"   Stop: ${stop:,.2f} ({risk:.2f}%)")
    print(f"   Target: ${target:,.2f} ({reward:.2f}%)")
    print(f"   R:R Ratio: 1:{reward/risk:.1f}")
    
    # Confluence score
    confluence = 0
    if 'Strong trend alignment' in str(alignments): confluence += 2
    if 'Price at Daily Fib' in str(alignments): confluence += 2
    if 'EMA stack' in str(alignments): confluence += 1
    if 'High volume' in str(alignments): confluence += 1
    
    print(f"   Confluence Score: {confluence}/6")
    
    if confluence >= 4:
        print(f"   Quality: ⭐⭐⭐ HIGH")
    elif confluence >= 2:
        print(f"   Quality: ⭐⭐ MEDIUM")
    else:
        print(f"   Quality: ⭐ LOW")
else:
    print("   ❌ No setup found")
    print("   Reasons:")
    if trend_analysis['1d'] != trend_analysis['1h']:
        print("   - Trend mismatch between daily and hourly")
    if not any(abs(current_price - p) / current_price < 0.01 for p in h1_fib.values()):
        print("   - Price not at key Fibonacci level")

print()
print("=" * 90)
print("ANALYSIS COMPLETE")
print("=" * 90)
