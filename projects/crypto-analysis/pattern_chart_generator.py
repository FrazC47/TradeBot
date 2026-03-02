#!/usr/bin/env python3
"""
Pattern-Enhanced Candlestick Chart Generator with Timeframe-Specific Indicators
Generates interactive HTML candlestick charts with Japanese pattern detection,
highlighting, and timeframe-specific technical indicators.

Timeframe Indicator Matrix:
- 5M: EMA9, RSI(5), Session VWAP, Tick Delta, ATR(5), Heatmap
- 15M: EMA9/21/50, RSI(7), Micro-session VWAP, CVD/OBV, ATR(7), Heatmap
- 1H: EMA9/25, RSI(14), Session VWAP, 20SMA Vol, ATR(14), CVD/OBV
- 4H: EMA9/21, RSI(14), MACD(12,26,9), Session VWAP, 20SMA Vol, ATR(14), OI/Funding
- 1D: EMA20/50, RSI(14), MACD(12,26,9), Session VWAP, 20SMA Vol, ATR(14), Fibonacci
- 1W: EMA50/200, MACD(12,26,9), 20SMA Vol, Fib, S/R
- 1M: EMA50/200, MACD(12,26,9), 20SMA Vol, Fib, S/R
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Import pattern detector
try:
    from pattern_detector import PatternDetector, Pattern, PatternType, Candle
except ImportError:
    PatternDetector = None
    Pattern = None
    PatternType = None
    Candle = None

# Data directory
DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
OUTPUT_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/charts')

# Color scheme
COLORS = {
    'up': '#26a69a',              # Green for bullish
    'down': '#ef5350',            # Red for bearish
    'wick': '#787b86',            # Gray for wicks
    'bg': '#131722',              # Dark background
    'grid': '#2a2e39',            # Grid lines
    'text': '#d1d4dc',            # Text color
    'volume_up': 'rgba(38, 166, 154, 0.3)',
    'volume_down': 'rgba(239, 83, 80, 0.3)',
    # Pattern outline colors
    'pattern_bullish': '#00FF00',  # Bright green
    'pattern_bearish': '#FF0000',  # Bright red
    'pattern_neutral': '#FFFF00',  # Yellow
    # Indicator colors
    'ema9': '#FF6D00',            # Orange
    'ema21': '#00BCD4',           # Cyan
    'ema25': '#9C27B0',           # Purple
    'ema50': '#2196F3',           # Blue
    'ema200': '#E91E63',          # Pink
    'vwap': '#FFD700',            # Gold
    'rsi': '#FF9800',             # Amber
    'macd_line': '#00BCD4',       # Cyan
    'macd_signal': '#FF5722',     # Deep Orange
    'macd_histogram_up': 'rgba(38, 166, 154, 0.5)',
    'macd_histogram_down': 'rgba(239, 83, 80, 0.5)',
    'atr': '#607D8B',             # Blue Grey
    'fib_236': '#9E9E9E',         # Grey
    'fib_382': '#FFC107',         # Amber
    'fib_500': '#FF9800',         # Orange
    'fib_618': '#F44336',         # Red
    'fib_786': '#9C27B0',         # Purple
}

# Pattern display configuration
PATTERN_OUTLINE_WIDTH = 3


@dataclass
class IndicatorConfig:
    """Configuration for timeframe-specific indicators"""
    ema_periods: List[int]
    rsi_period: Optional[int]
    macd_fast: Optional[int]
    macd_slow: Optional[int]
    macd_signal: Optional[int]
    vwap_type: Optional[str]  # 'session', 'micro', None
    volume_type: Optional[str]  # 'tick_delta', 'cvd_obv', 'sma20', None
    atr_period: Optional[int]
    show_fibonacci: bool
    show_sr: bool
    show_heatmap: bool
    show_oi_funding: bool


# Timeframe indicator configurations
TIMEFRAME_CONFIGS = {
    '5m': IndicatorConfig(
        ema_periods=[9, 21],
        rsi_period=5,
        macd_fast=None, macd_slow=None, macd_signal=None,
        vwap_type='session',
        volume_type='sma20',
        atr_period=5,
        show_fibonacci=True,
        show_sr=False,
        show_heatmap=False,
        show_oi_funding=False
    ),
    '15m': IndicatorConfig(
        ema_periods=[9, 21, 50],
        rsi_period=7,
        macd_fast=None, macd_slow=None, macd_signal=None,
        vwap_type='micro',
        volume_type='cvd_obv',
        atr_period=7,
        show_fibonacci=True,
        show_sr=False,
        show_heatmap=True,
        show_oi_funding=False
    ),
    '1h': IndicatorConfig(
        ema_periods=[9, 25],
        rsi_period=14,
        macd_fast=None, macd_slow=None, macd_signal=None,
        vwap_type='session',
        volume_type='sma20',
        atr_period=14,
        show_fibonacci=False,
        show_sr=False,
        show_heatmap=False,
        show_oi_funding=False
    ),
    '4h': IndicatorConfig(
        ema_periods=[9, 21],
        rsi_period=14,
        macd_fast=12, macd_slow=26, macd_signal=9,
        vwap_type='session',
        volume_type='sma20',
        atr_period=14,
        show_fibonacci=False,
        show_sr=False,
        show_heatmap=False,
        show_oi_funding=True
    ),
    '1d': IndicatorConfig(
        ema_periods=[20, 50],
        rsi_period=14,
        macd_fast=12, macd_slow=26, macd_signal=9,
        vwap_type='session',
        volume_type='sma20',
        atr_period=14,
        show_fibonacci=True,
        show_sr=False,
        show_heatmap=False,
        show_oi_funding=False
    ),
    '1w': IndicatorConfig(
        ema_periods=[50, 200],
        rsi_period=None,
        macd_fast=12, macd_slow=26, macd_signal=9,
        vwap_type=None,
        volume_type='sma20',
        atr_period=None,
        show_fibonacci=True,
        show_sr=True,
        show_heatmap=False,
        show_oi_funding=False
    ),
    '1M': IndicatorConfig(
        ema_periods=[50, 200],
        rsi_period=None,
        macd_fast=12, macd_slow=26, macd_signal=9,
        vwap_type=None,
        volume_type='sma20',
        atr_period=None,
        show_fibonacci=True,
        show_sr=True,
        show_heatmap=False,
        show_oi_funding=False
    ),
}


def load_ohlcv_data(symbol: str, interval: str, limit: int = 200) -> List[Dict]:
    """Load OHLCV data from CSV file"""
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    
    if not filepath.exists():
        return []
    
    data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                data.append({
                    'timestamp': int(row['open_time']),
                    'datetime': datetime.fromtimestamp(int(row['open_time']) / 1000),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume'])
                })
            except (ValueError, KeyError):
                continue
    
    # Return last N candles
    return data[-limit:] if len(data) > limit else data


# ==================== INDICATOR CALCULATION FUNCTIONS ====================

def calculate_ema(data: List[Dict], period: int) -> List[Optional[float]]:
    """Calculate Exponential Moving Average"""
    if len(data) < period:
        return [None] * len(data)
    
    closes = [d['close'] for d in data]
    multiplier = 2 / (period + 1)
    
    ema_values = []
    # First EMA is SMA
    sma = sum(closes[:period]) / period
    ema_values.extend([None] * (period - 1))
    ema_values.append(sma)
    
    # Calculate subsequent EMAs
    for i in range(period, len(closes)):
        ema = (closes[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
        ema_values.append(ema)
    
    return ema_values


def calculate_sma(data: List[Dict], period: int, field: str = 'close') -> List[Optional[float]]:
    """Calculate Simple Moving Average"""
    if len(data) < period:
        return [None] * len(data)
    
    values = [d[field] for d in data]
    sma_values = []
    
    for i in range(len(values)):
        if i < period - 1:
            sma_values.append(None)
        else:
            sma = sum(values[i - period + 1:i + 1]) / period
            sma_values.append(sma)
    
    return sma_values


def calculate_rsi(data: List[Dict], period: int = 14) -> List[Optional[float]]:
    """Calculate Relative Strength Index"""
    if len(data) < period + 1:
        return [None] * len(data)
    
    closes = [d['close'] for d in data]
    rsi_values = [None] * period
    
    gains = []
    losses = []
    
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))
    
    if len(gains) < period:
        return rsi_values
    
    # First RSI calculation
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    if avg_loss == 0:
        rsi_values.append(100.0)
    else:
        rs = avg_gain / avg_loss
        rsi_values.append(100 - (100 / (1 + rs)))
    
    # Subsequent RSI calculations using smoothing
    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
        
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100 - (100 / (1 + rs)))
    
    return rsi_values


def calculate_macd(data: List[Dict], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """Calculate MACD (Moving Average Convergence Divergence)
    Returns: (macd_line, signal_line, histogram)
    """
    if len(data) < slow + signal:
        return ([None] * len(data), [None] * len(data), [None] * len(data))
    
    closes = [d['close'] for d in data]
    
    # Calculate EMAs
    def ema_series(prices, period):
        multiplier = 2 / (period + 1)
        ema = [sum(prices[:period]) / period]
        for price in prices[period:]:
            ema.append((price * multiplier) + (ema[-1] * (1 - multiplier)))
        return [None] * (period - 1) + ema
    
    ema_fast = ema_series(closes, fast)
    ema_slow = ema_series(closes, slow)
    
    # MACD Line
    macd_line = []
    for i in range(len(closes)):
        if ema_fast[i] is None or ema_slow[i] is None:
            macd_line.append(None)
        else:
            macd_line.append(ema_fast[i] - ema_slow[i])
    
    # Signal Line (EMA of MACD)
    valid_macd = [m for m in macd_line if m is not None]
    if len(valid_macd) < signal:
        return (macd_line, [None] * len(data), [None] * len(data))
    
    signal_ema = ema_series(valid_macd, signal)
    signal_line = [None] * (len(data) - len(signal_ema)) + signal_ema
    
    # Histogram
    histogram = []
    for i in range(len(data)):
        if macd_line[i] is None or signal_line[i] is None:
            histogram.append(None)
        else:
            histogram.append(macd_line[i] - signal_line[i])
    
    return (macd_line, signal_line, histogram)


def calculate_vwap(data: List[Dict], session_start_idx: int = 0) -> List[Optional[float]]:
    """Calculate Volume Weighted Average Price (VWAP)"""
    if not data:
        return []
    
    vwap_values = []
    cumulative_tp_vol = 0  # Cumulative (typical_price * volume)
    cumulative_vol = 0
    
    for i, d in enumerate(data):
        if i < session_start_idx:
            vwap_values.append(None)
            continue
        
        typical_price = (d['high'] + d['low'] + d['close']) / 3
        tp_vol = typical_price * d['volume']
        
        cumulative_tp_vol += tp_vol
        cumulative_vol += d['volume']
        
        if cumulative_vol > 0:
            vwap_values.append(cumulative_tp_vol / cumulative_vol)
        else:
            vwap_values.append(None)
    
    return vwap_values


def calculate_atr(data: List[Dict], period: int = 14) -> List[Optional[float]]:
    """Calculate Average True Range"""
    if len(data) < 2:
        return [None] * len(data)
    
    tr_values = []
    
    for i in range(len(data)):
        if i == 0:
            tr = data[i]['high'] - data[i]['low']
        else:
            tr1 = data[i]['high'] - data[i]['low']
            tr2 = abs(data[i]['high'] - data[i - 1]['close'])
            tr3 = abs(data[i]['low'] - data[i - 1]['close'])
            tr = max(tr1, tr2, tr3)
        tr_values.append(tr)
    
    if len(tr_values) < period:
        return [None] * len(data)
    
    atr_values = [None] * (period - 1)
    
    # First ATR is simple average
    first_atr = sum(tr_values[:period]) / period
    atr_values.append(first_atr)
    
    # Wilder's smoothing
    for i in range(period, len(tr_values)):
        atr = ((atr_values[-1] * (period - 1)) + tr_values[i]) / period
        atr_values.append(atr)
    
    return atr_values


def calculate_obv(data: List[Dict]) -> List[float]:
    """Calculate On-Balance Volume (OBV)"""
    if not data:
        return []
    
    obv_values = [data[0]['volume']]
    
    for i in range(1, len(data)):
        if data[i]['close'] > data[i - 1]['close']:
            obv_values.append(obv_values[-1] + data[i]['volume'])
        elif data[i]['close'] < data[i - 1]['close']:
            obv_values.append(obv_values[-1] - data[i]['volume'])
        else:
            obv_values.append(obv_values[-1])
    
    return obv_values


def calculate_cvd(data: List[Dict]) -> List[float]:
    """Calculate Cumulative Volume Delta (simplified)"""
    if not data:
        return []
    
    cvd_values = []
    cumulative = 0
    
    for d in data:
        # Estimate buying/selling pressure based on close position in range
        range_size = d['high'] - d['low']
        if range_size > 0:
            close_position = (d['close'] - d['low']) / range_size
            delta = (close_position - 0.5) * 2 * d['volume']  # -vol to +vol
        else:
            delta = 0
        
        cumulative += delta
        cvd_values.append(cumulative)
    
    return cvd_values


def calculate_fibonacci_retracement(high: float, low: float) -> Dict[str, float]:
    """Calculate Fibonacci retracement levels"""
    diff = high - low
    return {
        '0.0': high,
        '0.236': high - diff * 0.236,
        '0.382': high - diff * 0.382,
        '0.5': high - diff * 0.5,
        '0.618': high - diff * 0.618,
        '0.786': high - diff * 0.786,
        '1.0': low
    }


def calculate_bollinger_bands(data: List[Dict], period: int = 20, std_dev: float = 2.0) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """Calculate Bollinger Bands (middle, upper, lower)"""
    if len(data) < period:
        return [None] * len(data), [None] * len(data), [None] * len(data)
    
    closes = [d['close'] for d in data]
    middle = []
    upper = []
    lower = []
    
    for i in range(len(data)):
        if i < period - 1:
            middle.append(None)
            upper.append(None)
            lower.append(None)
        else:
            window = closes[i - period + 1:i + 1]
            sma = sum(window) / period
            variance = sum((x - sma) ** 2 for x in window) / period
            std = variance ** 0.5
            
            middle.append(sma)
            upper.append(sma + std_dev * std)
            lower.append(sma - std_dev * std)
    
    return middle, upper, lower


def calculate_previous_day_levels(data: List[Dict]) -> Dict[str, Optional[float]]:
    """Calculate previous day high, low, close for intraday timeframes"""
    if not data or len(data) < 2:
        return {'pd_high': None, 'pd_low': None, 'pd_close': None}
    
    # Group by day
    from datetime import datetime
    daily_data = {}
    
    for d in data:
        dt = datetime.fromtimestamp(d['timestamp'] / 1000)
        day_key = dt.strftime('%Y-%m-%d')
        
        if day_key not in daily_data:
            daily_data[day_key] = {'highs': [], 'lows': [], 'closes': []}
        
        daily_data[day_key]['highs'].append(d['high'])
        daily_data[day_key]['lows'].append(d['low'])
        daily_data[day_key]['closes'].append(d['close'])
    
    # Get previous day (not today)
    sorted_days = sorted(daily_data.keys())
    if len(sorted_days) < 2:
        return {'pd_high': None, 'pd_low': None, 'pd_close': None}
    
    prev_day = sorted_days[-2]
    prev_data = daily_data[prev_day]
    
    return {
        'pd_high': max(prev_data['highs']),
        'pd_low': min(prev_data['lows']),
        'pd_close': prev_data['closes'][-1]
    }


def find_support_resistance(data: List[Dict], lookback: int = 20, tolerance: float = 0.005) -> Dict[str, List[float]]:
    """Find support and resistance levels based on recent highs/lows"""
    if len(data) < lookback * 2:
        return {'support': [], 'resistance': []}
    
    recent_data = data[-lookback*2:]
    highs = [d['high'] for d in recent_data]
    lows = [d['low'] for d in recent_data]
    
    # Find local maxima and minima
    resistance_levels = []
    support_levels = []
    
    for i in range(1, len(recent_data) - 1):
        # Local maximum
        if recent_data[i]['high'] > recent_data[i-1]['high'] and recent_data[i]['high'] > recent_data[i+1]['high']:
            resistance_levels.append(recent_data[i]['high'])
        # Local minimum
        if recent_data[i]['low'] < recent_data[i-1]['low'] and recent_data[i]['low'] < recent_data[i+1]['low']:
            support_levels.append(recent_data[i]['low'])
    
    # Cluster nearby levels
    def cluster_levels(levels, tolerance):
        if not levels:
            return []
        levels = sorted(levels, reverse=True)
        clusters = [[levels[0]]]
        for level in levels[1:]:
            if abs(level - clusters[-1][0]) / clusters[-1][0] < tolerance:
                clusters[-1].append(level)
            else:
                clusters.append([level])
        return [sum(c) / len(c) for c in clusters[:3]]  # Top 3 clusters
    
    return {
        'resistance': cluster_levels(resistance_levels, tolerance),
        'support': cluster_levels(support_levels, tolerance)
    }


# ==================== INDICATOR CALCULATION BUNDLE ====================

def calculate_all_indicators(data: List[Dict], interval: str) -> Dict[str, Any]:
    """Calculate all indicators for a given timeframe"""
    # Map interval to config key
    interval_key = interval.lower()
    if interval_key == '1m':
        interval_key = '1M'  # Special case for monthly
    config = TIMEFRAME_CONFIGS.get(interval_key, TIMEFRAME_CONFIGS['1h'])
    indicators = {}
    
    # EMAs
    for period in config.ema_periods:
        indicators[f'ema{period}'] = calculate_ema(data, period)
    
    # RSI
    if config.rsi_period:
        indicators['rsi'] = calculate_rsi(data, config.rsi_period)
    
    # MACD
    if config.macd_fast and config.macd_slow and config.macd_signal:
        macd_line, signal_line, histogram = calculate_macd(
            data, config.macd_fast, config.macd_slow, config.macd_signal
        )
        indicators['macd_line'] = macd_line
        indicators['macd_signal'] = signal_line
        indicators['macd_histogram'] = histogram
    
    # VWAP
    if config.vwap_type:
        indicators['vwap'] = calculate_vwap(data, 0)
    
    # Volume indicators
    if config.volume_type == 'sma20':
        indicators['volume_sma20'] = calculate_sma(data, 20, 'volume')
    elif config.volume_type == 'cvd_obv':
        indicators['obv'] = calculate_obv(data)
        indicators['cvd'] = calculate_cvd(data)
    elif config.volume_type == 'tick_delta':
        indicators['tick_delta'] = calculate_cvd(data)  # Simplified tick delta
    
    # ATR
    if config.atr_period:
        indicators['atr'] = calculate_atr(data, config.atr_period)
    
    # Fibonacci
    if config.show_fibonacci and len(data) >= 20:
        recent_high = max(d['high'] for d in data[-50:])
        recent_low = min(d['low'] for d in data[-50:])
        indicators['fibonacci'] = calculate_fibonacci_retracement(recent_high, recent_low)
    
    # Support/Resistance
    if config.show_sr:
        indicators['sr_levels'] = find_support_resistance(data)
    
    # Bollinger Bands (for all timeframes)
    bb_middle, bb_upper, bb_lower = calculate_bollinger_bands(data, 20, 2.0)
    indicators['bb_middle'] = bb_middle
    indicators['bb_upper'] = bb_upper
    indicators['bb_lower'] = bb_lower
    
    # Previous Day High/Low/Close (for intraday timeframes)
    if interval in ['5m', '15m', '1h', '4h']:
        pd_levels = calculate_previous_day_levels(data)
        indicators['pd_high'] = pd_levels['pd_high']
        indicators['pd_low'] = pd_levels['pd_low']
        indicators['pd_close'] = pd_levels['pd_close']
    
    return indicators


def get_pattern_outline_color(pattern_type) -> str:
    """Get outline color for pattern type"""
    if pattern_type is None:
        return COLORS['pattern_neutral']
    try:
        if hasattr(pattern_type, 'value'):
            ptype = pattern_type.value
        else:
            ptype = str(pattern_type)
        
        if 'bullish' in ptype.lower():
            return COLORS['pattern_bullish']
        elif 'bearish' in ptype.lower():
            return COLORS['pattern_bearish']
        else:
            return COLORS['pattern_neutral']
    except:
        return COLORS['pattern_neutral']


def generate_pattern_annotations_js(patterns: List, data: List[Dict]) -> str:
    """Generate JavaScript for pattern annotations"""
    if not patterns:
        return ""
    
    annotations_js = []
    shapes_js = []
    
    for i, pattern in enumerate(patterns):
        start_idx = pattern.start_idx
        end_idx = pattern.end_idx
        
        if start_idx >= len(data) or end_idx >= len(data):
            continue
        
        start_time = int(data[start_idx]['timestamp'] / 1000)
        end_time = int(data[end_idx]['timestamp'] / 1000)
        
        # Get price levels for annotation positioning
        high_prices = [data[j]['high'] for j in range(start_idx, min(end_idx + 1, len(data)))]
        low_prices = [data[j]['low'] for j in range(start_idx, min(end_idx + 1, len(data)))]
        
        if not high_prices or not low_prices:
            continue
        
        max_high = max(high_prices)
        min_low = min(low_prices)
        
        # Determine label position
        color = get_pattern_outline_color(pattern.type)
        
        # Add marker for first candle
        marker_js = f"""
        // Pattern marker for {pattern.name}
        candleSeries.attachPrimitive({{
            type: 'Marker',
            time: {start_time},
            position: '{'belowBar' if 'bullish' in str(pattern.type).lower() else 'aboveBar'}',
            color: '{color}',
            text: '{pattern.name.upper()}',
            size: 2
        }});
        """
        annotations_js.append(marker_js)
    
    return '\n'.join(annotations_js + shapes_js)


def generate_pattern_legend(patterns: List) -> str:
    """Generate HTML legend for detected patterns"""
    if not patterns:
        return ""
    
    # Group patterns by name and count
    pattern_counts = {}
    for p in patterns:
        key = (p.name, p.type)
        pattern_counts[key] = pattern_counts.get(key, 0) + 1
    
    legend_items = []
    for (name, ptype), count in sorted(pattern_counts.items()):
        color = get_pattern_outline_color(ptype)
        count_text = f" x{count}" if count > 1 else ""
        legend_items.append(f"""
            <div class="legend-item">
                <span class="legend-color" style="background-color: {color};"></span>
                <span class="legend-text">{name}{count_text}</span>
            </div>
        """)
    
    return f"""
    <div class="pattern-legend">
        <div class="legend-title">Detected Patterns</div>
        {''.join(legend_items)}
    </div>
    """


def generate_indicator_stats(indicators: Dict[str, Any], data: List[Dict]) -> str:
    """Generate HTML for indicator statistics panel"""
    stats_html = []
    
    # Latest values
    latest_idx = len(data) - 1
    
    # EMAs
    for key in indicators:
        if key.startswith('ema') and indicators[key]:
            value = indicators[key][-1]
            if value is not None:
                period = key.replace('ema', '')
                color_key = key
                stats_html.append(f"""
                    <div class="stat-item indicator">
                        <div class="stat-label">EMA{period}</div>
                        <div class="stat-value" style="color: {COLORS.get(color_key, COLORS['text'])}">${value:,.2f}</div>
                    </div>
                """)
    
    # RSI
    if 'rsi' in indicators and indicators['rsi']:
        rsi_value = indicators['rsi'][-1]
        if rsi_value is not None:
            rsi_color = COLORS['rsi']
            rsi_status = "Overbought" if rsi_value > 70 else "Oversold" if rsi_value < 30 else "Neutral"
            stats_html.append(f"""
                <div class="stat-item indicator">
                    <div class="stat-label">RSI</div>
                    <div class="stat-value" style="color: {rsi_color}">{rsi_value:.1f} <span class="rsi-status">({rsi_status})</span></div>
                </div>
            """)
    
    # MACD
    if 'macd_line' in indicators and indicators['macd_line']:
        macd_val = indicators['macd_line'][-1]
        signal_val = indicators['macd_signal'][-1] if 'macd_signal' in indicators else None
        if macd_val is not None:
            macd_str = f"{macd_val:,.4f}"
            if signal_val is not None:
                macd_str += f" / {signal_val:,.4f}"
            stats_html.append(f"""
                <div class="stat-item indicator">
                    <div class="stat-label">MACD / Signal</div>
                    <div class="stat-value" style="color: {COLORS['macd_line']}">{macd_str}</div>
                </div>
            """)
    
    # VWAP
    if 'vwap' in indicators and indicators['vwap']:
        vwap_value = indicators['vwap'][-1]
        if vwap_value is not None:
            stats_html.append(f"""
                <div class="stat-item indicator">
                    <div class="stat-label">VWAP</div>
                    <div class="stat-value" style="color: {COLORS['vwap']}">${vwap_value:,.2f}</div>
                </div>
            """)
    
    # ATR
    if 'atr' in indicators and indicators['atr']:
        atr_value = indicators['atr'][-1]
        if atr_value is not None:
            stats_html.append(f"""
                <div class="stat-item indicator">
                    <div class="stat-label">ATR</div>
                    <div class="stat-value" style="color: {COLORS['atr']}">${atr_value:,.2f}</div>
                </div>
            """)
    
    # Bollinger Bands
    if 'bb_upper' in indicators and indicators['bb_upper']:
        bb_upper = indicators['bb_upper'][-1]
        bb_lower = indicators['bb_lower'][-1]
        if bb_upper is not None and bb_lower is not None:
            stats_html.append(f"""
                <div class="stat-item indicator">
                    <div class="stat-label">BB Upper</div>
                    <div class="stat-value" style="color: #9E9E9E">${bb_upper:,.2f}</div>
                </div>
            """)
            stats_html.append(f"""
                <div class="stat-item indicator">
                    <div class="stat-label">BB Lower</div>
                    <div class="stat-value" style="color: #9E9E9E">${bb_lower:,.2f}</div>
                </div>
            """)
    
    # Previous Day Levels
    if 'pd_high' in indicators and indicators['pd_high']:
        pd_high = indicators['pd_high']
        pd_low = indicators['pd_low']
        pd_close = indicators['pd_close']
        if pd_high and pd_low and pd_close:
            stats_html.append(f"""
                <div class="stat-item indicator">
                    <div class="stat-label">PD High</div>
                    <div class="stat-value" style="color: #2196F3">${pd_high:,.2f}</div>
                </div>
            """)
            stats_html.append(f"""
                <div class="stat-item indicator">
                    <div class="stat-label">PD Low</div>
                    <div class="stat-value" style="color: #2196F3">${pd_low:,.2f}</div>
                </div>
            """)
            stats_html.append(f"""
                <div class="stat-item indicator">
                    <div class="stat-label">PD Close</div>
                    <div class="stat-value" style="color: #FF9800">${pd_close:,.2f}</div>
                </div>
            """)
    
    return ''.join(stats_html)


def generate_chart_html(symbol: str, interval: str, data: List[Dict], patterns: List = None, indicators: Dict[str, Any] = None) -> str:
    """Generate HTML candlestick chart with pattern highlighting and indicators"""
    
    if not data:
        return f"<p>No data available for {symbol} {interval}</p>"
    
    patterns = patterns or []
    indicators = indicators or {}
    
    # Prepare candlestick data with pattern highlighting
    candles = []
    volumes = []
    pattern_highlights = []
    
    # Build a set of indices that are part of patterns
    pattern_indices = set()
    pattern_info = {}  # idx -> (pattern_name, pattern_type, fib_data)
    
    for pattern in patterns:
        for idx in range(pattern.start_idx, pattern.end_idx + 1):
            if idx < len(data):
                pattern_indices.add(idx)
                if idx == pattern.start_idx:
                    # Include Fibonacci data if available
                    fib_data = {
                        'near_fibonacci': getattr(pattern, 'near_fibonacci', False),
                        'fibonacci_level': getattr(pattern, 'fibonacci_level', None)
                    }
                    pattern_info[idx] = (pattern.name, pattern.type, fib_data)
    
    for i, d in enumerate(data):
        timestamp = int(d['timestamp'] / 1000)
        
        is_pattern_candle = i in pattern_indices
        outline_color = None
        fib_data = {'near_fibonacci': False, 'fibonacci_level': None}
        if i in pattern_info:
            _, ptype, fib_data = pattern_info[i]
            outline_color = get_pattern_outline_color(ptype)
        
        candle_data = {
            'time': timestamp,
            'open': round(d['open'], 2),
            'high': round(d['high'], 2),
            'low': round(d['low'], 2),
            'close': round(d['close'], 2)
        }
        
        if outline_color:
            candle_data['borderColor'] = outline_color
            candle_data['wickColor'] = outline_color
        
        candles.append(candle_data)
        
        # Volume bars
        color = COLORS['up'] if d['close'] >= d['open'] else COLORS['down']
        volumes.append({
            'time': timestamp,
            'value': round(d['volume'], 4),
            'color': color
        })
        
        # Store pattern highlight info
        if i in pattern_info:
            name, ptype, fib_data = pattern_info[i]
            pattern_highlights.append({
                'time': timestamp,
                'name': name,
                'type': str(ptype),
                'color': outline_color,
                'index': i,
                'near_fibonacci': fib_data.get('near_fibonacci', False),
                'fibonacci_level': fib_data.get('fibonacci_level')
            })
    
    # Calculate price range for y-axis
    highs = [d['high'] for d in data]
    lows = [d['low'] for d in data]
    price_range = max(highs) - min(lows)
    price_padding = price_range * 0.1
    
    # Latest price info
    latest = data[-1]
    prev = data[-2] if len(data) > 1 else latest
    change = latest['close'] - prev['close']
    change_pct = (change / prev['close']) * 100 if prev['close'] else 0
    
    # Generate pattern legend HTML
    legend_html = generate_pattern_legend(patterns)
    
    # Generate pattern markers JavaScript
    pattern_markers_js = []
    for ph in pattern_highlights:
        position = 'aboveBar' if 'bearish' in ph['type'].lower() else 'belowBar'
        shape = 'arrowDown' if 'bearish' in ph['type'].lower() else 'arrowUp'
        
        # Check if pattern has Fibonacci correlation
        fib_text = ""
        if ph.get('near_fibonacci') and ph.get('fibonacci_level'):
            fib_text = f" @ Fib {ph['fibonacci_level']}"
        
        pattern_markers_js.append(f"""
        {{
            time: {ph['time']},
            position: '{position}',
            color: '{ph['color']}',
            shape: '{shape}',
            text: '{ph['name'].upper()}{fib_text}',
            size: 2
        }}
        """)
    
    markers_js = ',\n'.join(pattern_markers_js) if pattern_markers_js else ''
    
    # Generate indicator series data
    indicator_series_js = []
    indicator_series_data = {}
    
    # EMA series
    for key in ['ema9', 'ema21', 'ema25', 'ema50', 'ema200']:
        if key in indicators and indicators[key]:
            ema_data = []
            for i, d in enumerate(data):
                if indicators[key][i] is not None:
                    ema_data.append({
                        'time': int(d['timestamp'] / 1000),
                        'value': round(indicators[key][i], 2)
                    })
            if ema_data:
                indicator_series_data[key] = ema_data
                period = key.replace('ema', '')
                indicator_series_js.append(f"""
                // EMA{period} series
                const ema{period}Series = chart.addLineSeries({{
                    color: '{COLORS[key]}',
                    lineWidth: 2,
                    title: 'EMA{period}',
                    priceLineVisible: false,
                    priceScaleId: 'right',
                }});
                ema{period}Series.setData({json.dumps(ema_data)});
                """)
    
    # Bollinger Bands
    if 'bb_middle' in indicators and indicators['bb_middle']:
        bb_upper_data = []
        bb_lower_data = []
        for i, d in enumerate(data):
            if indicators['bb_upper'][i] is not None and indicators['bb_lower'][i] is not None:
                timestamp = int(d['timestamp'] / 1000)
                bb_upper_data.append({
                    'time': timestamp,
                    'value': round(indicators['bb_upper'][i], 2)
                })
                bb_lower_data.append({
                    'time': timestamp,
                    'value': round(indicators['bb_lower'][i], 2)
                })
        if bb_upper_data and bb_lower_data:
            indicator_series_js.append(f"""
            // Bollinger Bands Upper
            const bbUpperSeries = chart.addLineSeries({{
                color: '#9E9E9E',
                lineWidth: 1,
                title: 'BB Upper',
                priceLineVisible: false,
                priceScaleId: 'right',
            }});
            bbUpperSeries.setData({json.dumps(bb_upper_data)});
            
            // Bollinger Bands Lower
            const bbLowerSeries = chart.addLineSeries({{
                color: '#9E9E9E',
                lineWidth: 1,
                title: 'BB Lower',
                priceLineVisible: false,
                priceScaleId: 'right',
            }});
            bbLowerSeries.setData({json.dumps(bb_lower_data)});
            """)
    
    # Previous Day Levels (for intraday)
    if 'pd_high' in indicators and indicators['pd_high']:
        start_time = int(data[0]['timestamp'] / 1000)
        end_time = int(data[-1]['timestamp'] / 1000)
        pd_high = indicators['pd_high']
        pd_low = indicators['pd_low']
        pd_close = indicators['pd_close']
        
        if pd_high and pd_low and pd_close:
            indicator_series_js.append(f"""
            // Previous Day High
            const pdHighData = [
                {{'time': {start_time}, 'value': {pd_high}}},
                {{'time': {end_time}, 'value': {pd_high}}}
            ];
            const pdHighSeries = chart.addLineSeries({{
                color: '#2196F3',
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                title: 'PD High',
                priceLineVisible: false,
                priceScaleId: 'right',
            }});
            pdHighSeries.setData(pdHighData);
            
            // Previous Day Low
            const pdLowData = [
                {{'time': {start_time}, 'value': {pd_low}}},
                {{'time': {end_time}, 'value': {pd_low}}}
            ];
            const pdLowSeries = chart.addLineSeries({{
                color: '#2196F3',
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                title: 'PD Low',
                priceLineVisible: false,
                priceScaleId: 'right',
            }});
            pdLowSeries.setData(pdLowData);
            
            // Previous Day Close
            const pdCloseData = [
                {{'time': {start_time}, 'value': {pd_close}}},
                {{'time': {end_time}, 'value': {pd_close}}}
            ];
            const pdCloseSeries = chart.addLineSeries({{
                color: '#FF9800',
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                title: 'PD Close',
                priceLineVisible: false,
                priceScaleId: 'right',
            }});
            pdCloseSeries.setData(pdCloseData);
            """)
    if 'vwap' in indicators and indicators['vwap']:
        vwap_data = []
        for i, d in enumerate(data):
            if indicators['vwap'][i] is not None:
                vwap_data.append({
                    'time': int(d['timestamp'] / 1000),
                    'value': round(indicators['vwap'][i], 2)
                })
        if vwap_data:
            indicator_series_js.append(f"""
            // VWAP series
            const vwapSeries = chart.addLineSeries({{
                color: '{COLORS['vwap']}',
                lineWidth: 2,
                title: 'VWAP',
                lineStyle: LightweightCharts.LineStyle.LargeDashed,
                priceLineVisible: false,
                priceScaleId: 'right',
            }});
            vwapSeries.setData({json.dumps(vwap_data)});
            """)
    
    # Volume SMA20 overlay
    if 'volume_sma20' in indicators and indicators['volume_sma20']:
        vol_sma_data = []
        for i, d in enumerate(data):
            if indicators['volume_sma20'][i] is not None:
                vol_sma_data.append({
                    'time': int(d['timestamp'] / 1000),
                    'value': round(indicators['volume_sma20'][i], 4)
                })
        if vol_sma_data:
            indicator_series_js.append(f"""
            // Volume SMA20 overlay
            const volumeSmaSeries = chart.addLineSeries({{
                color: '#FFEB3B',
                lineWidth: 1,
                title: 'Vol SMA20',
                priceScaleId: '',
                scaleMargins: {{
                    top: 0.85,
                    bottom: 0,
                }},
            }});
            volumeSmaSeries.setData({json.dumps(vol_sma_data)});
            """)
    
    # MACD series - only for timeframes that have MACD config
    if 'macd_line' in indicators and indicators['macd_line']:
        macd_line_data = []
        macd_signal_data = []
        macd_histogram_data = []
        
        for i, d in enumerate(data):
            timestamp = int(d['timestamp'] / 1000)
            if indicators['macd_line'][i] is not None:
                macd_line_data.append({
                    'time': timestamp,
                    'value': round(indicators['macd_line'][i], 4)
                })
            if indicators['macd_signal'][i] is not None:
                macd_signal_data.append({
                    'time': timestamp,
                    'value': round(indicators['macd_signal'][i], 4)
                })
            if indicators['macd_line'][i] is not None and indicators['macd_signal'][i] is not None:
                hist_value = indicators['macd_line'][i] - indicators['macd_signal'][i]
                hist_color = COLORS['macd_histogram_up'] if hist_value >= 0 else COLORS['macd_histogram_down']
                macd_histogram_data.append({
                    'time': timestamp,
                    'value': round(hist_value, 4),
                    'color': hist_color
                })
        
        if macd_line_data and macd_signal_data:
            indicator_series_js.append(f"""
            // MACD Line
            const macdLineSeries = chart.addLineSeries({{
                color: '{COLORS['macd_line']}',
                lineWidth: 2,
                title: 'MACD',
                priceLineVisible: false,
                priceScaleId: 'macd',
                scaleMargins: {{
                    top: 0.8,
                    bottom: 0,
                }},
            }});
            macdLineSeries.setData({json.dumps(macd_line_data)});
            
            // MACD Signal Line
            const macdSignalSeries = chart.addLineSeries({{
                color: '{COLORS['macd_signal']}',
                lineWidth: 2,
                title: 'Signal',
                priceLineVisible: false,
                priceScaleId: 'macd',
                scaleMargins: {{
                    top: 0.8,
                    bottom: 0,
                }},
            }});
            macdSignalSeries.setData({json.dumps(macd_signal_data)});
            
            // MACD Histogram
            const macdHistogramSeries = chart.addHistogramSeries({{
                priceScaleId: 'macd',
                scaleMargins: {{
                    top: 0.8,
                    bottom: 0,
                }},
            }});
            macdHistogramSeries.setData({json.dumps(macd_histogram_data)});
            """)
    
    # RSI Panel - separate price scale below main chart
    if 'rsi' in indicators and indicators['rsi']:
        rsi_data = []
        for i, d in enumerate(data):
            if indicators['rsi'][i] is not None:
                rsi_data.append({
                    'time': int(d['timestamp'] / 1000),
                    'value': round(indicators['rsi'][i], 1)
                })
        if rsi_data:
            indicator_series_js.append(f"""
            // RSI Panel
            const rsiSeries = chart.addLineSeries({{
                color: '{COLORS['rsi']}',
                lineWidth: 2,
                title: 'RSI',
                priceLineVisible: false,
                priceScaleId: 'rsi',
                scaleMargins: {{
                    top: 0.8,
                    bottom: 0,
                }},
            }});
            rsiSeries.setData({json.dumps(rsi_data)});
            
            // Add RSI overbought line (70)
            const rsiOverboughtData = [
                {{'time': {rsi_data[0]['time']}, 'value': 70}},
                {{'time': {rsi_data[-1]['time']}, 'value': 70}}
            ];
            const rsiOverboughtSeries = chart.addLineSeries({{
                color: '#ef5350',
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                priceScaleId: 'rsi',
                scaleMargins: {{
                    top: 0.8,
                    bottom: 0,
                }},
                lastValueVisible: false,
                title: '',
            }});
            rsiOverboughtSeries.setData(rsiOverboughtData);
            
            // Add RSI oversold line (30)
            const rsiOversoldData = [
                {{'time': {rsi_data[0]['time']}, 'value': 30}},
                {{'time': {rsi_data[-1]['time']}, 'value': 30}}
            ];
            const rsiOversoldSeries = chart.addLineSeries({{
                color: '#26a69a',
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                priceScaleId: 'rsi',
                scaleMargins: {{
                    top: 0.8,
                    bottom: 0,
                }},
                lastValueVisible: false,
                title: '',
            }});
            rsiOversoldSeries.setData(rsiOversoldData);
            """)
    
    # Fibonacci retracement lines - horizontal lines at key levels
    if 'fibonacci' in indicators and indicators['fibonacci']:
        fib_levels = indicators['fibonacci']
        fib_data_by_level = {}
        
        # Get time range for the data
        start_time = int(data[0]['timestamp'] / 1000)
        end_time = int(data[-1]['timestamp'] / 1000)
        
        for level_name, level_value in fib_levels.items():
            if level_value is not None:
                # Create a horizontal line across the chart
                fib_data_by_level[level_name] = [
                    {'time': start_time, 'value': round(level_value, 2)},
                    {'time': end_time, 'value': round(level_value, 2)}
                ]
        
        # Add Fibonacci lines with appropriate colors
        fib_colors = {
            '0.0': COLORS['fib_236'],  # Use as approximation for 0%
            '0.236': COLORS['fib_236'],
            '0.382': COLORS['fib_382'],
            '0.5': COLORS['fib_500'],
            '0.618': COLORS['fib_618'],
            '0.786': COLORS['fib_786'],
            '1.0': COLORS['fib_236'],  # Use as approximation for 100%
        }
        
        fib_series_js = []
        for level_name, level_data in fib_data_by_level.items():
            color = fib_colors.get(level_name, '#9E9E9E')
            label = f"Fib {level_name}"
            fib_series_js.append(f"""
            // Fibonacci {level_name} level
            const fib{level_name.replace('.', '_')}Series = chart.addLineSeries({{
                color: '{color}',
                lineWidth: 1,
                title: '{label}',
                priceLineVisible: false,
                priceScaleId: 'right',
                lineStyle: LightweightCharts.LineStyle.Dashed,
            }});
            fib{level_name.replace('.', '_')}Series.setData({json.dumps(level_data)});
            """)
        
        if fib_series_js:
            indicator_series_js.extend(fib_series_js)
    
    # Pattern summary for display
    pattern_summary_html = ""
    if patterns and PatternDetector:
        pattern_summary = PatternDetector(data).get_pattern_summary() if patterns else {}
        if pattern_summary:
            items = [f"{name}: {count}" for name, count in sorted(pattern_summary.items())]
            pattern_summary_html = f"<div class='pattern-summary'>{', '.join(items)}</div>"
    
    # Indicator stats
    indicator_stats_html = generate_indicator_stats(indicators, data)
    
    # Get config for display
    # Map interval to config key
    interval_key = interval.lower()
    if interval_key == '1m':
        interval_key = '1M'
    config = TIMEFRAME_CONFIGS.get(interval_key, TIMEFRAME_CONFIGS['1h'])
    indicator_list = []
    if config.ema_periods:
        indicator_list.append(f"EMA{','.join(map(str, config.ema_periods))}")
    if config.rsi_period:
        indicator_list.append(f"RSI({config.rsi_period})")
    if config.macd_fast:
        indicator_list.append(f"MACD")
    if config.vwap_type:
        indicator_list.append(f"VWAP")
    if config.atr_period:
        indicator_list.append(f"ATR({config.atr_period})")
    if config.show_fibonacci:
        indicator_list.append("Fib")
    if config.show_sr:
        indicator_list.append("S/R")
    
    indicator_badge = f" • {', '.join(indicator_list)}" if indicator_list else ""
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{symbol} {interval} Chart - Pattern & Indicator Enhanced</title>
    <script src="https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            background: {COLORS['bg']}; 
            color: {COLORS['text']}; 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            padding: 20px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid {COLORS['grid']};
        }}
        .symbol-info h1 {{
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 5px;
        }}
        .interval {{
            font-size: 14px;
            color: #787b86;
        }}
        .price-info {{
            text-align: right;
        }}
        .current-price {{
            font-size: 28px;
            font-weight: 600;
        }}
        .price-change {{
            font-size: 16px;
            margin-top: 5px;
        }}
        .positive {{ color: {COLORS['up']}; }}
        .negative {{ color: {COLORS['down']}; }}
        .chart-wrapper {{
            position: relative;
            width: 100%;
            height: 800px;
        }}
        #chart-container {{
            width: 100%;
            height: 100%;
            background: {COLORS['bg']};
            border-radius: 8px;
        }}
        .pattern-legend {{
            position: absolute;
            bottom: 10px;
            right: 10px;
            background: rgba(19, 23, 34, 0.95);
            border: 1px solid {COLORS['grid']};
            border-radius: 8px;
            padding: 12px;
            min-width: 180px;
            max-width: 250px;
            font-size: 12px;
            z-index: 100;
        }}
        .legend-title {{
            font-weight: 600;
            margin-bottom: 8px;
            color: {COLORS['text']};
            border-bottom: 1px solid {COLORS['grid']};
            padding-bottom: 6px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 6px 0;
        }}
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 2px;
            margin-right: 8px;
            border: 1px solid rgba(255,255,255,0.3);
        }}
        .legend-text {{
            color: #b0b3b8;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin-top: 20px;
            padding: 15px;
            background: {COLORS['grid']};
            border-radius: 8px;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-item.indicator {{
            border-left: 2px solid {COLORS['grid']};
            padding-left: 10px;
        }}
        .stat-label {{
            font-size: 11px;
            color: #787b86;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .stat-value {{
            font-size: 15px;
            font-weight: 600;
        }}
        .rsi-status {{
            font-size: 11px;
            color: #787b86;
        }}
        .pattern-summary {{
            margin-top: 15px;
            padding: 10px 15px;
            background: rgba(0, 255, 0, 0.05);
            border: 1px solid rgba(0, 255, 0, 0.2);
            border-radius: 6px;
            font-size: 13px;
            color: #a0a3a8;
        }}
        .pattern-highlight {{
            transition: opacity 0.3s;
        }}
        .pattern-highlight:hover {{
            opacity: 0.8;
        }}
        .indicator-legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 10px;
            padding: 10px;
            background: rgba(42, 46, 57, 0.5);
            border-radius: 6px;
            font-size: 12px;
        }}
        .indicator-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .indicator-color {{
            width: 20px;
            height: 3px;
            border-radius: 1px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="symbol-info">
            <h1>{symbol}</h1>
            <span class="interval">{interval} Interval • Pattern Enhanced{indicator_badge}</span>
        </div>
        <div class="price-info">
            <div class="current-price">${latest['close']:,.2f}</div>
            <div class="price-change {'positive' if change >= 0 else 'negative'}">
                {'+' if change >= 0 else ''}{change:,.2f} ({'+' if change_pct >= 0 else ''}{change_pct:.2f}%)
            </div>
        </div>
    </div>
    
    <div class="chart-wrapper">
        <div id="chart-container"></div>
        {legend_html}
    </div>
    
    {pattern_summary_html}
    
    <div class="stats">
        <div class="stat-item">
            <div class="stat-label">Open</div>
            <div class="stat-value">${latest['open']:,.2f}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">High</div>
            <div class="stat-value">${latest['high']:,.2f}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Low</div>
            <div class="stat-value">${latest['low']:,.2f}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Volume</div>
            <div class="stat-value">{latest['volume']:,.2f}</div>
        </div>
        {indicator_stats_html}
    </div>

    <script>
        const chartContainer = document.getElementById('chart-container');
        
        const chart = LightweightCharts.createChart(chartContainer, {{
            layout: {{
                background: {{ color: '{COLORS['bg']}' }},
                textColor: '{COLORS['text']}',
            }},
            grid: {{
                vertLines: {{ color: '{COLORS['grid']}' }},
                horzLines: {{ color: '{COLORS['grid']}' }},
            }},
            crosshair: {{
                mode: LightweightCharts.CrosshairMode.Normal,
            }},
            rightPriceScale: {{
                borderColor: '{COLORS['grid']}',
            }},
            leftPriceScale: {{
                visible: false,
            }},
            timeScale: {{
                borderColor: '{COLORS['grid']}',
                timeVisible: true,
                secondsVisible: false,
            }},
        }});
        
        // Configure RSI price scale if RSI data exists
        const hasRSI = {str('rsi' in indicators and indicators['rsi'] is not None).lower()};
        if (hasRSI) {{
            chart.priceScale('rsi').applyOptions({{
                visible: true,
                borderColor: '{COLORS['grid']}',
                scaleMargins: {{
                    top: 0.1,
                    bottom: 0.1,
                }},
            }});
        }}
        
        // Candlestick series with custom colors for patterns
        const candleSeries = chart.addCandlestickSeries({{
            upColor: '{COLORS['up']}',
            downColor: '{COLORS['down']}',
            borderUpColor: '{COLORS['up']}',
            borderDownColor: '{COLORS['down']}',
            wickUpColor: '{COLORS['up']}',
            wickDownColor: '{COLORS['down']}',
        }});
        
        const candleData = {json.dumps(candles)};
        candleSeries.setData(candleData);
        
        // Volume histogram
        const volumeSeries = chart.addHistogramSeries({{
            color: '{COLORS['up']}',
            priceFormat: {{
                type: 'volume',
            }},
            priceScaleId: '',
            scaleMargins: {{
                top: 0.85,
                bottom: 0,
            }},
        }});
        
        volumeSeries.setData({json.dumps(volumes)});
        
        // Add indicator series
        {' '.join(indicator_series_js)}
        
        // Add pattern markers
        const markers = [{markers_js}];
        if (markers.length > 0) {{
            candleSeries.setMarkers(markers);
        }}
        
        // Fit content
        chart.timeScale().fitContent();
        
        // Handle resize
        window.addEventListener('resize', () => {{
            chart.applyOptions({{ width: chartContainer.clientWidth }});
        }});
    </script>
</body>
</html>'''
    
    return html


def generate_all_charts():
    """Generate pattern-enhanced charts with indicators for all symbols and intervals"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    intervals = ['5m', '15m', '1h', '4h', '1d', '1w', '1M']
    
    generated = []
    total_patterns = 0
    
    for symbol in symbols:
        for interval in intervals:
            print(f"Generating chart for {symbol} {interval}...")
            
            data = load_ohlcv_data(symbol, interval)
            
            if not data:
                print(f"  ✗ No data available")
                continue
            
            # Detect patterns with Fibonacci correlation
            patterns = []
            if PatternDetector:
                detector = PatternDetector(data)
                
                # Calculate Fibonacci levels for pattern correlation
                fib_levels = None
                if len(data) >= 20:
                    recent_high = max(d['high'] for d in data[-20:])
                    recent_low = min(d['low'] for d in data[-20:])
                    fib_levels = calculate_fibonacci_retracement(recent_high, recent_low)
                
                # Detect patterns with Fibonacci correlation
                patterns = detector.detect_all_patterns_with_fibonacci(fib_levels)
                pattern_count = len(patterns)
                total_patterns += pattern_count
                
                # Count patterns at Fibonacci levels
                fib_patterns = sum(1 for p in patterns if getattr(p, 'near_fibonacci', False))
                if fib_patterns > 0:
                    print(f"    ({fib_patterns} patterns at Fibonacci levels)")
            else:
                pattern_count = 0
            
            # Calculate indicators
            indicators = calculate_all_indicators(data, interval)
            
            # Generate chart with patterns and indicators
            html = generate_chart_html(symbol, interval, data, patterns, indicators)
            
            # Save individual chart
            chart_file = OUTPUT_DIR / f"{symbol}_{interval}.html"
            with open(chart_file, 'w') as f:
                f.write(html)
            
            pattern_summary = {}
            if PatternDetector and patterns:
                pattern_summary = detector.get_pattern_summary()
            
            indicator_summary = []
            # Map interval to config key
            interval_key = interval.lower()
            if interval_key == '1m':
                interval_key = '1M'  # Special case for monthly
            config = TIMEFRAME_CONFIGS.get(interval_key, TIMEFRAME_CONFIGS['1h'])
            if config.ema_periods:
                indicator_summary.append(f"EMA{','.join(map(str, config.ema_periods))}")
            if config.rsi_period:
                indicator_summary.append(f"RSI({config.rsi_period})")
            if config.macd_fast:
                indicator_summary.append("MACD")
            if config.vwap_type:
                indicator_summary.append("VWAP")
            if config.atr_period:
                indicator_summary.append(f"ATR({config.atr_period})")
            
            generated.append({
                'symbol': symbol,
                'interval': interval,
                'file': str(chart_file),
                'candles': len(data),
                'patterns': pattern_count,
                'pattern_summary': pattern_summary,
                'indicators': indicator_summary
            })
            
            print(f"  ✓ Saved {chart_file} ({len(data)} candles, {pattern_count} patterns)")
            print(f"    Indicators: {', '.join(indicator_summary)}")
    
    # Generate index page
    generate_index_page(generated)
    
    return generated, total_patterns


