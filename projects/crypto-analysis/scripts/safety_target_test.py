#!/usr/bin/env python3
"""
Backtest with 10% Safety Discount Target
Target = 10% of original target (0.4x ATR instead of 4x ATR)
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

def backtest_safety_target(symbol, data_1h, safety_discount=0.10):
    """
    Backtest with 10% safety discount on target
    Original: 4x ATR target
    New: 0.4x ATR target (10% of original)
    """
    
    setups = []
    
    for i in range(50, len(data_1h) - 20):
        candle = data_1h[i]
        h1_close = candle['close']
        
        h1_recent = data_1h[i-20:i+1]
        h1_high = max(c['high'] for c in h1_recent)
        h1_low = min(c['low'] for c in h1_recent)
        atr = (h1_high - h1_low) * 0.1
        
        # Trend
        if h1_close > h1_recent[10]['close']:
            trend = 'bullish'
            entry = h1_close
            stop = entry - (atr * 2)  # Keep original stop
            target = entry + (atr * 4 * safety_discount)  # 10% of original target
        else:
            trend = 'bearish'
            entry = h1_close
            stop = entry + (atr * 2)  # Keep original stop
            target = entry - (atr * 4 * safety_discount)  # 10% of original target
        
        # Check outcome
        for j in range(i+1, min(i+21, len(data_1h))):
            future = data_1h[j]
            
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
        'losses': len(setups) - wins,
        'win_rate': wins / len(setups) * 100,
        'pnl': sum(s['pnl'] for s in setups),
        'avg_win': sum(s['pnl'] for s in setups if s['outcome'] == 'win') / wins if wins > 0 else 0,
        'avg_loss': sum(s['pnl'] for s in setups if s['outcome'] == 'loss') / (len(setups) - wins) if len(setups) > wins else 0
    }

print("=" * 90)
print("BACKTEST WITH 10% SAFETY DISCOUNT TARGET")
print("=" * 90)
print()
print("Original target: 4x ATR")
print("New target: 0.4x ATR (10% of original)")
print("Stop: 2x ATR (unchanged)")
print("New R:R ratio: 1:0.2 (very tight)")
print()

for symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']:
    print(f"\n{symbol}:")
    print("-" * 70)
    
    data = load_data(symbol, '1h')
    if not data:
        print("  No data")
        continue
    
    result = backtest_safety_target(symbol, data, safety_discount=0.10)
    
    if result:
        print(f"  Trades: {result['trades']}")
        print(f"  Wins: {result['wins']} ({result['win_rate']:.1f}%)")
        print(f"  Losses: {result['losses']}")
        print(f"  Total P&L: {result['pnl']:+.2f}%")
        print(f"  Avg Win: {result['avg_win']:+.2f}%")
        print(f"  Avg Loss: {result['avg_loss']:+.2f}%")
        
        if result['pnl'] > 0:
            print(f"  ✅ PROFITABLE")
        else:
            print(f"  ❌ UNPROFITABLE")
    else:
        print("  No trades")

print("\n" + "=" * 90)
print("OBSERVATION:")
print("=" * 90)
print()
print("With 10% safety discount:")
print("  - Target is much closer (0.4x ATR vs 4x ATR)")
print("  - Win rate should increase significantly")
print("  - But R:R becomes very poor (1:0.2)")
print("  - Need many more wins to compensate for losses")