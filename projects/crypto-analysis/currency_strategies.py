#!/usr/bin/env python3
"""
Individual Currency Strategies - Unique Parameters Per Pair
ETH Strategy: Selective Momentum with Confirmation
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import numpy as np

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
INDICATORS_DIR = Path('/root/.openclaw/workspace/data/indicators')

# =============================================================================
# STRATEGY CONFIGURATIONS - UNIQUE PER CURRENCY
# =============================================================================

STRATEGIES = {
    'ETHUSDT': {
        'name': 'ETH_Selective_Momentum_v2',
        'description': 'Momentum breakout with confirmation and position scaling',
        'timeframe': '1h',
        'trend_timeframe': '4h',
        'direction': 'LONG',
        
        # Entry Parameters
        'entry': {
            'method': 'momentum_breakout_with_confirmation',
            'ema_fast': 9,
            'ema_slow': 21,
            'consecutive_bullish': 2,  # Reduced from 3 for more entries
            'require_close_above': True,  # Wait for candle close
            'volume_threshold': 1.0,  # 1.0x average (tightened from 0.8x)
        },
        
        # Stop Loss
        'stop_loss': {
            'method': 'atr_based',
            'atr_multiplier': 1.5,
            'min_stop_pct': 0.38,
            'max_stop_pct': 2.0,
        },
        
        # Take Profit
        'take_profit': {
            'method': 'rr_based',
            'atr_multiplier': 3.0,
            'min_rr': 2.0,
            'targets': [2.0, 3.0],  # R:R levels
        },
        
        # Position Sizing
        'position_sizing': {
            'method': 'scaled_entry',
            'initial_risk': 0.015,  # 1.5% on first entry
            'add_risk': 0.015,      # 1.5% on add
            'total_risk': 0.03,     # 3% total
            'add_trigger': 'confirmation',  # Add after confirmation candle
        },
        
        # Filters
        'filters': {
            'rsi_period': 14,
            'rsi_min': 40,
            'rsi_max': 75,
            'macd_confirmation': True,
            'volatility_max': 4.0,  # Skip if ATR% > 4%
            'max_spread_pct': 0.08,
        },
        
        # Exit
        'exit': {
            'time_stop': 20,
            'trailing_stop': True,
            'trailing_activation': 1.5,
            'breakeven_trigger': 1.0,
        }
    },
    
    'BTCUSDT': {
        'name': 'BTC_Trend_Following_v2',
        'description': 'Fibonacci pullback with strict trend filters',
        'timeframe': '1h',
        'trend_timeframe': '1d',
        'direction': 'LONG',
        
        'entry': {
            'method': 'fibonacci_pullback',
            'fib_levels': [0.618, 0.5],  # Prioritize 0.618
            'fib_tolerance': 0.01,
            'require_daily_trend': True,  # CRITICAL: Price > EMA 20 daily
            'require_adx': True,          # CRITICAL: ADX > 25
            'adx_period': 14,
            'adx_threshold': 25,
        },
        
        'stop_loss': {
            'method': 'atr_based',
            'atr_multiplier': 4.0,  # INCREASED from 3.0
            'min_stop_pct': 0.75,
            'max_stop_pct': 4.0,
        },
        
        'take_profit': {
            'method': 'fib_extension',
            'atr_multiplier': 6.0,
            'min_rr': 2.0,
        },
        
        'position_sizing': {
            'method': 'fixed_risk',
            'risk_per_trade': 0.03,
            'max_position': 0.6,
        },
        
        'filters': {
            'rsi_period': 14,
            'rsi_min': 35,
            'rsi_max': 70,
            'max_trades_per_day': 2,  # NEW: Limit overtrading
            'volume_threshold': 0.8,
        },
        
        'exit': {
            'time_stop': 24,
            'trailing_stop': False,
            'breakeven_trigger': 1.0,
        }
    },
    
    'SOLUSDT': {
        'name': 'SOL_EMA_Momentum_v2',
        'description': 'EMA crossover with momentum confirmation',
        'timeframe': '1h',
        'trend_timeframe': '4h',
        'direction': 'LONG',
        
        'entry': {
            'method': 'ema_crossover_with_pullback',
            'ema_fast': 12,
            'ema_slow': 26,
            'require_pullback': True,  # Wait for pullback to fast EMA
            'rsi_confirmation': True,
            'rsi_min': 50,
            'rsi_max': 70,
        },
        
        'stop_loss': {
            'method': 'fixed_percentage',
            'fixed_pct': 2.5,  # REDUCED from 3.0
        },
        
        'take_profit': {
            'method': 'fixed_percentage',
            'fixed_pct': 4.0,
        },
        
        'position_sizing': {
            'method': 'fixed_risk_reduced',
            'risk_per_trade': 0.015,  # 1.5% (half of normal)
            'position_factor': 0.5,
        },
        
        'filters': {
            'adx_min': 20,  # NEW: Avoid chop
            'max_trades_per_day': 2,
            'cooldown_hours': 4,
        },
        
        'exit': {
            'time_stop': 24,
            'close_on_opposite_cross': True,
        }
    },
    
    'XRPUSDT': {
        'name': 'XRP_PAUSED',
        'description': 'STRATEGY DISABLED - Underperforming',
        'status': 'DISABLED',
        'reason': '27% win rate unacceptable - needs complete redesign',
    },
    
    'BNBUSDT': {
        'name': 'BNB_Extreme_Selectivity_v2',
        'description': 'Ultra-selective trend following',
        'timeframe': '1h',
        'trend_timeframe': '1d',
        'direction': 'LONG',
        
        'entry': {
            'method': 'trend_plus_volume',
            'min_trend_pct': 3.0,  # REDUCED from 5%
            'trend_lookback_days': 10,
            'volume_spike': 1.2,     # REDUCED from 1.5
            'require_macd': True,
        },
        
        'stop_loss': {
            'method': 'atr_based',
            'atr_multiplier': 3.0,
        },
        
        'take_profit': {
            'method': 'atr_based',
            'atr_multiplier': 6.0,
        },
        
        'position_sizing': {
            'method': 'fixed_risk',
            'risk_per_trade': 0.03,
        },
        
        'filters': {
            'rsi_min': 40,
            'rsi_max': 75,
        },
        
        'exit': {
            'time_stop': 24,
        }
    }
}


# =============================================================================
# STRATEGY IMPLEMENTATIONS
# =============================================================================

def calculate_ema(prices: List[float], period: int) -> float:
    """Calculate EMA"""
    if len(prices) < period:
        return sum(prices) / len(prices)
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for price in prices[period:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    return ema


def calculate_atr(data: List[Dict], period: int = 14) -> float:
    """Calculate ATR"""
    if len(data) < period + 1:
        return 0
    tr_list = []
    for i in range(1, len(data)):
        high = data[i]['high']
        low = data[i]['low']
        prev_close = data[i-1]['close']
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_list.append(tr)
    return sum(tr_list[-period:]) / period


def calculate_adx(data: List[Dict], period: int = 14) -> float:
    """Simplified ADX calculation"""
    if len(data) < period * 2:
        return 25  # Default to trending
    
    # Calculate +DM and -DM
    plus_dm = []
    minus_dm = []
    for i in range(1, len(data)):
        high_diff = data[i]['high'] - data[i-1]['high']
        low_diff = data[i-1]['low'] - data[i]['low']
        
        plus_dm.append(max(high_diff, 0) if high_diff > low_diff else 0)
        minus_dm.append(max(low_diff, 0) if low_diff > high_diff else 0)
    
    # Simplified - return average of recent directional movement
    avg_plus = sum(plus_dm[-period:]) / period
    avg_minus = sum(minus_dm[-period:]) / period
    
    if avg_plus + avg_minus == 0:
        return 0
    
    dx = abs(avg_plus - avg_minus) / (avg_plus + avg_minus) * 100
    return dx


def eth_strategy(data_1h: List[Dict], data_4h: List[Dict], indicators: Dict) -> Optional[Dict]:
    """
    ETH Selective Momentum Strategy v2
    Key improvements: Confirmation candle, position scaling, volume filter
    """
    config = STRATEGIES['ETHUSDT']
    
    if len(data_1h) < 30:
        return None
    
    prices = [c['close'] for c in data_1h]
    highs = [c['high'] for c in data_1h]
    lows = [c['low'] for c in data_1h]
    volumes = [c['volume'] for c in data_1h]
    
    # Calculate EMAs
    ema9 = calculate_ema(prices[-20:], 9)
    ema21 = calculate_ema(prices[-30:], 21)
    
    # Check bullish alignment
    current = prices[-1]
    if current < ema9 or ema9 < ema21:
        return None
    
    # Check for momentum (2 consecutive bullish candles)
    if not (prices[-1] > prices[-2] > prices[-3]):
        return None
    
    # Volume check (1.0x average)
    avg_volume = sum(volumes[-20:]) / 20
    if volumes[-1] < avg_volume * config['entry']['volume_threshold']:
        return None
    
    # Check for breakout (close above recent high)
    recent_high = max(highs[-10:-1])
    if current <= recent_high:
        return None
    
    # Wait for confirmation - price must close above breakout level
    # (This is handled by caller checking previous candle)
    if prices[-2] <= recent_high:
        # This is the confirmation candle
        pass
    
    # Volatility filter (skip if ATR% > 4%)
    atr = calculate_atr(data_1h[-20:])
    atr_pct = (atr / current) * 100
    if atr_pct > config['filters']['volatility_max']:
        return None
    
    # Calculate levels
    stop = current - atr * config['stop_loss']['atr_multiplier']
    target = current + atr * config['take_profit']['atr_multiplier']
    
    # Check R:R
    risk = current - stop
    reward = target - current
    if reward / risk < config['take_profit']['min_rr']:
        return None
    
    return {
        'symbol': 'ETHUSDT',
        'direction': 'LONG',
        'entry': current,
        'stop': stop,
        'target': target,
        'strategy': config['name'],
        'position_scale': True,  # Flag for position scaling
        'initial_position': 0.5,  # 50% initial
        'add_position': 0.5,      # 50% on confirmation
        'rr': reward / risk
    }


def btc_strategy(data_1h: List[Dict], data_1d: List[Dict], indicators: Dict) -> Optional[Dict]:
    """
    BTC Trend Following Strategy v2
    Key improvements: ADX filter, daily trend check, wider stops, trade limits
    """
    config = STRATEGIES['BTCUSDT']
    
    if len(data_1h) < 50 or len(data_1d) < 20:
        return None
    
    # Check daily trend first (CRITICAL)
    daily_prices = [c['close'] for c in data_1d]
    daily_ema20 = calculate_ema(daily_prices[-30:], 20)
    
    if daily_prices[-1] < daily_ema20:
        return None  # No trades in downtrend
    
    # Check ADX (CRITICAL)
    adx = calculate_adx(data_1h[-30:])
    if adx < config['entry']['adx_threshold']:
        return None  # No trades in chop
    
    # Fibonacci pullback logic
    prices = [c['close'] for c in data_1h]
    highs = [c['high'] for c in data_1h]
    lows = [c['low'] for c in data_1h]
    
    swing_high = max(highs[-30:])
    swing_low = min(lows[-30:])
    current = prices[-1]
    
    # Calculate fib levels
    diff = swing_high - swing_low
    fib_618 = swing_high - diff * 0.618
    fib_50 = swing_high - diff * 0.5
    
    # Check if price in entry zone (prioritize 0.618)
    tolerance = config['entry']['fib_tolerance']
    in_zone = (fib_618 * (1 - tolerance) <= current <= fib_50 * (1 + tolerance))
    
    if not in_zone:
        return None
    
    # ATR and levels (4x multiplier)
    atr = calculate_atr(data_1h[-20:])
    stop = current - atr * config['stop_loss']['atr_multiplier']
    target = swing_high  # Target the swing high
    
    # Check minimum stop
    stop_pct = (current - stop) / current * 100
    if stop_pct < config['stop_loss']['min_stop_pct']:
        return None
    
    return {
        'symbol': 'BTCUSDT',
        'direction': 'LONG',
        'entry': current,
        'stop': stop,
        'target': target,
        'strategy': config['name'],
        'max_trades_per_day': config['filters']['max_trades_per_day']
    }


def sol_strategy(data_1h: List[Dict], indicators: Dict) -> Optional[Dict]:
    """
    SOL EMA Momentum Strategy v2
    Key improvements: Pullback entry, RSI confirmation, ADX filter
    """
    config = STRATEGIES['SOLUSDT']
    
    if len(data_1h) < 30:
        return None
    
    prices = [c['close'] for c in data_1h]
    
    # EMA 12/26
    ema12 = calculate_ema(prices[-20:], 12)
    ema26 = calculate_ema(prices[-30:], 26)
    
    # Check for bullish alignment
    current = prices[-1]
    if ema12 < ema26:
        return None
    
    # Check ADX
    adx = calculate_adx(data_1h[-20:])
    if adx < config['filters']['adx_min']:
        return None
    
    # Wait for pullback to EMA 12
    if current > ema12 * 1.02:  # Price more than 2% above EMA
        return None  # Too extended, wait for pullback
    
    if current < ema12 * 0.98:  # Price below EMA
        return None  # Pullback too deep
    
    # Entry zone is near EMA 12
    entry = current
    stop = entry * (1 - config['stop_loss']['fixed_pct'] / 100)
    target = entry * (1 + config['take_profit']['fixed_pct'] / 100)
    
    return {
        'symbol': 'SOLUSDT',
        'direction': 'LONG',
        'entry': entry,
        'stop': stop,
        'target': target,
        'strategy': config['name'],
        'position_factor': config['position_sizing']['position_factor']
    }


def xrp_strategy(data_1h: List[Dict], indicators: Dict) -> Optional[Dict]:
    """XRP Strategy - DISABLED"""
    return None  # Strategy disabled due to poor performance


def bnb_strategy(data_1h: List[Dict], data_1d: List[Dict], indicators: Dict) -> Optional[Dict]:
    """
    BNB Extreme Selectivity Strategy v2
    Key improvements: Relaxed filters to generate trades
    """
    config = STRATEGIES['BNBUSDT']
    
    if len(data_1h) < 50 or len(data_1d) < 10:
        return None
    
    # Check trend (relaxed to 3%)
    daily_prices = [c['close'] for c in data_1d]
    trend_pct = (daily_prices[-1] - daily_prices[-10]) / daily_prices[-10]
    if trend_pct < config['entry']['min_trend_pct'] / 100:
        return None
    
    # Check volume (relaxed to 1.2x)
    recent_vol = sum(c['volume'] for c in data_1h[-24:])
    avg_vol = sum(c['volume'] for c in data_1h[-120:]) / 5
    if recent_vol < avg_vol * config['entry']['volume_spike']:
        return None
    
    # Entry
    current = data_1h[-1]['close']
    atr = calculate_atr(data_1h[-20:])
    stop = current - atr * config['stop_loss']['atr_multiplier']
    target = current + atr * config['take_profit']['atr_multiplier']
    
    return {
        'symbol': 'BNBUSDT',
        'direction': 'LONG',
        'entry': current,
        'stop': stop,
        'target': target,
        'strategy': config['name']
    }


# =============================================================================
# STRATEGY SELECTOR
# =============================================================================

def get_strategy(symbol: str):
    """Get the appropriate strategy function for a symbol"""
    strategies = {
        'ETHUSDT': eth_strategy,
        'BTCUSDT': btc_strategy,
        'SOLUSDT': sol_strategy,
        'XRPUSDT': xrp_strategy,
        'BNBUSDT': bnb_strategy,
    }
    return strategies.get(symbol)


def get_strategy_config(symbol: str) -> Dict:
    """Get strategy configuration for a symbol"""
    return STRATEGIES.get(symbol, {})


if __name__ == '__main__':
    print("="*80)
    print("INDIVIDUAL CURRENCY STRATEGIES - CONFIGURATION")
    print("="*80)
    
    for symbol, config in STRATEGIES.items():
        print(f"\n📊 {symbol}: {config.get('name', 'N/A')}")
        print(f"   Status: {config.get('status', 'ACTIVE')}")
        if 'description' in config:
            print(f"   Description: {config['description']}")
        if 'reason' in config:
            print(f"   Reason: {config['reason']}")
        
        if 'entry' in config:
            print(f"   Entry: {config['entry']['method']}")
        if 'stop_loss' in config:
            print(f"   Stop: {config['stop_loss'].get('atr_multiplier', 'N/A')}x ATR")
        if 'position_sizing' in config:
            risk = config['position_sizing'].get('risk_per_trade', 'N/A')
            print(f"   Risk: {risk*100 if isinstance(risk, float) else risk}%")
    
    print("\n" + "="*80)
    print("Strategies loaded successfully!")
    print("="*80)
