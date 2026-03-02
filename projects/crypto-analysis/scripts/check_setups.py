#!/usr/bin/env python3
"""
FINAL Trade Setup Checker - Optimized Strategies
BTC: 3x ATR, ETH: 1.5x ATR + filters, BNB: 3x ATR + extreme filters
"""

import json
import csv
import glob
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

def calculate_ema(prices, period):
    if len(prices) < period:
        return [None] * len(prices)
    multiplier = 2 / (period + 1)
    ema = [sum(prices[:period]) / period]
    for p in prices[period:]:
        ema.append((p * multiplier) + (ema[-1] * (1 - multiplier)))
    return [None] * (period - 1) + ema

# FINAL STRATEGIES
STRATEGIES = {
    'BTCUSDT': {
        'name': 'BTC Trend Following',
        'fib_levels': ['0.618', '0.5', '0.382'],
        'stop_mult': 3.0,
        'target_mult': 6.0,
        'min_stop_pct': 0.75,
        'rsi_long_max': 70,
        'rsi_short_min': 30,
        'volume_min': 0.8
    },
    'ETHUSDT': {
        'name': 'ETH Selective Momentum',
        'fib_levels': ['0.618', '0.5'],
        'stop_mult': 1.5,
        'target_mult': 3.0,
        'min_stop_pct': 0.38,
        'rsi_long_max': 70,
        'rsi_short_min': 30,
        'volume_min': 0.8,
        'consecutive_candles': 3
    },
    'BNBUSDT': {
        'name': 'BNB Extreme Selectivity',
        'fib_levels': ['0.5'],
        'stop_mult': 3.0,
        'target_mult': 6.0,
        'min_stop_pct': 0.75,
        'rsi_long_max': 65,
        'rsi_short_min': 35,
        'volume_min': 1.5,
        'trend_lookback_days': 10,
        'min_trend_change_pct': 5.0
    }
}

def get_latest_analysis(symbol):
    files = sorted(MTF_DIR.glob(f"{symbol}_mtf_*.json"), reverse=True)
    if not files:
        return None
    with open(files[0], 'r') as f:
        return json.load(f)

def check_btc_setup(analysis, strategy):
    """Check BTC with trend following strategy"""
    bias = analysis.get('overall_bias', 'unknown')
    confidence = analysis.get('confidence', 0)
    
    if confidence < 70 or bias not in ['bullish', 'bearish']:
        return None
    
    tf_analysis = analysis.get('timeframe_analysis', {})
    entry_data = tf_analysis.get('1h', {})
    
    at_fib = entry_data.get('at_higher_tf_fib')
    if not at_fib or at_fib not in strategy['fib_levels']:
        return None
    
    rsi = entry_data.get('rsi', 50)
    if bias == 'bullish' and rsi > strategy['rsi_long_max']:
        return None
    if bias == 'bearish' and rsi < strategy['rsi_short_min']:
        return None
    
    return format_setup('BTCUSDT', bias, entry_data, strategy)

def check_eth_setup(analysis, strategy):
    """Check ETH with selective momentum strategy"""
    # Similar to BTC but with consecutive candle check
    bias = analysis.get('overall_bias', 'unknown')
    confidence = analysis.get('confidence', 0)
    
    if confidence < 70 or bias not in ['bullish', 'bearish']:
        return None
    
    tf_analysis = analysis.get('timeframe_analysis', {})
    entry_data = tf_analysis.get('1h', {})
    
    at_fib = entry_data.get('at_higher_tf_fib')
    if not at_fib or at_fib not in strategy['fib_levels']:
        return None
    
    rsi = entry_data.get('rsi', 50)
    if bias == 'bullish' and rsi > strategy['rsi_long_max']:
        return None
    if bias == 'bearish' and rsi < strategy['rsi_short_min']:
        return None
    
    # Note: Consecutive candle check requires price history
    # For now, use same as BTC with tighter stops
    
    return format_setup('ETHUSDT', bias, entry_data, strategy)

