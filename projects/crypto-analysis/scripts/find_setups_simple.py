#!/usr/bin/env python3
"""
Simple Historical Setup Finder
Find trade setups using 1h data with 4h/daily context
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
OUTPUT_DIR = Path('/root/.openclaw/workspace/backtest_results')

def load_data(symbol, interval):
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    if not filepath.exists():
        return []
    
    data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'timestamp': int(row['open_time']),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume'])
            })
    return data

def find_setups_simple(symbol):
    """Find setups using simple rules"""
    print(f"\nAnalyzing {symbol}...")
    
    # Load data
    data_1h = load_data(symbol, '1h')
    data_4h = load_data(symbol, '4h')
    data_1d = load_data(symbol, '1d')
    
    if not data_1h or not data_4h or not data_1d:
        return []
    
    print(f"  1h: {len(data_1h)} candles")
    print(f"  4h: {len(data_4h)} candles")
    print(f"  1d: {len(data_1d)} candles")
    
    setups = []
    
    # Look at every 4th 1h candle (to avoid overlap)
    for i in range(100, len(data_1h) - 20, 4):
        candle = data_1h[i]
        timestamp = candle['timestamp']
        
        # Get 1h context (20 candles)
        h1_recent = data_1h[i-20:i+1]
        h1_high = max(c['high'] for c in h1_recent)
        h1_low = min(c['low'] for c in h1_recent)
        h1_close = candle['close']
        
        # Simple trend: compare to 20-candle ago
        h1_old = h1_recent[0]['close']
        h1_trend = 'bullish' if h1_close > h1_old else 'bearish'
        
        # Get corresponding 4h candle
        h4_idx = None
        for j, h4 in enumerate(data_4h):
            if h4['timestamp'] <= timestamp:
                h4_idx = j
        
        if h4_idx is None or h4_idx < 10:
            continue
        
        h4_recent = data_4h[h4_idx-10:h4_idx+1]
        h4_close = h4_recent[-1]['close']
        h4_old = h4_recent[0]['close']
        h4_trend = 'bullish' if h4_close > h4_old else 'bearish'
        
        # Get corresponding 1d candle
        d1_idx = None
        for j, d1 in enumerate(data_1d):
            if d1['timestamp'] <= timestamp:
                d1_idx = j
        
        if d1_idx is None or d1_idx < 5:
            continue
        
        d1_recent = data_1d[d1_idx-5:d1_idx+1]
        d1_close = d1_recent[-1]['close']
        d1_old = d1_recent[0]['close']
        d1_trend = 'bullish' if d1_close > d1_old else 'bearish'
        
        # Determine direction - REQUIRE ALL 3 timeframes to align
        if h1_trend == h4_trend == d1_trend == 'bullish':
            direction = 'bullish'
        elif h1_trend == h4_trend == d1_trend == 'bearish':
            direction = 'bearish'
        else:
            continue  # Skip if not all aligned
        
        # Calculate RSI for 1h
        def calculate_rsi(prices, period=14):
            if len(prices) < period + 1:
                return 50
            deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            gains = [d if d > 0 else 0 for d in deltas[-period:]]
            losses = [-d if d < 0 else 0 for d in deltas[-period:]]
            avg_gain = sum(gains) / period
            avg_loss = sum(losses) / period
            if avg_loss == 0:
                return 100
            rs = avg_gain / avg_loss
            return 100 - (100 / (1 + rs))
        
        h1_closes = [c['close'] for c in h1_recent]
        rsi = calculate_rsi(h1_closes)
        
        # RSI filter - relaxed
        if direction == 'bullish' and rsi > 70:
            continue
        if direction == 'bearish' and rsi < 30:
            continue
        
        # Volume filter - require above average volume
        recent_volumes = [c['volume'] for c in h1_recent[-20:]]
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        current_volume = candle['volume']
        if current_volume < avg_volume * 0.8:  # At least 80% of average
            continue
        diff = h1_high - h1_low
        fib_levels = {
            '0.0': h1_high,
            '0.236': h1_high - diff * 0.236,
            '0.382': h1_high - diff * 0.382,
            '0.5': h1_high - diff * 0.5,
            '0.618': h1_high - diff * 0.618,
            '0.786': h1_high - diff * 0.786,
            '1.0': h1_low
        }
        
        # Check if price is near a Fib level
        at_fib = None
        for level_name, level_price in fib_levels.items():
            if abs(h1_close - level_price) / h1_close < 0.01:  # 1% tolerance
                at_fib = level_name
                break
        
        if not at_fib:
            continue
        
        # Good levels for entries - expanded
        if direction == 'bullish' and at_fib not in ['0.618', '0.5', '0.382']:
            continue
        if direction == 'bearish' and at_fib not in ['0.382', '0.5', '0.618']:
            continue
        
        # Trend strength check - relaxed to 1%
        if direction == 'bullish':
            trend_strength = (h1_close - h1_old) / h1_old * 100
            if trend_strength < 1:
                continue
        else:
            trend_strength = (h1_old - h1_close) / h1_old * 100
            if trend_strength < 1:
                continue
        
        # Calculate stop and target with 1:2 R:R minimum
        atr = (h1_high - h1_low) * 0.15  # Slightly wider ATR
        
        if direction == 'bullish':
            stop = h1_close - (atr * 1.5)
            target = h1_close + (atr * 3)  # 1:2 R:R
        else:
            stop = h1_close + (atr * 1.5)
            target = h1_close - (atr * 3)  # 1:2 R:R
        
        # Skip if stop is too close (less than 0.5%)
        stop_distance = abs(stop - h1_close) / h1_close * 100
        if stop_distance < 0.5:
            continue
        
        # Check outcome (next 20 candles)
        outcome = 'open'
        exit_price = None
        pnl = 0
        
        for j in range(i+1, min(i+21, len(data_1h))):
            future = data_1h[j]
            
            if direction == 'bullish':
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
            else:
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
        
        setup = {
            'symbol': symbol,
            'timestamp': timestamp,
            'date': datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M'),
            'direction': direction,
            'entry': round(h1_close, 2),
            'stop': round(stop, 2),
            'target': round(target, 2),
            'fib_level': at_fib,
            'h1_trend': h1_trend,
            'h4_trend': h4_trend,
            'd1_trend': d1_trend,
            'outcome': outcome,
            'exit_price': round(exit_price, 2) if exit_price else None,
            'pnl_pct': round(pnl, 2) if pnl else 0
        }
        
        setups.append(setup)
    
    return setups

def main():
    print("=" * 70)
    print("HISTORICAL SETUP FINDER")
    print("=" * 70)
    
    all_setups = []
    
    for symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']:
        setups = find_setups_simple(symbol)
        all_setups.extend(setups)
        print(f"  Found {len(setups)} setups")
    
    # Statistics
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    print(f"\nTotal setups: {len(all_setups)}")
    
    if not all_setups:
        print("No setups found.")
        return
    
    wins = sum(1 for s in all_setups if s['outcome'] == 'win')
    losses = sum(1 for s in all_setups if s['outcome'] == 'loss')
    open_trades = sum(1 for s in all_setups if s['outcome'] == 'open')
    
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")
    print(f"Open: {open_trades}")
    
    if wins + losses > 0:
        win_rate = wins / (wins + losses) * 100
        print(f"Win rate: {win_rate:.1f}%")
        
        total_pnl = sum(s['pnl_pct'] for s in all_setups)
        print(f"Total P&L: {total_pnl:.2f}%")
        
        avg_win = sum(s['pnl_pct'] for s in all_setups if s['outcome'] == 'win') / wins if wins > 0 else 0
        avg_loss = sum(s['pnl_pct'] for s in all_setups if s['outcome'] == 'loss') / losses if losses > 0 else 0
        print(f"Avg win: {avg_win:.2f}%")
        print(f"Avg loss: {avg_loss:.2f}%")
    
    # Show setups by symbol
    for symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']:
        symbol_setups = [s for s in all_setups if s['symbol'] == symbol]
        if not symbol_setups:
            continue
        
        print(f"\n{symbol}: {len(symbol_setups)} setups")
        wins = sum(1 for s in symbol_setups if s['outcome'] == 'win')
        losses = sum(1 for s in symbol_setups if s['outcome'] == 'loss')
        pnl = sum(s['pnl_pct'] for s in symbol_setups)
        print(f"  W/L: {wins}/{losses}, P&L: {pnl:+.2f}%")
    
    # Show last 10 setups
    print("\n" + "=" * 70)
    print("LAST 10 SETUPS")
    print("=" * 70)
    
    for setup in sorted(all_setups, key=lambda x: x['timestamp'], reverse=True)[:10]:
        icon = "✅" if setup['outcome'] == 'win' else "❌" if setup['outcome'] == 'loss' else "⏳"
        print(f"\n{icon} {setup['symbol']} {setup['direction'].upper()}")
        print(f"   Date: {setup['date']}")
        print(f"   Entry: ${setup['entry']} (Fib {setup['fib_level']})")
        print(f"   Stop: ${setup['stop']} | Target: ${setup['target']}")
        print(f"   Trends: 1h={setup['h1_trend']}, 4h={setup['h4_trend']}, 1d={setup['d1_trend']}")
        if setup['pnl_pct']:
            print(f"   P&L: {setup['pnl_pct']:+.2f}%")
    
    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f'setups_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
    with open(output_file, 'w') as f:
        json.dump(all_setups, f, indent=2)
    print(f"\nSaved to: {output_file}")

if __name__ == '__main__':
    main()
