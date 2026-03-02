#!/usr/bin/env python3
"""
ETH Profitability Strategy - Different Approach
Test momentum, breakout, and mean reversion strategies
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

def test_momentum_breakout(data_1h, data_1d):
    """Strategy 1: Momentum Breakout
    Enter when price breaks above/below 20-period high/low with volume
    """
    setups = []
    
    for i in range(50, len(data_1h) - 20):
        candle = data_1h[i]
        h1_close = candle['close']
        
        # Lookback for breakout
        lookback = 20
        h1_recent = data_1h[i-lookback:i]
        recent_high = max(c['high'] for c in h1_recent)
        recent_low = min(c['low'] for c in h1_recent)
        
        # Volume check
        recent_volumes = [c['volume'] for c in h1_recent[-5:]]
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        
        if candle['volume'] < avg_volume * 1.2:
            continue
        
        # Breakout detection
        if h1_close > recent_high * 1.005:  # Break above high + 0.5%
            trend = 'bullish'
            entry = h1_close
            stop = recent_low  # Stop at recent swing low
            target = entry + (entry - stop) * 2  # 1:2 R:R
        elif h1_close < recent_low * 0.995:  # Break below low - 0.5%
            trend = 'bearish'
            entry = h1_close
            stop = recent_high  # Stop at recent swing high
            target = entry - (stop - entry) * 2  # 1:2 R:R
        else:
            continue
        
        # Check outcome
        for j in range(i+1, min(i+21, len(data_1h))):
            future = data_1h[j]
            
            if trend == 'bullish':
                if future['low'] <= stop:
                    setups.append({'outcome': 'loss', 'pnl': (stop - entry) / entry * 100})
                    break
                if future['high'] >= target:
                    setups.append({'outcome': 'win', 'pnl': (target - entry) / entry * 100})
                    break
            else:
                if future['high'] >= stop:
                    setups.append({'outcome': 'loss', 'pnl': (entry - stop) / entry * 100})
                    break
                if future['low'] <= target:
                    setups.append({'outcome': 'win', 'pnl': (entry - target) / entry * 100})
                    break
    
    if not setups:
        return None
    
    wins = sum(1 for s in setups if s['outcome'] == 'win')
    return {'trades': len(setups), 'wins': wins, 'win_rate': wins/len(setups)*100, 'pnl': sum(s['pnl'] for s in setups)}

def test_mean_reversion(data_1h, data_1d):
    """Strategy 2: Mean Reversion (RSI Extreme)
    Buy when RSI < 30, Sell when RSI > 70
    """
    setups = []
    
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
    
    for i in range(50, len(data_1h) - 20):
        candle = data_1h[i]
        h1_close = candle['close']
        
        # Calculate RSI
        h1_recent = data_1h[i-20:i+1]
        closes = [c['close'] for c in h1_recent]
        rsi_list = calculate_rsi(closes)
        rsi = rsi_list[-1] if rsi_list[-1] else 50
        
        # Mean reversion entries
        if rsi < 25:  # Oversold - buy
            trend = 'bullish'
            entry = h1_close
            stop = entry * 0.98  # 2% stop
            target = entry * 1.04  # 4% target (2:1 R:R)
        elif rsi > 75:  # Overbought - sell
            trend = 'bearish'
            entry = h1_close
            stop = entry * 1.02  # 2% stop
            target = entry * 0.96  # 4% target (2:1 R:R)
        else:
            continue
        
        # Check outcome
        for j in range(i+1, min(i+21, len(data_1h))):
            future = data_1h[j]
            
            if trend == 'bullish':
                if future['low'] <= stop:
                    setups.append({'outcome': 'loss', 'pnl': (stop - entry) / entry * 100})
                    break
                if future['high'] >= target:
                    setups.append({'outcome': 'win', 'pnl': (target - entry) / entry * 100})
                    break
            else:
                if future['high'] >= stop:
                    setups.append({'outcome': 'loss', 'pnl': (entry - stop) / entry * 100})
                    break
                if future['low'] <= target:
                    setups.append({'outcome': 'win', 'pnl': (entry - target) / entry * 100})
                    break
    
    if not setups:
        return None
    
    wins = sum(1 for s in setups if s['outcome'] == 'win')
    return {'trades': len(setups), 'wins': wins, 'win_rate': wins/len(setups)*100, 'pnl': sum(s['pnl'] for s in setups)}

def test_ema_crossover(data_1h, data_1d):
    """Strategy 3: EMA Crossover
    Buy when price crosses above EMA20, Sell when below
    """
    setups = []
    
    def calculate_ema(prices, period):
        if len(prices) < period:
            return [None] * len(prices)
        multiplier = 2 / (period + 1)
        ema = [sum(prices[:period]) / period]
        for p in prices[period:]:
            ema.append((p * multiplier) + (ema[-1] * (1 - multiplier)))
        return [None] * (period - 1) + ema
    
    for i in range(50, len(data_1h) - 20):
        candle = data_1h[i]
        h1_close = candle['close']
        
        # Calculate EMAs
        h1_recent = data_1h[i-30:i+1]
        closes = [c['close'] for c in h1_recent]
        ema20 = calculate_ema(closes, 20)
        
        if ema20[-2] is None or ema20[-1] is None:
            continue
        
        prev_close = closes[-2]
        prev_ema = ema20[-2]
        curr_ema = ema20[-1]
        
        # Crossover detection
        if prev_close < prev_ema and h1_close > curr_ema:  # Bullish cross
            trend = 'bullish'
            entry = h1_close
            stop = min(c['low'] for c in h1_recent[-5:])  # Recent swing low
            target = entry + (entry - stop) * 2
        elif prev_close > prev_ema and h1_close < curr_ema:  # Bearish cross
            trend = 'bearish'
            entry = h1_close
            stop = max(c['high'] for c in h1_recent[-5:])  # Recent swing high
            target = entry - (stop - entry) * 2
        else:
            continue
        
        # Check outcome
        for j in range(i+1, min(i+21, len(data_1h))):
            future = data_1h[j]
            
            if trend == 'bullish':
                if future['low'] <= stop:
                    setups.append({'outcome': 'loss', 'pnl': (stop - entry) / entry * 100})
                    break
                if future['high'] >= target:
                    setups.append({'outcome': 'win', 'pnl': (target - entry) / entry * 100})
                    break
            else:
                if future['high'] >= stop:
                    setups.append({'outcome': 'loss', 'pnl': (entry - stop) / entry * 100})
                    break
                if future['low'] <= target:
                    setups.append({'outcome': 'win', 'pnl': (entry - target) / entry * 100})
                    break
    
    if not setups:
        return None
    
    wins = sum(1 for s in setups if s['outcome'] == 'win')
    return {'trades': len(setups), 'wins': wins, 'win_rate': wins/len(setups)*100, 'pnl': sum(s['pnl'] for s in setups)}

print("=" * 90)
print("ETH PROFITABILITY STRATEGIES - NEW APPROACHES")
print("=" * 90)
print()

data_1h = load_data('ETHUSDT', '1h')
data_1d = load_data('ETHUSDT', '1d')

if not data_1h or not data_1d:
    print("No data available")
    exit()

strategies = [
    ('Momentum Breakout', test_momentum_breakout),
    ('Mean Reversion (RSI)', test_mean_reversion),
    ('EMA Crossover', test_ema_crossover),
]

print(f"{'Strategy':<25} {'Trades':<8} {'Wins':<6} {'Win %':<8} {'P&L %':<10} {'Status'}")
print("-" * 90)

results = []

for name, strategy_func in strategies:
    result = strategy_func(data_1h, data_1d)
    
    if result:
        marker = "✅" if result['pnl'] > 0 else "❌"
        print(f"{name:<25} {result['trades']:<8} {result['wins']:<6} {result['win_rate']:>6.1f}% {result['pnl']:>+8.2f}% {marker}")
        results.append({'name': name, 'result': result})
    else:
        print(f"{name:<25} No trades")

print("\n" + "=" * 90)
print("BEST STRATEGY FOR ETH:")
print("=" * 90)

if results:
    best = max(results, key=lambda x: x['result']['pnl'])
    print(f"🏆 {best['name']}")
    print(f"   Trades: {best['result']['trades']}")
    print(f"   Win Rate: {best['result']['win_rate']:.1f}%")
    print(f"   P&L: {best['result']['pnl']:+.2f}%")
else:
    print("No profitable strategy found for ETH.")
    print("Recommendation: Skip ETH trading with automated strategies.")