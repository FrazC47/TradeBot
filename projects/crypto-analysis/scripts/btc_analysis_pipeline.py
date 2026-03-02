#!/usr/bin/env python3
"""
BTC Analysis Pipeline - Sequential Step-by-Step Process
Shows exactly what happens after data is pulled
"""

import csv
from pathlib import Path
from datetime import datetime

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')

def load_data(symbol, interval):
    """STEP 1: Load raw OHLCV data from CSV"""
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        data = []
        for r in reader:
            data.append({
                'timestamp': int(r['open_time']),
                'open': float(r['open']),
                'high': float(r['high']),
                'low': float(r['low']),
                'close': float(r['close']),
                'volume': float(r['volume'])
            })
    return data

print("=" * 80)
print("BTC ANALYSIS PIPELINE - STEP BY STEP")
print("=" * 80)
print()

# =============================================================================
# STEP 1: LOAD RAW DATA
# =============================================================================
print("STEP 1: LOAD RAW OHLCV DATA")
print("-" * 80)

btc_1h = load_data('BTCUSDT', '1h')
btc_1d = load_data('BTCUSDT', '1d')

print(f"✅ Loaded {len(btc_1h)} 1h candles")
print(f"✅ Loaded {len(btc_1d)} 1d candles")
print(f"   Time range: {datetime.fromtimestamp(btc_1h[0]['timestamp']/1000)} to {datetime.fromtimestamp(btc_1h[-1]['timestamp']/1000)}")
print()

# Show latest candle
latest = btc_1h[-1]
print(f"   Latest 1h candle:")
print(f"   Open: ${latest['open']:,.2f}")
print(f"   High: ${latest['high']:,.2f}")
print(f"   Low:  ${latest['low']:,.2f}")
print(f"   Close: ${latest['close']:,.2f}")
print(f"   Volume: {latest['volume']:,.2f}")
print()

# =============================================================================
# STEP 2: CALCULATE INDICATORS
# =============================================================================
print("STEP 2: CALCULATE TECHNICAL INDICATORS")
print("-" * 80)

# 2.1 Calculate EMAs
def calculate_ema(prices, period):
    multiplier = 2 / (period + 1)
    ema = [sum(prices[:period]) / period]
    for p in prices[period:]:
        ema.append((p * multiplier) + (ema[-1] * (1 - multiplier)))
    return [None] * (period - 1) + ema

closes = [c['close'] for c in btc_1h]
ema_9 = calculate_ema(closes, 9)
ema_25 = calculate_ema(closes, 25)

print(f"✅ EMA 9:  ${ema_9[-1]:,.2f}")
print(f"✅ EMA 25: ${ema_25[-1]:,.2f}")

# 2.2 Calculate ATR
def calculate_atr(data, period=14):
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

atr = calculate_atr(btc_1h)
print(f"✅ ATR(14): ${atr:,.2f} ({atr/latest['close']*100:.2f}%)")

# 2.3 Calculate RSI
def calculate_rsi(prices, period=14):
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

rsi = calculate_rsi(closes)
print(f"✅ RSI(14): {rsi:.1f}")
print()

# =============================================================================
# STEP 3: CALCULATE FIBONACCI LEVELS
# =============================================================================
print("STEP 3: CALCULATE FIBONACCI RETRACEMENT LEVELS")
print("-" * 80)

# Use last 20 periods for Fibonacci
recent = btc_1h[-21:-1]
fib_high = max(c['high'] for c in recent)
fib_low = min(c['low'] for c in recent)
fib_diff = fib_high - fib_low

fib_levels = {
    '0.0%': fib_high,
    '23.6%': fib_high - fib_diff * 0.236,
    '38.2%': fib_high - fib_diff * 0.382,
    '50.0%': fib_high - fib_diff * 0.5,
    '61.8%': fib_high - fib_diff * 0.618,
    '78.6%': fib_high - fib_diff * 0.786,
    '100.0%': fib_low
}

print(f"   Swing High: ${fib_high:,.2f}")
print(f"   Swing Low:  ${fib_low:,.2f}")
print()
print("   Fibonacci Levels:")
for level, price in fib_levels.items():
    distance = abs(latest['close'] - price) / latest['close'] * 100
    marker = " ← CURRENT PRICE" if distance < 1 else ""
    print(f"   {level}: ${price:,.2f}{marker}")
print()

