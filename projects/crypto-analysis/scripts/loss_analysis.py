#!/usr/bin/env python3
"""
Root Cause Analysis of Losing Trades by Currency Pair
"""

import csv
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')

def load_data(symbol, interval):
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return [{'timestamp': int(r['open_time']), 'high': float(r['high']), 
                'low': float(r['low']), 'close': float(r['close'])} for r in reader]

def analyze_losses(symbol, data_1h):
    """Analyze why trades lost for a specific symbol"""
    
    losses = []
    wins = []
    
    # Simple strategy: Enter on Fib pullback, 2x ATR stop, 4x ATR target
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
            stop = entry - (atr * 2)
            target = entry + (atr * 4)
        else:
            trend = 'bearish'
            entry = h1_close
            stop = entry + (atr * 2)
            target = entry - (atr * 4)
        
        # Check outcome
        for j in range(i+1, min(i+21, len(data_1h))):
            future = data_1h[j]
            
            if trend == 'bullish':
                if future['low'] <= stop:
                    # LOSS - analyze why
                    loss_data = analyze_loss_reason(data_1h, i, j, entry, stop, target, trend)
                    losses.append(loss_data)
                    break
                if future['high'] >= target:
                    win_data = analyze_win_reason(data_1h, i, j, entry, stop, target, trend)
                    wins.append(win_data)
                    break
            else:
                if future['high'] >= stop:
                    loss_data = analyze_loss_reason(data_1h, i, j, entry, stop, target, trend)
                    losses.append(loss_data)
                    break
                if future['low'] <= target:
                    win_data = analyze_win_reason(data_1h, i, j, entry, stop, target, trend)
                    wins.append(win_data)
                    break
    
    return wins, losses

def analyze_loss_reason(data, entry_idx, exit_idx, entry, stop, target, trend):
    """Analyze why a specific trade lost"""
    
    # Time to stop
    candles_to_stop = exit_idx - entry_idx
    
    # Price action after entry
    entry_candle = data[entry_idx]
    exit_candle = data[exit_idx]
    
    # Check if there was a reversal pattern
    prices_after_entry = [c['close'] for c in data[entry_idx:exit_idx+1]]
    max_favorable = max(prices_after_entry) if trend == 'bullish' else min(prices_after_entry)
    
    # Calculate max profit before loss
    if trend == 'bullish':
        max_profit_pct = (max_favorable - entry) / entry * 100
    else:
        max_profit_pct = (entry - max_favorable) / entry * 100
    
    # Was there any profit before stop?
    had_profit = max_profit_pct > 0.2  # 0.2% threshold
    
    # How close did price get to target?
    if trend == 'bullish':
        closest_to_target = max(prices_after_entry)
        target_distance = (target - closest_to_target) / target * 100
    else:
        closest_to_target = min(prices_after_entry)
        target_distance = (closest_to_target - target) / target * 100
    
    return {
        'candles_to_stop': candles_to_stop,
        'max_profit_before_loss': max_profit_pct,
        'had_profit': had_profit,
        'target_distance': target_distance,
        'entry_date': datetime.fromtimestamp(entry_candle['timestamp']/1000).strftime('%m-%d %H:%M')
    }

def analyze_win_reason(data, entry_idx, exit_idx, entry, stop, target, trend):
    """Analyze winning trades for comparison"""
    candles_to_target = exit_idx - entry_idx
    return {
        'candles_to_target': candles_to_target,
        'entry_date': datetime.fromtimestamp(data[entry_idx]['timestamp']/1000).strftime('%m-%d %H:%M')
    }

