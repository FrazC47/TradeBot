#!/usr/bin/env python3
"""
Find Optimal ATR Stop Multiplier for Each Symbol
Test 1.0x, 1.5x, 2.0x, 2.5x, 3.0x ATR stops
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

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

def backtest_symbol(symbol, stop_mult, target_mult):
    """Backtest a symbol with specific ATR multiples"""
    data_1h = load_data(symbol, '1h')
    data_1d = load_data(symbol, '1d')
    
    if not data_1h or not data_1d:
        return None
    
    setups = []
    
    for i in range(50, len(data_1h) - 20):
        candle = data_1h[i]
        timestamp = candle['timestamp']
        
        # Daily trend
        d_idx = next((j for j, d in enumerate(data_1d) if d['timestamp'] > timestamp), len(data_1d)) - 1
        if d_idx < 20:
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
        
        # Calculate stop and target
        if trend == 'bearish':
            stop = h1_close + (atr * stop_mult)
            target = h1_close - (atr * target_mult)
        else:
            stop = h1_close - (atr * stop_mult)
            target = h1_close + (atr * target_mult)
        
        # Check outcome
        outcome = 'open'
        pnl = 0
        
        for j in range(i+1, min(i+21, len(data_1h))):
            future = data_1h[j]
            
            if trend == 'bearish':
                if future['high'] >= stop:
                    outcome = 'loss'
                    pnl = (h1_close - stop) / h1_close * 100
                    break
                if future['low'] <= target:
                    outcome = 'win'
                    pnl = (h1_close - target) / h1_close * 100
                    break
            else:
                if future['low'] <= stop:
                    outcome = 'loss'
                    pnl = (stop - h1_close) / h1_close * 100
                    break
                if future['high'] >= target:
                    outcome = 'win'
                    pnl = (target - h1_close) / h1_close * 100
                    break
        
        if outcome != 'open':
            setups.append({
                'outcome': outcome,
                'pnl': pnl,
                'stop_distance': abs(stop - h1_close) / h1_close * 100
            })
    
    if not setups:
        return None
    
    wins = sum(1 for s in setups if s['outcome'] == 'win')
    losses = len(setups) - wins
    total_pnl = sum(s['pnl'] for s in setups)
    avg_stop = sum(s['stop_distance'] for s in setups) / len(setups)
    
    return {
        'trades': len(setups),
        'wins': wins,
        'losses': losses,
        'win_rate': wins / len(setups) * 100,
        'pnl': total_pnl,
        'avg_stop': avg_stop
    }

def find_optimal_stops():
    """Find optimal ATR stop for each symbol"""
    
    print("=" * 100)
    print("FINDING OPTIMAL ATR STOP MULTIPLIER FOR EACH SYMBOL")
    print("=" * 100)
    print()
    print("Testing: 1.0x, 1.5x, 2.0x, 2.5x, 3.0x ATR stops")
    print("Target: 2x stop distance (maintaining 1:2 R:R)")
    print()
    
    stop_mults = [1.0, 1.5, 2.0, 2.5, 3.0]
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    
    results = {}
    
    for symbol in symbols:
        print(f"\n{'=' * 100}")
        print(f"{symbol}")
        print(f"{'=' * 100}")
        print(f"{'Stop ATR':<10} {'Trades':<8} {'Wins':<6} {'Losses':<8} {'Win %':<8} {'P&L %':<10} {'Avg Stop':<10} {'Rating'}")
        print("-" * 100)
        
        symbol_results = []
        
        for stop_mult in stop_mults:
            result = backtest_symbol(symbol, stop_mult, stop_mult * 2)
            
            if result:
                # Calculate rating score (PnL * win_rate / 100)
                rating = result['pnl'] * result['win_rate'] / 100
                
                print(f"{stop_mult:<10.1f} {result['trades']:<8} {result['wins']:<6} {result['losses']:<8} "
                      f"{result['win_rate']:>6.1f}% {result['pnl']:>+8.2f}% {result['avg_stop']:>7.2f}% "
                      f"{rating:>8.1f}")
                
                symbol_results.append({
                    'stop_mult': stop_mult,
                    'result': result,
                    'rating': rating
                })
            else:
                print(f"{stop_mult:<10.1f} No trades found")
        
        # Find best
        if symbol_results:
            best = max(symbol_results, key=lambda x: x['rating'])
            results[symbol] = best
            
            print()
            print(f"🏆 OPTIMAL for {symbol}: {best['stop_mult']}x ATR")
            print(f"   Win Rate: {best['result']['win_rate']:.1f}%")
            print(f"   P&L: {best['result']['pnl']:+.2f}%")
            print(f"   Trades: {best['result']['trades']}")
    
    # Summary
    print("\n" + "=" * 100)
    print("FINAL RECOMMENDATIONS")
    print("=" * 100)
    print()
    
    for symbol, best in results.items():
        stop = best['stop_mult']
        target = stop * 2
        print(f"{symbol}:")
        print(f"  Stop: {stop}x ATR")
        print(f"  Target: {target}x ATR")
        print(f"  Expected: {best['result']['win_rate']:.1f}% win rate, {best['result']['pnl']:+.2f}% P&L")
        print()
    
    # Save results
    output = {
        'BTCUSDT': {'stop_atr_mult': results['BTCUSDT']['stop_mult'], 'target_atr_mult': results['BTCUSDT']['stop_mult'] * 2},
        'ETHUSDT': {'stop_atr_mult': results['ETHUSDT']['stop_mult'], 'target_atr_mult': results['ETHUSDT']['stop_mult'] * 2},
        'BNBUSDT': {'stop_atr_mult': results['BNBUSDT']['stop_mult'], 'target_atr_mult': results['BNBUSDT']['stop_mult'] * 2}
    }
    
    with open('backtests/optimal_atr_stops.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("Saved to: backtests/optimal_atr_stops.json")

if __name__ == '__main__':
    find_optimal_stops()
