#!/usr/bin/env python3
"""
Strategy Optimization Framework
Test multiple variations to find optimal trade identification
"""

import csv
import json
import itertools
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import copy

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
OUTPUT_DIR = Path('/root/.openclaw/workspace/optimization_results')

SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']

@dataclass
class StrategyParams:
    """Strategy parameters to test"""
    name: str
    timeframe_alignment: str  # 'all3', 'majority2', 'daily_only'
    rsi_long_max: int
    rsi_short_min: int
    fib_levels_long: List[str]
    fib_levels_short: List[str]
    volume_threshold: float  # 0.0 to 1.0
    trend_strength_min: float  # percentage
    stop_atr_multiplier: float
    target_atr_multiplier: float
    holding_periods: int  # candles to hold
    use_pattern_confirm: bool
    min_stop_pct: float  # minimum stop distance
    
    def get_rr_ratio(self) -> float:
        return self.target_atr_multiplier / self.stop_atr_multiplier


def load_data(symbol: str, interval: str) -> List[Dict]:
    """Load OHLCV data"""
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


def calculate_ema(prices: List[float], period: int) -> List[Optional[float]]:
    if len(prices) < period:
        return [None] * len(prices)
    multiplier = 2 / (period + 1)
    ema = [sum(prices[:period]) / period]
    for price in prices[period:]:
        ema.append((price * multiplier) + (ema[-1] * (1 - multiplier)))
    return [None] * (period - 1) + ema


def calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
    if len(prices) < period + 1:
        return [None] * len(prices)
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    rsi = [None]
    for i in range(period, len(deltas)):
        gains = [d if d > 0 else 0 for d in deltas[i-period:i]]
        losses = [-d if d < 0 else 0 for d in deltas[i-period:i]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            rsi.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi.append(100 - (100 / (1 + rs)))
    return [None] * period + rsi[period:]


def calculate_bollinger(prices: List[float], period: int = 20, std_dev: float = 2.0):
    if len(prices) < period:
        return [None] * len(prices), [None] * len(prices), [None] * len(prices)
    
    middle = []
    upper = []
    lower = []
    
    for i in range(len(prices)):
        if i < period - 1:
            middle.append(None)
            upper.append(None)
            lower.append(None)
        else:
            window = prices[i-period+1:i+1]
            sma = sum(window) / period
            variance = sum((x - sma) ** 2 for x in window) / period
            std = variance ** 0.5
            middle.append(sma)
            upper.append(sma + std_dev * std)
            lower.append(sma - std_dev * std)
    
    return middle, upper, lower


def find_setups_with_params(symbol: str, params: StrategyParams) -> List[Dict]:
    """Find setups using specific parameters"""
    data_1h = load_data(symbol, '1h')
    data_4h = load_data(symbol, '4h')
    data_1d = load_data(symbol, '1d')
    
    if not data_1h or not data_4h or not data_1d:
        return []
    
    setups = []
    
    for i in range(100, len(data_1h) - params.holding_periods, 4):
        candle = data_1h[i]
        timestamp = candle['timestamp']
        
        # Get 1h context
        h1_recent = data_1h[i-20:i+1]
        h1_high = max(c['high'] for c in h1_recent)
        h1_low = min(c['low'] for c in h1_recent)
        h1_close = candle['close']
        h1_old = h1_recent[0]['close']
        h1_trend = 'bullish' if h1_close > h1_recent[10]['close'] else 'bearish'
        
        # Get 4h context
        h4_idx = next((j for j, h4 in enumerate(data_4h) if h4['timestamp'] > timestamp), len(data_4h)) - 1
        if h4_idx < 10:
            continue
        h4_recent = data_4h[h4_idx-10:h4_idx+1]
        h4_close = h4_recent[-1]['close']
        h4_old = h4_recent[0]['close']
        h4_trend = 'bullish' if h4_close > h4_recent[5]['close'] else 'bearish'
        
        # Get 1d context
        d1_idx = next((j for j, d1 in enumerate(data_1d) if d1['timestamp'] > timestamp), len(data_1d)) - 1
        if d1_idx < 5:
            continue
        d1_recent = data_1d[d1_idx-5:d1_idx+1]
        d1_close = d1_recent[-1]['close']
        d1_old = d1_recent[0]['close']
        d1_trend = 'bullish' if d1_close > d1_recent[2]['close'] else 'bearish'
        
        # TIMEFRAME ALIGNMENT CHECK
        trends = {'1h': h1_trend, '4h': h4_trend, '1d': d1_trend}
        bullish_count = sum(1 for t in trends.values() if t == 'bullish')
        bearish_count = sum(1 for t in trends.values() if t == 'bearish')
        
        if params.timeframe_alignment == 'all3':
            if bullish_count == 3:
                direction = 'bullish'
            elif bearish_count == 3:
                direction = 'bearish'
            else:
                continue
        elif params.timeframe_alignment == 'majority2':
            if bullish_count >= 2 and d1_trend == 'bullish':
                direction = 'bullish'
            elif bearish_count >= 2 and d1_trend == 'bearish':
                direction = 'bearish'
            else:
                continue
        elif params.timeframe_alignment == 'daily_only':
            if d1_trend == 'bullish' and h1_trend == 'bullish':
                direction = 'bullish'
            elif d1_trend == 'bearish' and h1_trend == 'bearish':
                direction = 'bearish'
            else:
                continue
        
        # RSI CHECK
        h1_closes = [c['close'] for c in h1_recent]
        rsi_list = calculate_rsi(h1_closes, 14)
        rsi = rsi_list[-1] if rsi_list[-1] is not None else 50
        
        if direction == 'bullish' and rsi > params.rsi_long_max:
            continue
        if direction == 'bearish' and rsi < params.rsi_short_min:
            continue
        
        # VOLUME CHECK
        recent_volumes = [c['volume'] for c in h1_recent[-20:]]
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        if candle['volume'] < avg_volume * params.volume_threshold:
            continue
        
        # TREND STRENGTH CHECK
        if direction == 'bullish':
            strength = (h1_close - h1_old) / h1_old * 100
            if strength < params.trend_strength_min:
                continue
        else:
            strength = (h1_old - h1_close) / h1_old * 100
            if strength < params.trend_strength_min:
                continue
        
        # FIBONACCI LEVELS
        diff = h1_high - h1_low
        fib_levels = {
            '0.0': h1_high, '0.236': h1_high - diff * 0.236,
            '0.382': h1_high - diff * 0.382, '0.5': h1_high - diff * 0.5,
            '0.618': h1_high - diff * 0.618, '0.786': h1_high - diff * 0.786,
            '1.0': h1_low
        }
        
        at_fib = None
        for level_name, level_price in fib_levels.items():
            if abs(h1_close - level_price) / h1_close < 0.015:
                at_fib = level_name
                break
        
        if not at_fib:
            continue
        
        if direction == 'bullish' and at_fib not in params.fib_levels_long:
            continue
        if direction == 'bearish' and at_fib not in params.fib_levels_short:
            continue
        
        # BOLLINGER BAND CONFIRMATION (optional pattern)
        if params.use_pattern_confirm:
            bb_middle, bb_upper, bb_lower = calculate_bollinger(h1_closes)
            if bb_upper[-1] and bb_lower[-1]:
                if direction == 'bullish' and h1_close > bb_middle[-1]:
                    continue  # Want price below middle for longs
                if direction == 'bearish' and h1_close < bb_middle[-1]:
                    continue  # Want price above middle for shorts
        
        # CALCULATE STOP AND TARGET
        atr = (h1_high - h1_low) * 0.1
        
        if direction == 'bullish':
            stop = h1_close - (atr * params.stop_atr_multiplier)
            target = h1_close + (atr * params.target_atr_multiplier)
        else:
            stop = h1_close + (atr * params.stop_atr_multiplier)
            target = h1_close - (atr * params.target_atr_multiplier)
        
        # MINIMUM STOP CHECK
        stop_distance = abs(stop - h1_close) / h1_close * 100
        if stop_distance < params.min_stop_pct:
            continue
        
        # CHECK OUTCOME
        outcome = 'open'
        exit_price = None
        pnl = 0
        
        for j in range(i+1, min(i + params.holding_periods + 1, len(data_1h))):
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
        
        setups.append({
            'symbol': symbol,
            'timestamp': timestamp,
            'direction': direction,
            'entry': round(h1_close, 2),
            'stop': round(stop, 2),
            'target': round(target, 2),
            'fib': at_fib,
            'rsi': round(rsi, 1),
            'outcome': outcome,
            'pnl': round(pnl, 2),
            'rr': params.get_rr_ratio()
        })
    
    return setups


def calculate_stats(setups: List[Dict]) -> Dict:
    """Calculate statistics for a set of trades"""
    if not setups:
        return {'total': 0, 'win_rate': 0, 'pnl': 0, 'avg_win': 0, 'avg_loss': 0}
    
    wins = sum(1 for s in setups if s['outcome'] == 'win')
    losses = sum(1 for s in setups if s['outcome'] == 'loss')
    open_trades = sum(1 for s in setups if s['outcome'] == 'open')
    
    total_pnl = sum(s['pnl'] for s in setups)
    
    win_pnls = [s['pnl'] for s in setups if s['outcome'] == 'win']
    loss_pnls = [s['pnl'] for s in setups if s['outcome'] == 'loss']
    
    return {
        'total': len(setups),
        'wins': wins,
        'losses': losses,
        'open': open_trades,
        'win_rate': (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0,
        'pnl': round(total_pnl, 2),
        'avg_win': round(sum(win_pnls) / len(win_pnls), 2) if win_pnls else 0,
        'avg_loss': round(sum(loss_pnls) / len(loss_pnls), 2) if loss_pnls else 0,
        'profit_factor': abs(sum(win_pnls) / sum(loss_pnls)) if sum(loss_pnls) != 0 else 0
    }


def run_optimization():
    """Test multiple strategy variations"""
    
    # Define parameter variations to test
    param_sets = [
        # Baseline (current working strategy)
        StrategyParams('baseline', 'all3', 70, 30, ['0.618', '0.5'], ['0.382', '0.5'], 
                      0.8, 1.0, 1.5, 3.0, 20, False, 0.5),
        
        # Test 1: More selective (only 0.618/0.382)
        StrategyParams('selective_fib', 'all3', 65, 35, ['0.618'], ['0.382'], 
                      0.8, 1.5, 1.5, 3.0, 20, False, 0.5),
        
        # Test 2: Wider stops, bigger targets
        StrategyParams('wide_rr', 'all3', 70, 30, ['0.618', '0.5', '0.382'], ['0.382', '0.5', '0.618'], 
                      0.8, 0.5, 1.0, 4.0, 30, False, 0.3),
        
        # Test 3: Shorter holds
        StrategyParams('quick_scalp', 'all3', 70, 30, ['0.5'], ['0.5'], 
                      0.8, 0.5, 1.0, 2.0, 10, False, 0.5),
        
        # Test 4: Majority 2 instead of all 3
        StrategyParams('majority2', 'majority2', 70, 30, ['0.618', '0.5'], ['0.382', '0.5'], 
                      0.8, 1.0, 1.5, 3.0, 20, False, 0.5),
        
        # Test 5: Daily trend only
        StrategyParams('daily_trend', 'daily_only', 70, 30, ['0.618', '0.5'], ['0.382', '0.5'], 
                      0.8, 1.0, 1.5, 3.0, 20, False, 0.5),
        
        # Test 6: With Bollinger confirmation
        StrategyParams('bb_confirm', 'all3', 70, 30, ['0.618', '0.5'], ['0.382', '0.5'], 
                      0.8, 1.0, 1.5, 3.0, 20, True, 0.5),
        
        # Test 7: No volume filter
        StrategyParams('no_volume', 'all3', 70, 30, ['0.618', '0.5'], ['0.382', '0.5'], 
                      0.0, 1.0, 1.5, 3.0, 20, False, 0.5),
        
        # Test 8: Extended Fib levels
        StrategyParams('extended_fib', 'all3', 75, 25, ['0.618', '0.5', '0.382', '0.786'], 
                      ['0.382', '0.5', '0.618', '0.236'], 
                      0.8, 0.5, 1.5, 3.0, 20, False, 0.5),
        
        # Test 9: Tighter stops
        StrategyParams('tight_stops', 'all3', 70, 30, ['0.618', '0.5'], ['0.382', '0.5'], 
                      0.8, 1.0, 1.0, 2.5, 15, False, 0.5),
        
        # Test 10: Longer holds for trends
        StrategyParams('trend_hold', 'all3', 70, 30, ['0.618', '0.5'], ['0.382', '0.5'], 
                      0.8, 2.0, 1.5, 4.0, 40, False, 0.5),
    ]
    
    results = []
    
    print("=" * 80)
    print("STRATEGY OPTIMIZATION")
    print("=" * 80)
    
    for params in param_sets:
        print(f"\nTesting: {params.name}")
        print("-" * 40)
        
        all_setups = []
        for symbol in SYMBOLS:
            setups = find_setups_with_params(symbol, params)
            all_setups.extend(setups)
            print(f"  {symbol}: {len(setups)} setups")
        
        stats = calculate_stats(all_setups)
        stats['strategy'] = params.name
        stats['params'] = {
            'alignment': params.timeframe_alignment,
            'rsi_range': f"<{params.rsi_long_max}, >{params.rsi_short_min}",
            'fib_long': params.fib_levels_long,
            'fib_short': params.fib_levels_short,
            'rr_ratio': params.get_rr_ratio(),
            'hold_periods': params.holding_periods
        }
        
        results.append(stats)
        
        print(f"  Total: {stats['total']}, Win Rate: {stats['win_rate']:.1f}%, P&L: {stats['pnl']:+.2f}%")
    
    # Sort by P&L
    results.sort(key=lambda x: x['pnl'], reverse=True)
    
    print("\n" + "=" * 80)
    print("RANKINGS (by P&L)")
    print("=" * 80)
    
    for i, r in enumerate(results[:5], 1):
        print(f"\n{i}. {r['strategy']}")
        print(f"   Setups: {r['total']} | Wins: {r.get('wins', 0)} | Losses: {r.get('losses', 0)}")
        print(f"   Win Rate: {r['win_rate']:.1f}%")
        print(f"   Total P&L: {r['pnl']:+.2f}%")
        print(f"   Avg Win: {r['avg_win']:+.2f}% | Avg Loss: {r['avg_loss']:+.2f}%")
        print(f"   Profit Factor: {r['profit_factor']:.2f}")
        print(f"   R:R Ratio: {r['params']['rr_ratio']:.1f}")
    
    # Save results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / f'optimization_{datetime.now().strftime("%Y%m%d_%H%M")}.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return results


if __name__ == '__main__':
    run_optimization()
