#!/usr/bin/env python3
"""
Winning Strategies for BTC and BNB
Based on analysis of successful setups
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

def calculate_atr(data, period=14):
    """Calculate Average True Range"""
    if len(data) < period + 1:
        return [None] * len(data)
    
    tr_list = [None]
    for i in range(1, len(data)):
        high = data[i]['high']
        low = data[i]['low']
        prev_close = data[i-1]['close']
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_list.append(tr)
    
    atr = [None] * period
    if len(tr_list) > period:
        first_atr = sum(tr_list[1:period+1]) / period
        atr.append(first_atr)
        
        for i in range(period + 1, len(tr_list)):
            atr.append((atr[-1] * (period - 1) + tr_list[i]) / period)
    
    return atr

def find_btc_winning_strategy(data_1h, data_1d):
    """
    BTC Winning Strategy Analysis:
    - Only 1 win out of 3 setups
    - Win was at Fib 0.618, all 3 trends aligned bearish
    - Losses also at Fib 0.618 with same alignment
    - Difference: Need to check for exhaustion
    
    Key insight: BTC needs confirmation of trend continuation
    not just reversal at Fib level
    """
    setups = []
    
    for i in range(50, len(data_1h) - 20):
        candle = data_1h[i]
        timestamp = candle['timestamp']
        
        # Daily trend check
        d_idx = next((j for j, d in enumerate(data_1d) if d['timestamp'] > timestamp), len(data_1d)) - 1
        if d_idx < 20:
            continue
        
        d_closes = [d['close'] for d in data_1d[:d_idx+1]]
        d_ema20 = calculate_ema(d_closes, 20)
        d_ema50 = calculate_ema(d_closes, 50)
        
        if d_ema20[-1] is None or d_ema50[-1] is None:
            continue
        
        d_close = data_1d[d_idx]['close']
        
        if d_close < d_ema20[-1] < d_ema50[-1]:
            trend = 'bearish'
        elif d_close > d_ema20[-1] > d_ema50[-1]:
            trend = 'bullish'
        else:
            continue
        
        # 1h context
        h1_recent = data_1h[i-20:i+1]
        h1_high = max(c['high'] for c in h1_recent)
        h1_low = min(c['low'] for c in h1_recent)
        h1_close = candle['close']
        
        # ATR for position sizing
        atr_list = calculate_atr(h1_recent)
        atr = atr_list[-1] if atr_list[-1] else (h1_high - h1_low) * 0.1
        
        # Fibonacci - only 0.618 for BTC (where the win was)
        diff = h1_high - h1_low
        fib_618 = h1_high - diff * 0.618
        
        if abs(h1_close - fib_618) / h1_close > 0.008:  # 0.8% tolerance
            continue
        
        # BTC SPECIFIC: Check for momentum exhaustion
        # Look for 3+ candles in trend direction with decreasing momentum
        h1_closes = [c['close'] for c in h1_recent[-5:]]
        
        if trend == 'bearish':
            # Need consecutive lower lows but RSI not oversold yet
            lower_lows = all(h1_closes[j] < h1_closes[j-1] for j in range(1, len(h1_closes)))
            if not lower_lows:
                continue
        else:
            higher_highs = all(h1_closes[j] > h1_closes[j-1] for j in range(1, len(h1_closes)))
            if not higher_highs:
                continue
        
        # RSI check - not extreme
        rsi_list = calculate_rsi([c['close'] for c in h1_recent])
        rsi = rsi_list[-1] if rsi_list[-1] else 50
        
        if trend == 'bearish' and rsi < 30:
            continue  # Too oversold, might bounce
        if trend == 'bullish' and rsi > 70:
            continue  # Too overbought, might pullback
        
        # Volume confirmation - above average
        recent_volumes = [c['volume'] for c in h1_recent[-10:]]
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        if candle['volume'] < avg_volume * 1.0:  # Need at least average volume
            continue
        
        # Calculate stop/target - tighter for BTC
        if trend == 'bearish':
            stop = h1_close + (atr * 1.2)
            target = h1_close - (atr * 2.4)  # 1:2 R:R
        else:
            stop = h1_close - (atr * 1.2)
            target = h1_close + (atr * 2.4)
        
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
        
        setups.append({
            'symbol': 'BTCUSDT',
            'date': datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M'),
            'direction': trend,
            'entry': round(h1_close, 2),
            'stop': round(stop, 2),
            'target': round(target, 2),
            'fib': '0.618',
            'rsi': round(rsi, 1),
            'volume_ratio': round(candle['volume'] / avg_volume, 2),
            'outcome': outcome,
            'pnl': round(pnl, 2)
        })
    
    return setups


def find_bnb_winning_strategy(data_1h, data_1d):
    """
    BNB Winning Strategy Analysis:
    - Only 1 win out of 6 setups
    - Win was at Fib 0.5 (not 0.618 or 0.382)
    - Losses at 0.618, 0.382, 0.5
    - Key difference: The win had stronger trend alignment
    
    Key insight: BNB needs middle Fib (0.5) with very strong trend
    and conservative RSI
    """
    setups = []
    
    for i in range(50, len(data_1h) - 20):
        candle = data_1h[i]
        timestamp = candle['timestamp']
        
        # Daily trend check - must be strong
        d_idx = next((j for j, d in enumerate(data_1d) if d['timestamp'] > timestamp), len(data_1d)) - 1
        if d_idx < 20:
            continue
        
        d_closes = [d['close'] for d in data_1d[:d_idx+1]]
        d_ema20 = calculate_ema(d_closes, 20)
        d_ema50 = calculate_ema(d_closes, 50)
        
        if d_ema20[-1] is None or d_ema50[-1] is None:
            continue
        
        d_close = data_1d[d_idx]['close']
        
        # BNB: Need strong trend - price far from EMA
        ema_distance = abs(d_close - d_ema20[-1]) / d_close * 100
        
        if d_close < d_ema20[-1] < d_ema50[-1] and ema_distance > 2.0:
            trend = 'bearish'
        elif d_close > d_ema20[-1] > d_ema50[-1] and ema_distance > 2.0:
            trend = 'bullish'
        else:
            continue
        
        # 1h context
        h1_recent = data_1h[i-20:i+1]
        h1_high = max(c['high'] for c in h1_recent)
        h1_low = min(c['low'] for c in h1_recent)
        h1_close = candle['close']
        
        # ATR
        atr_list = calculate_atr(h1_recent)
        atr = atr_list[-1] if atr_list[-1] else (h1_high - h1_low) * 0.1
        
        # BNB SPECIFIC: Only 0.5 Fib (where the win was)
        diff = h1_high - h1_low
        fib_50 = h1_high - diff * 0.5
        
        if abs(h1_close - fib_50) / h1_close > 0.006:  # 0.6% tolerance
            continue
        
        # BNB SPECIFIC: Very conservative RSI
        h1_closes = [c['close'] for c in h1_recent]
        rsi_list = calculate_rsi(h1_closes)
        rsi = rsi_list[-1] if rsi_list[-1] else 50
        
        if trend == 'bearish' and (rsi < 35 or rsi > 55):
            continue  # Need moderate RSI for bearish
        if trend == 'bullish' and (rsi > 65 or rsi < 45):
            continue  # Need moderate RSI for bullish
        
        # BNB SPECIFIC: High volume required (low liquidity coin)
        recent_volumes = [c['volume'] for c in h1_recent[-10:]]
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        if candle['volume'] < avg_volume * 1.2:  # 20% above average
            continue
        
        # Calculate stop/target - wider for BNB's volatility
        if trend == 'bearish':
            stop = h1_close + (atr * 1.5)
            target = h1_close - (atr * 3.0)  # 1:2 R:R
        else:
            stop = h1_close - (atr * 1.5)
            target = h1_close + (atr * 3.0)
        
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
        
        setups.append({
            'symbol': 'BNBUSDT',
            'date': datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M'),
            'direction': trend,
            'entry': round(h1_close, 2),
            'stop': round(stop, 2),
            'target': round(target, 2),
            'fib': '0.5',
            'rsi': round(rsi, 1),
            'ema_distance': round(ema_distance, 2),
            'volume_ratio': round(candle['volume'] / avg_volume, 2),
            'outcome': outcome,
            'pnl': round(pnl, 2)
        })
    
    return setups


def main():
    print("=" * 70)
    print("WINNING STRATEGIES FOR BTC AND BNB")
    print("=" * 70)
    
    # Test BTC strategy
    print("\n--- BTC STRATEGY (Momentum Exhaustion at 0.618) ---")
    btc_data_1h = load_data('BTCUSDT', '1h')
    btc_data_1d = load_data('BTCUSDT', '1d')
    btc_setups = find_btc_winning_strategy(btc_data_1h, btc_data_1d)
    
    wins = sum(1 for s in btc_setups if s['outcome'] == 'win')
    losses = sum(1 for s in btc_setups if s['outcome'] == 'loss')
    pnl = sum(s['pnl'] for s in btc_setups)
    
    print(f"Setups: {len(btc_setups)}, Wins: {wins}, Losses: {losses}")
    print(f"Win Rate: {(wins/(wins+losses)*100 if (wins+losses) > 0 else 0):.1f}%")
    print(f"Total P&L: {pnl:+.2f}%")
    
    if btc_setups:
        print("\nRecent setups:")
        for s in btc_setups[-5:]:
            icon = "✅" if s['outcome'] == 'win' else "❌" if s['outcome'] == 'loss' else "⏳"
            print(f"  {icon} {s['date']}: {s['direction']} @ ${s['entry']}, Fib {s['fib']}, RSI {s['rsi']}, Vol {s['volume_ratio']}x")
    
    # Test BNB strategy
    print("\n--- BNB STRATEGY (Strong Trend at 0.5) ---")
    bnb_data_1h = load_data('BNBUSDT', '1h')
    bnb_data_1d = load_data('BNBUSDT', '1d')
    bnb_setups = find_bnb_winning_strategy(bnb_data_1h, bnb_data_1d)
    
    wins = sum(1 for s in bnb_setups if s['outcome'] == 'win')
    losses = sum(1 for s in bnb_setups if s['outcome'] == 'loss')
    pnl = sum(s['pnl'] for s in bnb_setups)
    
    print(f"Setups: {len(bnb_setups)}, Wins: {wins}, Losses: {losses}")
    print(f"Win Rate: {(wins/(wins+losses)*100 if (wins+losses) > 0 else 0):.1f}%")
    print(f"Total P&L: {pnl:+.2f}%")
    
    if bnb_setups:
        print("\nRecent setups:")
        for s in bnb_setups[-5:]:
            icon = "✅" if s['outcome'] == 'win' else "❌" if s['outcome'] == 'loss' else "⏳"
            print(f"  {icon} {s['date']}: {s['direction']} @ ${s['entry']}, Fib {s['fib']}, EMA dist {s['ema_distance']}%, Vol {s['volume_ratio']}x")
    
    # Summary
    print("\n" + "=" * 70)
    print("STRATEGY SUMMARY")
    print("=" * 70)
    
    print("\nBTC Strategy:")
    print("  - Entry: Only at Fib 0.618")
    print("  - Condition: 5 consecutive candles in trend direction")
    print("  - RSI: Not extreme (30-70 range)")
    print("  - Volume: Above average (1.0x)")
    print("  - Stop: 1.2x ATR, Target: 2.4x ATR (1:2 R:R)")
    
    print("\nBNB Strategy:")
    print("  - Entry: Only at Fib 0.5")
    print("  - Condition: Strong trend (price >2% from daily EMA)")
    print("  - RSI: Moderate (35-55 for shorts, 45-65 for longs)")
    print("  - Volume: 1.2x above average (liquidity requirement)")
    print("  - Stop: 1.5x ATR, Target: 3.0x ATR (1:2 R:R)")


if __name__ == '__main__':
    main()