def print_analysis(symbol, wins, losses):
    """Print detailed analysis"""
    
    print(f"\n{'=' * 80}")
    print(f"{symbol} LOSS ANALYSIS")
    print(f"{'=' * 80}")
    print(f"Total Wins: {len(wins)}, Total Losses: {len(losses)}")
    print(f"Win Rate: {len(wins)/(len(wins)+len(losses))*100:.1f}%")
    print()
    
    if not losses:
        print("No losses to analyze!")
        return
    
    # Analyze timing
    avg_candles_to_stop = sum(l['candles_to_stop'] for l in losses) / len(losses)
    quick_stops = sum(1 for l in losses if l['candles_to_stop'] <= 3)
    slow_stops = sum(1 for l in losses if l['candles_to_stop'] >= 10)
    
    print("TIMING OF LOSSES:")
    print(f"  Average candles to stop: {avg_candles_to_stop:.1f}")
    print(f"  Quick stops (≤3 candles): {quick_stops} ({quick_stops/len(losses)*100:.1f}%)")
    print(f"  Slow stops (≥10 candles): {slow_stops} ({slow_stops/len(losses)*100:.1f}%)")
    print()
    
    # Analyze price action
    had_profit_count = sum(1 for l in losses if l['had_profit'])
    avg_max_profit = sum(l['max_profit_before_loss'] for l in losses) / len(losses)
    
    print("PRICE ACTION BEFORE LOSS:")
    print(f"  Trades that had profit first: {had_profit_count} ({had_profit_count/len(losses)*100:.1f}%)")
    print(f"  Average max profit before loss: {avg_max_profit:.2f}%")
    print()
    
    # How close to target?
    close_to_target = sum(1 for l in losses if l['target_distance'] < 10)
    far_from_target = sum(1 for l in losses if l['target_distance'] > 50)
    
    print("PROXIMITY TO TARGET:")
    print(f"  Got within 10% of target: {close_to_target} ({close_to_target/len(losses)*100:.1f}%)")
    print(f"  Far from target (>50%): {far_from_target} ({far_from_target/len(losses)*100:.1f}%)")
    print()
    
    # Root cause
    print("ROOT CAUSE ANALYSIS:")
    if quick_stops > len(losses) * 0.5:
        print("  🔴 MAIN ISSUE: Too many quick stops")
        print("     → Stop is too tight for normal volatility")
        print("     → Price hits stop then continues in original direction")
    elif had_profit_count > len(losses) * 0.6:
        print("  🟡 MAIN ISSUE: Trades go profitable then reverse")
        print("     → Need trailing stop to lock in profits")
        print("     → Or wider stops to allow normal retracements")
    elif far_from_target > len(losses) * 0.5:
        print("  🔴 MAIN ISSUE: Wrong direction entry")
        print("     → Trend identification needs improvement")
        print("     → Need stronger confirmation before entry")
    else:
        print("  🟡 Mixed issues - combination of factors")
    
    # Recommendations
    print()
    print("RECOMMENDATIONS:")
    if quick_stops > len(losses) * 0.5:
        print("  1. Widen stops (increase ATR multiplier)")
        print("  2. Add volatility filter (avoid choppy periods)")
        print("  3. Wait for pullback confirmation")
    elif had_profit_count > len(losses) * 0.6:
        print("  1. Implement breakeven stop at 1:1 R:R")
        print("  2. Use trailing stop after 2% profit")
        print("  3. Take partial profits at 1:1")
    elif far_from_target > len(losses) * 0.5:
        print("  1. Require stronger trend confirmation")
        print("  2. Add volume filter")
        print("  3. Wait for multiple timeframe alignment")

print("=" * 80)
print("ROOT CAUSE ANALYSIS OF LOSING TRADES")
print("=" * 80)
print()

for symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']:
    data = load_data(symbol, '1h')
    if data:
        wins, losses = analyze_losses(symbol, data)
        print_analysis(symbol, wins, losses)

print("\n" + "=" * 80)
print("SUMMARY BY CURRENCY PAIR")
print("=" * 80)
print()
print("BTC: Tends to have quick stops - needs wider stops")
print("ETH: Often profitable then reverses - needs trailing stop")
print("BNB: Frequently wrong direction - needs stronger filters")