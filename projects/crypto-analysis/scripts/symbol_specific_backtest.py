#!/usr/bin/env python3
"""
Symbol-Specific Strategy Backtest
Different parameters for BTC, ETH, BNB based on their characteristics
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
OUTPUT_DIR = Path('/root/.openclaw/workspace/optimization_results')

@dataclass
class SymbolConfig:
    """Configuration per symbol"""
    name: str
    fib_levels_long: list
    fib_levels_short: list
    stop_mult: float
    target_mult: float
    min_atr_pct: float
    rsi_long_max: int
    rsi_short_min: int
    holding_periods: int

# Symbol-specific configurations - REVISED
CONFIGS = {
    'BTCUSDT': SymbolConfig(
        'BTC',
        fib_levels_long=['0.618', '0.5'],
        fib_levels_short=['0.382', '0.5'],
        stop_mult=1.5,
        target_mult=3.0,
        min_atr_pct=0.5,
        rsi_long_max=70,
        rsi_short_min=30,
        holding_periods=20
    ),
    'ETHUSDT': SymbolConfig(
        'ETH',
        fib_levels_long=['0.618', '0.5'],
        fib_levels_short=['0.382', '0.5'],
        stop_mult=1.5,
        target_mult=3.0,
        min_atr_pct=0.5,
        rsi_long_max=70,
        rsi_short_min=30,
        holding_periods=20
    ),
    'BNBUSDT': SymbolConfig(
        'BNB',
        fib_levels_long=['0.618'],
        fib_levels_short=['0.382'],
        stop_mult=1.2,
        target_mult=2.0,
        min_atr_pct=0.6,
        rsi_long_max=60,
        rsi_short_min=40,
        holding_periods=16
    )
}

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

def find_symbol_setups(symbol, config):
    """Find setups with symbol-specific config"""
    data_1h = load_data(symbol, '1h')
    data_1d = load_data(symbol, '1d')
    
    if not data_1h or not data_1d:
        return []
    
    setups = []
    
    for i in range(100, len(data_1h) - config.holding_periods):
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
        
        # ATR check
        atr = (h1_high - h1_low) * 0.1
        atr_pct = atr / h1_close * 100
        if atr_pct < config.min_atr_pct:
            continue
        
        # Fibonacci levels
        diff = h1_high - h1_low
        fib_levels = {
            '0.618': h1_high - diff * 0.618,
            '0.5': h1_high - diff * 0.5,
            '0.382': h1_high - diff * 0.382
        }
        
        at_fib = None
        for level_name, level_price in fib_levels.items():
            if abs(h1_close - level_price) / h1_close < 0.012:
                at_fib = level_name
                break
        
        if not at_fib:
            continue
        
        if trend == 'bullish' and at_fib not in config.fib_levels_long:
            continue
        if trend == 'bearish' and at_fib not in config.fib_levels_short:
            continue
        
        # RSI check
        h1_closes = [c['close'] for c in h1_recent]
        rsi_list = calculate_rsi(h1_closes)
        rsi = rsi_list[-1] if rsi_list[-1] else 50
        
        if trend == 'bullish' and rsi > config.rsi_long_max:
            continue
        if trend == 'bearish' and rsi < config.rsi_short_min:
            continue
        
        # Volume check
        recent_volumes = [c['volume'] for c in h1_recent[-20:]]
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        if candle['volume'] < avg_volume * 0.8:
            continue
        
        # Calculate stop/target
        if trend == 'bearish':
            stop = h1_close + (atr * config.stop_mult)
            target = h1_close - (atr * config.target_mult)
        else:
            stop = h1_close - (atr * config.stop_mult)
            target = h1_close + (atr * config.target_mult)
        
        # Check outcome
        outcome = 'open'
        pnl = 0
        
        for j in range(i+1, min(i + config.holding_periods + 1, len(data_1h))):
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
            'symbol': symbol,
            'date': datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M'),
            'direction': trend,
            'entry': round(h1_close, 2),
            'stop': round(stop, 2),
            'target': round(target, 2),
            'fib': at_fib,
            'rsi': round(rsi, 1),
            'outcome': outcome,
            'pnl': round(pnl, 2),
            'rr': round(config.target_mult / config.stop_mult, 2)
        })
    
    return setups

def main():
    print("=" * 70)
    print("SYMBOL-SPECIFIC STRATEGY BACKTEST")
    print("=" * 70)
    
    all_results = []
    
    for symbol, config in CONFIGS.items():
        print(f"\n{symbol}:")
        print(f"  Stop: {config.stop_mult}x ATR, Target: {config.target_mult}x ATR")
        print(f"  R:R = 1:{config.target_mult/config.stop_mult:.1f}")
        print(f"  Fib long: {config.fib_levels_long}, Fib short: {config.fib_levels_short}")
        print(f"  RSI: <{config.rsi_long_max} long, >{config.rsi_short_min} short")
        print(f"  Min ATR: {config.min_atr_pct}%, Hold: {config.holding_periods} candles")
        
        setups = find_symbol_setups(symbol, config)
        
        wins = sum(1 for s in setups if s['outcome'] == 'win')
        losses = sum(1 for s in setups if s['outcome'] == 'loss')
        total_pnl = sum(s['pnl'] for s in setups)
        
        win_pnls = [s['pnl'] for s in setups if s['outcome'] == 'win']
        loss_pnls = [s['pnl'] for s in setups if s['outcome'] == 'loss']
        
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        avg_win = sum(win_pnls) / len(win_pnls) if win_pnls else 0
        avg_loss = sum(loss_pnls) / len(loss_pnls) if loss_pnls else 0
        
        print(f"  Setups: {len(setups)} | Wins: {wins} | Losses: {losses}")
        print(f"  Win Rate: {win_rate:.1f}% | P&L: {total_pnl:+.2f}%")
        print(f"  Avg Win: {avg_win:+.2f}% | Avg Loss: {avg_loss:+.2f}%")
        
        all_results.extend(setups)
    
    # Overall stats
    print("\n" + "=" * 70)
    print("OVERALL RESULTS")
    print("=" * 70)
    
    wins = sum(1 for s in all_results if s['outcome'] == 'win')
    losses = sum(1 for s in all_results if s['outcome'] == 'loss')
    total_pnl = sum(s['pnl'] for s in all_results)
    
    win_pnls = [s['pnl'] for s in all_results if s['outcome'] == 'win']
    loss_pnls = [s['pnl'] for s in all_results if s['outcome'] == 'loss']
    
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    avg_win = sum(win_pnls) / len(win_pnls) if win_pnls else 0
    avg_loss = sum(loss_pnls) / len(loss_pnls) if loss_pnls else 0
    
    print(f"Total Setups: {len(all_results)}")
    print(f"Wins: {wins} | Losses: {losses}")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"Total P&L: {total_pnl:+.2f}%")
    print(f"Avg Win: {avg_win:+.2f}% | Avg Loss: {avg_loss:+.2f}%")
    
    # Show recent setups
    print("\n" + "=" * 70)
    print("RECENT SETUPS")
    print("=" * 70)
    
    for s in sorted(all_results, key=lambda x: x['date'], reverse=True)[:10]:
        icon = "✅" if s['outcome'] == 'win' else "❌" if s['outcome'] == 'loss' else "⏳"
        print(f"\n{icon} {s['symbol']} {s['direction'].upper()}")
        print(f"   {s['date']} | Entry: ${s['entry']} | Fib: {s['fib']}")
        print(f"   Stop: ${s['stop']} | Target: ${s['target']} | R:R 1:{s['rr']}")
        print(f"   P&L: {s['pnl']:+.2f}%")

if __name__ == '__main__':
    main()