# =============================================================================
# STEP 4: DETERMINE TREND
# =============================================================================
print("STEP 4: DETERMINE TREND DIRECTION")
print("-" * 80)

# 4.1 1h trend (10-period comparison)
h1_trend_up = latest['close'] > btc_1h[-10]['close']
h1_trend_down = latest['close'] < btc_1h[-10]['close']

# 4.2 Daily trend (5-day comparison)
d_trend_up = btc_1d[-1]['close'] > btc_1d[-6]['close'] if len(btc_1d) >= 6 else True
d_trend_down = btc_1d[-1]['close'] < btc_1d[-6]['close'] if len(btc_1d) >= 6 else False

print(f"   1h Trend: {'📈 BULLISH' if h1_trend_up else '📉 BEARISH' if h1_trend_down else '➡️ NEUTRAL'}")
print(f"   1d Trend: {'📈 BULLISH' if d_trend_up else '📉 BEARISH' if d_trend_down else '➡️ NEUTRAL'}")
print()

# =============================================================================
# STEP 5: CHECK ENTRY CONDITIONS
# =============================================================================
print("STEP 5: CHECK ENTRY CONDITIONS (Fibonacci Pullback Strategy)")
print("-" * 80)

# Check if price is near a Fib level
fib_tolerance = 0.01  # 1%
at_fib = None
for level_name, level_price in fib_levels.items():
    if abs(latest['close'] - level_price) / latest['close'] < fib_tolerance:
        at_fib = level_name
        break

print(f"   Condition 1: Price at Fibonacci level?")
if at_fib:
    print(f"   ✅ YES - Price is at {at_fib} level")
else:
    print(f"   ❌ NO - Price is not near any Fib level")

print(f"   Condition 2: Daily trend aligned?")
if d_trend_up or d_trend_down:
    print(f"   ✅ YES - Daily trend is clear")
else:
    print(f"   ❌ NO - Daily trend is neutral")

print(f"   Condition 3: RSI not overbought/oversold?")
if 30 < rsi < 70:
    print(f"   ✅ YES - RSI is {rsi:.1f} (neutral zone)")
else:
    print(f"   ⚠️ NO - RSI is {rsi:.1f} (extreme zone)")
print()

# =============================================================================
# STEP 6: CALCULATE TRADE PARAMETERS
# =============================================================================
print("STEP 6: CALCULATE TRADE PARAMETERS")
print("-" * 80)

if at_fib and (d_trend_up or d_trend_down):
    entry = latest['close']
    
    if d_trend_up:
        direction = "LONG"
        stop = entry - (atr * 3.0)
        target = entry + (atr * 6.0)
    else:
        direction = "SHORT"
        stop = entry + (atr * 3.0)
        target = entry - (atr * 6.0)
    
    risk = abs(entry - stop) / entry * 100
    reward = abs(target - entry) / entry * 100
    rr_ratio = reward / risk if risk > 0 else 0
    
    print(f"   🎯 SETUP FOUND!")
    print(f"   Direction: {direction}")
    print(f"   Entry: ${entry:,.2f}")
    print(f"   Stop: ${stop:,.2f} ({risk:.2f}%)")
    print(f"   Target: ${target:,.2f} ({reward:.2f}%)")
    print(f"   R:R Ratio: 1:{rr_ratio:.1f}")
    print()
    
    # Position sizing
    account_size = 10000  # Example
    risk_per_trade = 0.03  # 3%
    position_size = (account_size * risk_per_trade) / risk
    
    print(f"   Position Sizing:")
    print(f"   Account: ${account_size:,.2f}")
    print(f"   Risk per trade: {risk_per_trade*100:.0f}%")
    print(f"   Position size: ${position_size:,.2f}")
else:
    print("   ❌ No setup found - conditions not met")
print()

# =============================================================================
# STEP 7: SUMMARY
# =============================================================================
print("=" * 80)
print("ANALYSIS SUMMARY")
print("=" * 80)
print(f"   Symbol: BTCUSDT")
print(f"   Price: ${latest['close']:,.2f}")
print(f"   Trend: 1h {'Bullish' if h1_trend_up else 'Bearish'}, 1d {'Bullish' if d_trend_up else 'Bearish'}")
print(f"   RSI: {rsi:.1f}")
print(f"   ATR: ${atr:,.2f}")
print(f"   Setup: {'YES' if at_fib else 'NO'}")
print("=" * 80)