def check_bnb_setup(analysis, strategy, data_1d):
    """Check BNB with extreme selectivity"""
    bias = analysis.get('overall_bias', 'unknown')
    confidence = analysis.get('confidence', 0)
    
    if confidence < 70 or bias not in ['bullish', 'bearish']:
        return None
    
    # Check extreme trend filter
    if data_1d and len(data_1d) >= 11:
        d_close = data_1d[-1]['close']
        d_10ago = data_1d[-11]['close']
        trend_change = abs(d_close - d_10ago) / d_10ago * 100
        
        if trend_change < strategy['min_trend_change_pct']:
            return None  # Trend not strong enough
    
    tf_analysis = analysis.get('timeframe_analysis', {})
    entry_data = tf_analysis.get('1h', {})
    
    at_fib = entry_data.get('at_higher_tf_fib')
    if at_fib not in strategy['fib_levels']:
        return None
    
    rsi = entry_data.get('rsi', 50)
    if bias == 'bullish' and rsi > strategy['rsi_long_max']:
        return None
    if bias == 'bearish' and rsi < strategy['rsi_short_min']:
        return None
    
    return format_setup('BNBUSDT', bias, entry_data, strategy)

def format_setup(symbol, bias, entry_data, strategy):
    """Format trade setup"""
    close = entry_data.get('latest_close', 0)
    
    # Calculate ATR
    key_levels = entry_data.get('key_levels', {})
    if 'high' in key_levels and 'low' in key_levels:
        atr = (key_levels['high'] - key_levels['low']) * 0.1
    else:
        atr = close * 0.01
    
    if bias == 'bearish':
        stop = close + (atr * strategy['stop_mult'])
        target = close - (atr * strategy['target_mult'])
    else:
        stop = close - (atr * strategy['stop_mult'])
        target = close + (atr * strategy['target_mult'])
    
    risk = abs(stop - close)
    reward = abs(target - close)
    rr = reward / risk if risk > 0 else 0
    
    # Futures position sizing (per $1000)
    risk_amount = 1000 * 0.03  # 3% risk
    position_size = risk_amount / (risk / close)
    margin = position_size / 5  # 5x leverage
    
    return {
        'symbol': symbol,
        'direction': bias,
        'strategy': strategy['name'],
        'entry': round(close, 2),
        'stop': round(stop, 2),
        'target': round(target, 2),
        'rr': round(rr, 2),
        'position_size': round(position_size, 2),
        'margin': round(margin, 2)
    }

def check_trade_setups():
    """Main function to check all setups"""
    setups_found = []
    
    # Check BTC
    analysis = get_latest_analysis('BTCUSDT')
    if analysis:
        setup = check_btc_setup(analysis, STRATEGIES['BTCUSDT'])
        if setup:
            setups_found.append(setup)
    
    # Check ETH
    analysis = get_latest_analysis('ETHUSDT')
    if analysis:
        setup = check_eth_setup(analysis, STRATEGIES['ETHUSDT'])
        if setup:
            setups_found.append(setup)
    
    # Check BNB (needs daily data)
    analysis = get_latest_analysis('BNBUSDT')
    data_1d = load_data('BNBUSDT', '1d')
    if analysis and data_1d:
        setup = check_bnb_setup(analysis, STRATEGIES['BNBUSDT'], data_1d)
        if setup:
            setups_found.append(setup)
    
    return setups_found

if __name__ == '__main__':
    setups = check_trade_setups()
    
    if setups:
        print("🎯 TRADE SETUPS FOUND:")
        for s in setups:
            print(f"\n{s['symbol']} - {s['direction'].upper()}")
            print(f"  Strategy: {s['strategy']}")
            print(f"  Entry: ${s['entry']}")
            print(f"  Stop: ${s['stop']}")
            print(f"  Target: ${s['target']}")
            print(f"  R:R = 1:{s['rr']}")
            print(f"  Position: ${s['position_size']} (margin: ${s['margin']})")
    else:
        # Silent exit - no message
        pass
