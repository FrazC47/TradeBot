#!/usr/bin/env python3
"""
FINAL Trade Setup Checker - V3
BTC: Fibonacci Pullback | ETH: Momentum Breakout | BNB: Extreme Selectivity
"""

import json
import csv
from pathlib import Path
from datetime import datetime

MTF_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/mtf')
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

# STRATEGY V3
STRATEGIES = {
    'BTCUSDT': {
        'name': 'BTC Fibonacci Pullback',
        'fib_levels': ['0.618', '0.5', '0.382'],
        'fib_tolerance': 0.01,
        'stop_mult': 3.0,
        'target_mult': 6.0,
        'rsi_long_max': 70,
        'rsi_short_min': 30,
        'volume_min': 0.8
    },
    'ETHUSDT': {
        'name': 'ETH Momentum Breakout',
        'breakout_lookback': 20,
        'breakout_buffer': 0.005,
        'volume_min': 1.2
    },
    'BNBUSDT': {
        'name': 'BNB Extreme Selectivity',
        'fib_levels': ['0.5'],
        'fib_tolerance': 0.01,
        'stop_mult': 3.0,
        'target_mult': 6.0,
        'rsi_long_max': 65,
        'rsi_short_min': 35,
        'volume_min': 1.5,
        'trend_lookback': 10,
        'min_trend_change': 5.0
    }
}

def format_setup(symbol, trend, entry, stop, target, strategy_name, context):
    """Format trade setup"""
    risk = abs(stop - entry)
    reward = abs(target - entry)
    rr = reward / risk if risk > 0 else 0
    
    # Position sizing (per $1000 account, 3% risk, 5x leverage)
    risk_amount = 1000 * 0.03
    position_size = risk_amount / (risk / entry)
    margin = position_size / 5
    
    return {
        'symbol': symbol,
        'direction': trend,
        'strategy': strategy_name,
        'context': context,
        'entry': round(entry, 2),
        'stop': round(stop, 2),
        'target': round(target, 2),
        'rr': round(rr, 2),
        'position_size': round(position_size, 2),
        'margin': round(margin, 2)
    }

def check_btc_setup(data_1h, data_1d):
    """BTC: Fibonacci Pullback Strategy"""
    if not data_1h or len(data_1h) < 50 or not data_1d or len(data_1d) < 6:
        return None
    
    strategy = STRATEGIES['BTCUSDT']
    latest = data_1h[-1]
    close = latest['close']
    
    # Daily trend
    d_close = data_1d[-1]['close']
    d_old = data_1d[-6]['close']
    trend = 'bullish' if d_close > d_old else 'bearish' if d_close < d_old else None
    if not trend:
        return None
    
    # Fibonacci levels
    recent = data_1h[-21:-1]
    h = max(c['high'] for c in recent)
    l = min(c['low'] for c in recent)
    diff = h - l
    
    fibs = {'0.618': h - diff * 0.618, '0.5': h - diff * 0.5, '0.382': h - diff * 0.382}
    
    at_fib = None
    for level_name, level_price in fibs.items():
        if abs(close - level_price) / close < strategy['fib_tolerance']:
            at_fib = level_name
            break
    
    if not at_fib:
        return None
    
    # RSI check
    closes = [c['close'] for c in data_1h[-30:]]
    rsi_list = calculate_rsi(closes)
    rsi = rsi_list[-1] if rsi_list[-1] else 50
    
    if trend == 'bullish' and rsi > strategy['rsi_long_max']:
        return None
    if trend == 'bearish' and rsi < strategy['rsi_short_min']:
        return None
    
    # Volume check
    recent_volumes = [c['volume'] for c in data_1h[-5:]]
    if latest['volume'] < sum(recent_volumes) / len(recent_volumes) * strategy['volume_min']:
        return None
    
    # Calculate stop/target
    atr = (h - l) * 0.1
    if trend == 'bullish':
        stop = close - (atr * strategy['stop_mult'])
        target = close + (atr * strategy['target_mult'])
    else:
        stop = close + (atr * strategy['stop_mult'])
        target = close - (atr * strategy['target_mult'])
    
    return format_setup('BTCUSDT', trend, close, stop, target, strategy['name'], f'Fib {at_fib}')

