#!/usr/bin/env python3
"""
BNB Deep Optimization - Test More Variations
Try different Fib levels, RSI ranges, volume filters, EMA distances
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from itertools import product

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
    if len(prices) < period:
        return [None] * len(prices)
    multiplier = 2 / (period + 1)
    ema = [sum(prices[:period]) / period]
    for p in prices[period:]:
        ema.append((p * multiplier) + (ema[-1] * (1 - multiplier)))
    return [None] * (period - 1) + ema

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

def backtest_bnb_variant(data_1h, data_1d, params):
    """Backtest BNB with specific parameters"""
    
    setups = []
    
    for i in range(100, len(data_1h) - 20):
        candle = data_1h[i]
        timestamp = candle['timestamp']
        
        # Daily trend with EMA distance check
        d_idx = next((j for j, d in enumerate(data_1d) if d['timestamp'] > timestamp), len(data_1d)) - 1
        if d_idx < 20:
            continue
        
        d_closes = [d['close'] for d in data_1d[:d_idx+1]]
        d_ema20 = calculate_ema(d_closes, 20)
        
        if d_ema20[-1] is None:
            continue
        
        d_close = data_1d[d_idx]['close']
        ema_dist = abs(d_close - d_ema20[-1]) / d_close * 100
        
        # Check trend and EMA distance
        if d_close < d_ema20[-1]:
            trend = 'bearish'
        elif d_close > d_ema20[-1]:
            trend = 'bullish'
        else:
            continue
        
        # EMA distance filter
        if ema_dist < params['ema_dist_min']:
            continue
        
        # 1h context
        h1_recent = data_1h[i-20:i+1]
        h1_high = max(c['high'] for c in h1_recent)
        h1_low = min(c['low'] for c in h1_recent)
        h1_close = candle['close']
        
        # RSI check
        h1_closes = [c['close'] for c in h1_recent]
        rsi_list = calculate_rsi(h1_closes, params['rsi_period'])
        rsi = rsi_list[-1] if rsi_list[-1] else 50
        
        if trend == 'bullish' and rsi > params['rsi_long_max']:
            continue
        if trend == 'bearish' and rsi < params['rsi_short_min']:
            continue
        
        # Volume check
        recent_volumes = [c['volume'] for c in h1_recent[-20:]]
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        if candle['volume'] < avg_volume * params['volume_min']:
            continue
        
        # Fibonacci
        diff = h1_high - h1_low
        fib_levels = {}
        for level in params['fib_levels']:
            if level == '0.618':
                fib_levels[level] = h1_high - diff * 0.618
            elif level == '0.5':
                fib_levels[level] = h1_high - diff * 0.5
            elif level == '0.382':
                fib_levels[level] = h1_high - diff * 0.382
        
        at_fib = None
        for level_name, level_price in fib_levels.items():
            if abs(h1_close - level_price) / h1_close < params['fib_tolerance']:
                at_fib = level_name
                break
        
        if not at_fib:
            continue
        
        # Calculate ATR
        atr = (h1_high - h1_low) * 0.1
        
        # Calculate stop and target
        if trend == 'bearish':
            stop = h1_close + (atr * params['stop_mult'])
            target = h1_close - (atr * params['target_mult'])
        else:
            stop = h1_close - (atr * params['stop_mult'])
            target = h1_close + (atr * params['target_mult'])
        
        # Proportional minimum stop
        min_stop_pct = 0.5 * (params['stop_mult'] / 2.0)
        stop_distance = abs(stop - h1_close) / h1_close * 100
        if stop_distance < min_stop_pct:
            continue
        
        # Check outcome
        outcome = 'open'
        pnl = 0
        
        for j in range(i+1, min(i+params['holding_periods']+1, len(data_1h))):
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
            setups.append({'outcome': outcome, 'pnl': pnl})
    
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

def optimize_bnb():
    """Run comprehensive BNB optimization"""
    
    print("=" * 100)
    print("BNB DEEP OPTIMIZATION")
    print("=" * 100)
    print()
    
    # Load data
    data_1h = load_data('BNBUSDT', '1h')
    data_1d = load_data('BNBUSDT', '1d')
    
    if not data_1h or not data_1d:
        print("No data available")
        return
    
    # Parameter variations to test
    param_grid = {
        'fib_levels': [['0.5'], ['0.618'], ['0.5', '0.618']],
        'fib_tolerance': [0.01, 0.015],
        'stop_mult': [1.5, 2.0, 2.5],
        'target_mult': [3.0, 4.0, 5.0],
        'ema_dist_min': [1.0, 1.5, 2.0],
        'rsi_long_max': [60, 65, 70],
        'rsi_short_min': [30, 35, 40],
        'rsi_period': [14],
        'volume_min': [0.8, 1.0, 1.2],
        'holding_periods': [16, 20, 24]
    }
    
    # Test top combinations
    test_combinations = [
        {'name': 'Original', 'fib_levels': ['0.5'], 'fib_tolerance': 0.01, 'stop_mult': 2.0, 'target_mult': 4.0, 
         'ema_dist_min': 2.0, 'rsi_long_max': 65, 'rsi_short_min': 35, 'rsi_period': 14, 'volume_min': 1.2, 'holding_periods': 16},
        
        {'name': 'Wider Fib', 'fib_levels': ['0.5', '0.618'], 'fib_tolerance': 0.015, 'stop_mult': 2.0, 'target_mult': 4.0,
         'ema_dist_min': 2.0, 'rsi_long_max': 65, 'rsi_short_min': 35, 'rsi_period': 14, 'volume_min': 1.2, 'holding_periods': 16},
        
        {'name': 'Tighter EMA', 'fib_levels': ['0.5'], 'fib_tolerance': 0.01, 'stop_mult': 2.0, 'target_mult': 4.0,
         'ema_dist_min': 1.5, 'rsi_long_max': 65, 'rsi_short_min': 35, 'rsi_period': 14, 'volume_min': 1.2, 'holding_periods': 16},
        
        {'name': 'Conservative RSI', 'fib_levels': ['0.5'], 'fib_tolerance': 0.01, 'stop_mult': 2.0, 'target_mult': 4.0,
         'ema_dist_min': 2.0, 'rsi_long_max': 60, 'rsi_short_min': 40, 'rsi_period': 14, 'volume_min': 1.2, 'holding_periods': 16},
        
        {'name': 'Longer Hold', 'fib_levels': ['0.5'], 'fib_tolerance': 0.01, 'stop_mult': 2.0, 'target_mult': 4.0,
         'ema_dist_min': 2.0, 'rsi_long_max': 65, 'rsi_short_min': 35, 'rsi_period': 14, 'volume_min': 1.2, 'holding_periods': 24},
        
        {'name': 'Higher Volume', 'fib_levels': ['0.5'], 'fib_tolerance': 0.01, 'stop_mult': 2.0, 'target_mult': 4.0,
         'ema_dist_min': 2.0, 'rsi_long_max': 65, 'rsi_short_min': 35, 'rsi_period': 14, 'volume_min': 1.5, 'holding_periods': 16},
        
        {'name': 'Wider Stop', 'fib_levels': ['0.5'], 'fib_tolerance': 0.01, 'stop_mult': 2.5, 'target_mult': 5.0,
         'ema_dist_min': 2.0, 'rsi_long_max': 65, 'rsi_short_min': 35, 'rsi_period': 14, 'volume_min': 1.2, 'holding_periods': 20},
        
        {'name': 'Tighter Stop', 'fib_levels': ['0.5'], 'fib_tolerance': 0.01, 'stop_mult': 1.5, 'target_mult': 3.0,
         'ema_dist_min': 2.0, 'rsi_long_max': 65, 'rsi_short_min': 35, 'rsi_period': 14, 'volume_min': 1.2, 'holding_periods': 16},
        
        {'name': '0.618 Only', 'fib_levels': ['0.618'], 'fib_tolerance': 0.01, 'stop_mult': 2.0, 'target_mult': 4.0,
         'ema_dist_min': 2.0, 'rsi_long_max': 65, 'rsi_short_min': 35, 'rsi_period': 14, 'volume_min': 1.2, 'holding_periods': 16},
    ]
    
    results = []
    
    print(f"Testing {len(test_combinations)} BNB strategy variations...")
    print()
    
    for combo in test_combinations:
        name = combo.pop('name')
        result = backtest_bnb_variant(data_1h, data_1d, combo)
        
        if result:
            results.append({
                'name': name,
                'params': combo,
                'result': result
            })
    
    # Sort by P&L
    results.sort(key=lambda x: x['result']['pnl'], reverse=True)
    
    print(f"{'Rank':<6} {'Strategy':<20} {'Trades':<8} {'Wins':<6} {'Win %':<8} {'P&L %':<10} {'Avg W':<8} {'Avg L':<8}")
    print("-" * 100)
    
    for i, r in enumerate(results[:10], 1):
        res = r['result']
        marker = "🏆" if i == 1 else "✅" if res['pnl'] > 0 else ""
        print(f"{i:<6} {r['name']:<20} {res['trades']:<8} {res['wins']:<6} "
              f"{res['win_rate']:>6.1f}% {res['pnl']:>+8.2f}% {res['avg_win']:>+6.2f}% {res['avg_loss']:>+6.2f}% {marker}")
    
    # Best result
    if results:
        best = results[0]
        print()
        print("=" * 100)
        print(f"🏆 BEST BNB STRATEGY: {best['name']}")
        print("=" * 100)
        print(f"P&L: {best['result']['pnl']:+.2f}%")
        print(f"Win Rate: {best['result']['win_rate']:.1f}%")
        print(f"Trades: {best['result']['trades']}")
        print()
        print("Parameters:")
        for k, v in best['params'].items():
            print(f"  {k}: {v}")
        
        # Save
        with open('backtests/bnb_optimized.json', 'w') as f:
            json.dump(best, f, indent=2)
        
        print()
        print("Saved to: backtests/bnb_optimized.json")

if __name__ == '__main__':
    optimize_bnb()
