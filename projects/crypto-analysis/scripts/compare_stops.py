#!/usr/bin/env python3
"""
Backtest with Wider Stops (2x ATR)
Compare performance vs original 1.2x/1.5x ATR stops
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

def find_setups_wider_stops(symbol, stop_mult=2.0, target_mult=4.0):
    """Find setups with wider stops"""
    data_1h = load_data(symbol, '1h')
    data_1d = load_data(symbol, '1d')
    
    if not data_1h or not data_1d:
        return []
    
    setups = []
    
    for i in range(50, len(data_1h) - 20):
        candle = data_1h[i]
        timestamp = candle['timestamp']
        
        # Daily trend check
        d_idx = next((j for j, d in enumerate(data_1d) if d['timestamp'] > timestamp), len(data_1d)) - 1
        if d_idx < 20:
            continue
        
        d_recent = data_1d[d_idx-5:d_idx+1]
        d_close = d_recent[-1]['close']
        d_old = d_recent[0]['close']
        d_trend = 'bullish' if d_close > d_recent[2]['close'] else 'bearish'
        
        # Need clear trend
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
        
        # WIDER STOPS (2x ATR)
        if trend == 'bearish':
            stop = h1_close + (atr * stop_mult)
            target = h1_close - (atr * target_mult)
        else:
            stop = h1_close - (atr * stop_mult)
            target = h1_close + (atr * target_mult)
        
        # Check outcome (next 20 candles)
        outcome = 'open'
        exit_price = None
        pnl = 0
        
        for j in range(i+1, min(i+21, len(data_1h))):
            future = data_1h[j]
            
            if trend == 'bearish':
                if future['high'] >= stop:
                    outcome = 'loss'
                    exit_price = stop
                    pnl = (h1_close - stop) / h1_close * 100
                    break
                if future['low'] <= target:
                    outcome = 'win'
                    exit_price = target
                    pnl = (h1_close - target) / h1_close * 100
                    break
            else:
                if future['low'] <= stop:
                    outcome = 'loss'
                    exit_price = stop
                    pnl = (stop - h1_close) / h1_close * 100
                    break
                if future['high'] >= target:
                    outcome = 'win'
                    exit_price = target
                    pnl = (target - h1_close) / h1_close * 100
                    break
        
        if outcome != 'open':
            setups.append({
                'symbol': symbol,
                'date': datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M'),
                'direction': trend,
                'entry': round(h1_close, 2),
                'stop': round(stop, 2),
                'target': round(target, 2),
                'fib': at_fib,
                'outcome': outcome,
                'pnl': round(pnl, 2),
                'stop_distance': round(abs(stop - h1_close) / h1_close * 100, 2)
            })
    
    return setups

def compare_performance():
    """Compare original vs wider stops"""
    
    print("=" * 80)
    print("BACKTEST COMPARISON: ORIGINAL vs WIDER STOPS (2x ATR)")
    print("=" * 80)
    print()
    
    # Original results (from earlier)
    original = {
        'BTCUSDT': {'trades': 3, 'wins': 1, 'losses': 2, 'pnl': -0.12, 'avg_stop': 0.99},
        'ETHUSDT': {'trades': 3, 'wins': 3, 'losses': 0, 'pnl': 4.49, 'avg_stop': 1.45},
        'BNBUSDT': {'trades': 6, 'wins': 1, 'losses': 5, 'pnl': -2.96, 'avg_stop': 0.92}
    }
    
    # Test with wider stops
    print("Testing with 2x ATR stops...")
    print()
    
    for symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']:
        print(f"\n{symbol}:")
        print("-" * 60)
        
        # Original
        orig = original[symbol]
        print(f"ORIGINAL ({orig['avg_stop']:.2f}% avg stop):")
        print(f"  Trades: {orig['trades']}, Wins: {orig['wins']}, Losses: {orig['losses']}")
        print(f"  Win Rate: {orig['wins']/orig['trades']*100:.1f}%")
        print(f"  P&L: {orig['pnl']:+.2f}%")
        
        # New with wider stops
        setups = find_setups_wider_stops(symbol, stop_mult=2.0, target_mult=4.0)
        
        if setups:
            wins = sum(1 for s in setups if s['outcome'] == 'win')
            losses = sum(1 for s in setups if s['outcome'] == 'loss')
            total_pnl = sum(s['pnl'] for s in setups)
            avg_stop = sum(s['stop_distance'] for s in setups) / len(setups)
            
            print(f"\nNEW (2x ATR, {avg_stop:.2f}% avg stop):")
            print(f"  Trades: {len(setups)}, Wins: {wins}, Losses: {losses}")
            print(f"  Win Rate: {wins/len(setups)*100:.1f}%" if setups else "  N/A")
            print(f"  P&L: {total_pnl:+.2f}%")
            
            # Compare
            if total_pnl > orig['pnl']:
                print(f"  ✅ IMPROVEMENT: +{total_pnl - orig['pnl']:.2f}%")
            elif total_pnl < orig['pnl']:
                print(f"  ❌ WORSE: {total_pnl - orig['pnl']:.2f}%")
            else:
                print(f"  ➡️  SAME")
        else:
            print("\nNEW: No trades found with these parameters")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("Wider stops (2x ATR) should:")
    print("  ✅ Reduce false stop-outs from market noise")
    print("  ✅ Improve win rate (fewer losses)")
    print("  ⚠️  Larger loss per losing trade")
    print("  ✅ Better overall P&L if win rate improves enough")
    print()
    print("The 1:2 R:R ratio is maintained (2x stop, 4x target)")

if __name__ == '__main__':
    compare_performance()