def check_eth_setup(data_1h):
    """ETH: Momentum Breakout Strategy"""
    if not data_1h or len(data_1h) < 50:
        return None
    
    strategy = STRATEGIES['ETHUSDT']
    latest = data_1h[-1]
    close = latest['close']
    
    # 20-period high/low
    recent = data_1h[-21:-1]
    recent_high = max(c['high'] for c in recent)
    recent_low = min(c['low'] for c in recent)
    
    # Volume check
    recent_volumes = [c['volume'] for c in data_1h[-5:]]
    if latest['volume'] < sum(recent_volumes) / len(recent_volumes) * strategy['volume_min']:
        return None
    
    # Breakout check
    buffer = strategy['breakout_buffer']
    trend = None
    
    if close > recent_high * (1 + buffer):
        trend = 'bullish'
        stop = recent_low
        target = close + (close - stop) * 2
    elif close < recent_low * (1 - buffer):
        trend = 'bearish'
        stop = recent_high
        target = close - (stop - close) * 2
    
    if not trend:
        return None
    
    return format_setup('ETHUSDT', trend, close, stop, target, strategy['name'], '20-period breakout')

def check_bnb_setup(data_1h, data_1d):
    """BNB: Extreme Selectivity Strategy"""
    if not data_1h or len(data_1h) < 50 or not data_1d or len(data_1d) < 11:
        return None
    
    strategy = STRATEGIES['BNBUSDT']
    latest = data_1h[-1]
    close = latest['close']
    
    # Extreme trend check (>5% over 10 days)
    d_close = data_1d[-1]['close']
    d_10ago = data_1d[-11]['close']
    trend_change = abs(d_close - d_10ago) / d_10ago * 100
    
    if trend_change < strategy['min_trend_change']:
        return None
    
    trend = 'bullish' if d_close > d_10ago else 'bearish'
    
    # Fibonacci (0.5 only)
    recent = data_1h[-21:-1]
    h = max(c['high'] for c in recent)
    l = min(c['low'] for c in recent)
    fib_50 = h - (h - l) * 0.5
    
    if abs(close - fib_50) / close > strategy['fib_tolerance']:
        return None
    
    # RSI check
    closes = [c['close'] for c in data_1h[-30:]]
    rsi_list = calculate_rsi(closes)
    rsi = rsi_list[-1] if rsi_list[-1] else 50
    
    if trend == 'bullish' and rsi > strategy['rsi_long_max']:
        return None
    if trend == 'bearish' and rsi < strategy['rsi_short_min']:
        return None
    
    # Volume check (strict)
    recent_volumes = [c['volume'] for c in data_1h[-5:]]
    if latest['volume'] < sum(recent_volumes) / len(recent_volumes) * strategy['volume_min']:
        return None
    
    # Calculate stop/target
    atr = (h - l) * 0.1
    if trend == 'bullish':
        stop = close - (atr * strategy['stop_mult'])
        target = close + (atr * strategy['target_mult'])
    else:
        stop = close + (atr * strategy['stop_mult'])
        target = close - (atr * strategy['target_mult'])
    
    return format_setup('BNBUSDT', trend, close, stop, target, strategy['name'], f'{trend_change:.1f}% trend')

def check_trade_setups():
    """Main function"""
    setups_found = []
    
    # Check BTC
    data_1h = load_data('BTCUSDT', '1h')
    data_1d = load_data('BTCUSDT', '1d')
    setup = check_btc_setup(data_1h, data_1d)
    if setup:
        setups_found.append(setup)
    
    # Check ETH
    data_1h = load_data('ETHUSDT', '1h')
    setup = check_eth_setup(data_1h)
    if setup:
        setups_found.append(setup)
    
    # Check BNB
    data_1h = load_data('BNBUSDT', '1h')
    data_1d = load_data('BNBUSDT', '1d')
    setup = check_bnb_setup(data_1h, data_1d)
    if setup:
        setups_found.append(setup)
    
    return setups_found

if __name__ == '__main__':
    setups = check_trade_setups()
    
    if setups:
        print("🎯 TRADE SETUPS FOUND:")
        for s in setups:
            emoji = "🟢" if s['direction'] == 'bullish' else "🔴"
            print(f"\n{emoji} {s['symbol']} {s['direction'].upper()}")
            print(f"   Strategy: {s['strategy']}")
            print(f"   Context: {s['context']}")
            print(f"   Entry: ${s['entry']}")
            print(f"   Stop: ${s['stop']}")
            print(f"   Target: ${s['target']}")
            print(f"   R:R = 1:{s['rr']}")
            print(f"   Position: ${s['position_size']} (margin: ${s['margin']})")
    # Silent if no setups