def generate_index_page(charts: List[Dict]):
    """Generate an index page with links to all charts"""
    
    total_patterns = sum(c.get('patterns', 0) for c in charts)
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Pattern & Indicator Enhanced Binance Charts</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            background: #131722; 
            color: #d1d4dc; 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            padding: 40px;
        }}
        h1 {{ 
            font-size: 32px; 
            margin-bottom: 10px;
            text-align: center;
        }}
        .subtitle {{
            text-align: center;
            color: #787b86;
            margin-bottom: 30px;
        }}
        .stats-bar {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-bottom: 40px;
            padding: 20px;
            background: #2a2e39;
            border-radius: 12px;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: 600;
            color: #26a69a;
        }}
        .stat-label {{
            font-size: 12px;
            color: #787b86;
            margin-top: 5px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        .chart-card {{
            background: #2a2e39;
            border-radius: 12px;
            padding: 20px;
            text-decoration: none;
            color: inherit;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .chart-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        .symbol {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 5px;
        }}
        .interval {{
            font-size: 14px;
            color: #787b86;
            margin-bottom: 10px;
        }}
        .indicators {{
            font-size: 11px;
            color: #00BCD4;
            margin-bottom: 8px;
            padding: 4px 8px;
            background: rgba(0, 188, 212, 0.1);
            border-radius: 4px;
            display: inline-block;
        }}
        .pattern-count {{
            font-size: 12px;
            color: #00FF00;
            margin-bottom: 15px;
        }}
        .pattern-count.zero {{
            color: #787b86;
        }}
        .preview {{
            width: 100%;
            height: 150px;
            background: #131722;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 48px;
        }}
        .candles-count {{
            font-size: 12px;
            color: #787b86;
            margin-top: 10px;
            text-align: right;
        }}
        .btc {{ color: #f7931a; }}
        .eth {{ color: #627eea; }}
        .bnb {{ color: #f3ba2f; }}
        .legend {{
            margin-top: 40px;
            padding: 20px;
            background: #2a2e39;
            border-radius: 12px;
            max-width: 1000px;
            margin-left: auto;
            margin-right: auto;
        }}
        .legend h3 {{
            margin-bottom: 15px;
            color: #d1d4dc;
        }}
        .legend-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 10px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            font-size: 13px;
        }}
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
            margin-right: 10px;
            border: 2px solid;
        }}
        .legend-color.bullish {{
            background-color: rgba(0, 255, 0, 0.2);
            border-color: #00FF00;
        }}
        .legend-color.bearish {{
            background-color: rgba(255, 0, 0, 0.2);
            border-color: #FF0000;
        }}
        .legend-color.neutral {{
            background-color: rgba(255, 255, 0, 0.2);
            border-color: #FFFF00;
        }}
        .indicator-colors {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #3a3e49;
        }}
        .indicator-colors h4 {{
            margin-bottom: 10px;
            color: #787b86;
        }}
        .indicator-color-item {{
            display: flex;
            align-items: center;
            margin: 5px 0;
            font-size: 12px;
        }}
        .indicator-line {{
            width: 30px;
            height: 3px;
            margin-right: 10px;
            border-radius: 1px;
        }}
    </style>
</head>
<body>
    <h1>📊 Pattern & Indicator Enhanced Charts</h1>
    <p class="subtitle">Japanese Candlestick Pattern Detection with Timeframe-Specific Indicators</p>
    
    <div class="stats-bar">
        <div class="stat">
            <div class="stat-value">{len(charts)}</div>
            <div class="stat-label">Charts</div>
        </div>
        <div class="stat">
            <div class="stat-value">{total_patterns}</div>
            <div class="stat-label">Patterns Detected</div>
        </div>
        <div class="stat">
            <div class="stat-value">7</div>
            <div class="stat-label">Timeframes</div>
        </div>
    </div>
    
    <div class="grid">
'''
    
    for chart in charts:
        symbol_class = chart['symbol'][:3].lower()
        emoji = {'BTCUSDT': '₿', 'ETHUSDT': 'Ξ', 'BNBUSDT': '🔶'}.get(chart['symbol'], '📈')
        pattern_count = chart.get('patterns', 0)
        pattern_class = 'zero' if pattern_count == 0 else ''
        indicators_str = ', '.join(chart.get('indicators', []))
        
        html += f'''
        <a href="{chart['symbol']}_{chart['interval']}.html" class="chart-card">
            <div class="symbol {symbol_class}">{chart['symbol']}</div>
            <div class="interval">{chart['interval']} Interval</div>
            <div class="indicators">{indicators_str}</div>
            <div class="pattern-count {pattern_class}">{pattern_count} patterns detected</div>
            <div class="preview {symbol_class}">{emoji}</div>
            <div class="candles-count">{chart['candles']} candles</div>
        </a>
'''
    
    html += '''
    </div>
    
    <div class="legend">
        <h3>Pattern Legend</h3>
        <div class="legend-grid">
            <div class="legend-item">
                <span class="legend-color bullish"></span>
                <span>Bullish Patterns (Green Outline)</span>
            </div>
            <div class="legend-item">
                <span class="legend-color bearish"></span>
                <span>Bearish Patterns (Red Outline)</span>
            </div>
            <div class="legend-item">
                <span class="legend-color neutral"></span>
                <span>Neutral Patterns (Yellow Outline)</span>
            </div>
        </div>
        
        <div class="indicator-colors">
            <h4>Indicator Colors</h4>
            <div class="indicator-color-item"><span class="indicator-line" style="background: #FF6D00;"></span>EMA9</div>
            <div class="indicator-color-item"><span class="indicator-line" style="background: #00BCD4;"></span>EMA21</div>
            <div class="indicator-color-item"><span class="indicator-line" style="background: #9C27B0;"></span>EMA25</div>
            <div class="indicator-color-item"><span class="indicator-line" style="background: #2196F3;"></span>EMA50</div>
            <div class="indicator-color-item"><span class="indicator-line" style="background: #E91E63;"></span>EMA200</div>
            <div class="indicator-color-item"><span class="indicator-line" style="background: #FFD700;"></span>VWAP (dashed)</div>
        </div>
        
        <p style="margin-top: 15px; font-size: 12px; color: #787b86;">
            Timeframe-specific indicators: 5M (EMA9,RSI5,VWAP,ATR5), 15M (EMA9/21/50,RSI7,VWAP,ATR7), 
            1H (EMA9/25,RSI14,VWAP,ATR14), 4H (EMA9/21,RSI14,MACD,VWAP,ATR14), 
            1D (EMA20/50,RSI14,MACD,VWAP,ATR14,Fib), 1W/1M (EMA50/200,MACD,Fib,S/R)
        </p>
    </div>
</body>
</html>'''
    
    index_file = OUTPUT_DIR / 'index.html'
    with open(index_file, 'w') as f:
        f.write(html)
    
    print(f"\n✓ Index page saved: {index_file}")


def main():
    """Main execution"""
    print("=" * 70)
    print("PATTERN & INDICATOR ENHANCED CANDLESTICK CHART GENERATOR")
    print("=" * 70)
    
    charts, total_patterns = generate_all_charts()
    
    print("\n" + "=" * 70)
    print(f"Generated {len(charts)} charts with {total_patterns} total patterns detected")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"View index: file://{OUTPUT_DIR}/index.html")
    print("=" * 70)


if __name__ == '__main__':
    main()
