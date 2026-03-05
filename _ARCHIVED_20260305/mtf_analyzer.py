#!/usr/bin/env python3
"""
Multi-Timeframe (MTF) Analyzer
Performs comprehensive technical analysis across multiple timeframes
for BTC, ETH, and BNB to generate trading signals and market bias.
"""

import requests
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

# Configuration
DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
MTF_DIR = Path('/root/.openclaw/workspace/mtf_analysis')
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']

# Timeframes from highest to lowest (for hierarchical analysis)
TIMEFRAMES = ['1M', '1w', '1d', '4h', '1h', '15m', '5m']

# Binance API
BASE_URL = 'https://api.binance.com'

def fetch_klines(symbol: str, interval: str, limit: int = 500) -> List[Dict]:
    """Fetch OHLCV data from Binance"""
    url = f"{BASE_URL}/api/v3/klines"
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        processed = []
        for k in data:
            processed.append({
                'open_time': int(k[0]),
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5]),
                'close_time': int(k[6])
            })
        return processed
    except Exception as e:
        print(f"Error fetching {symbol} {interval}: {e}")
        return []

def calculate_ema(data: List[float], period: int) -> List[float]:
    """Calculate EMA for a data series"""
    if len(data) < period:
        return []
    
    multiplier = 2 / (period + 1)
    ema = [sum(data[:period]) / period]  # SMA for first value
    
    for price in data[period:]:
        ema.append((price - ema[-1]) * multiplier + ema[-1])
    
    return ema

def calculate_rsi(closes: List[float], period: int = 14) -> float:
    """Calculate RSI for the latest value"""
    if len(closes) < period + 1:
        return 50.0
    
    gains = []
    losses = []
    
    for i in range(1, period + 1):
        change = closes[-i] - closes[-i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_fibonacci_levels(high: float, low: float) -> Dict[str, float]:
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

def determine_trend(closes: List[float], ema20: float, ema50: float) -> Tuple[str, float]:
    """Determine trend based on EMA alignment and price position"""
    if not closes or len(closes) < 2:
        return 'neutral', 50.0
    
    latest_close = closes[-1]
    
    # EMA alignment
    ema_bullish = ema20 > ema50
    ema_bearish = ema20 < ema50
    
    # Price relative to EMAs
    above_ema20 = latest_close > ema20
    above_ema50 = latest_close > ema50
    
    # Calculate trend strength (0-100)
    strength = 50.0
    
    if ema_bullish and above_ema20 and above_ema50:
        trend = 'bullish'
        strength = 70 + (latest_close - ema20) / ema20 * 1000
    elif ema_bearish and not above_ema20 and not above_ema50:
        trend = 'bearish'
        strength = 70 + (ema20 - latest_close) / ema20 * 1000
    else:
        trend = 'neutral'
        strength = 50.0
    
    # Cap strength at 100
    strength = min(100, strength)
    
    return trend, strength

def find_nearest_fib_level(price: float, fib_levels: Dict[str, float]) -> Tuple[str, float]:
    """Find the nearest Fibonacci level to current price"""
    min_diff = float('inf')
    nearest_level = 'none'
    nearest_price = price
    
    for level, level_price in fib_levels.items():
        diff = abs(price - level_price)
        if diff < min_diff:
            min_diff = diff
            nearest_level = level
            nearest_price = level_price
    
    return nearest_level, nearest_price

def analyze_timeframe(symbol: str, interval: str, higher_tf_bias: str = 'unknown') -> Dict:
    """Analyze a single timeframe"""
    # Fetch data
    data = fetch_klines(symbol, interval, limit=200)
    
    if not data or len(data) < 50:
        return {
            'interval': interval,
            'error': 'Insufficient data'
        }
    
    closes = [d['close'] for d in data]
    highs = [d['high'] for d in data]
    lows = [d['low'] for d in data]
    
    latest_close = closes[-1]
    
    # Calculate EMAs
    ema20_values = calculate_ema(closes, 20)
    ema50_values = calculate_ema(closes, 50)
    
    ema20 = ema20_values[-1] if ema20_values else latest_close
    ema50 = ema50_values[-1] if ema50_values else latest_close
    
    # Calculate RSI
    rsi = calculate_rsi(closes, 14)
    
    # Key levels (recent high/low)
    recent_high = max(highs[-50:])
    recent_low = min(lows[-50:])
    
    # Fibonacci levels
    fib_levels = calculate_fibonacci_levels(recent_high, recent_low)
    
    # Determine trend
    trend, trend_strength = determine_trend(closes, ema20, ema50)
    
    # Check alignment with higher timeframe
    alignment = 'aligned' if trend == higher_tf_bias or higher_tf_bias == 'unknown' else 'misaligned'
    
    # Find nearest higher TF level if applicable
    near_higher_tf_level = 'none'
    higher_tf_level_value = None
    
    if higher_tf_bias != 'unknown':
        # Check if near key support/resistance
        for level_name, level_price in fib_levels.items():
            if abs(latest_close - level_price) / latest_close < 0.005:  # Within 0.5%
                near_higher_tf_level = 'fib'
                higher_tf_level_value = level_price
                break
    
    # Find nearest fib level
    at_fib, fib_price = find_nearest_fib_level(latest_close, fib_levels)
    
    # Calculate confidence based on multiple factors
    confidence_factors = []
    
    if trend != 'neutral':
        confidence_factors.append(min(trend_strength / 100, 1.0))
    
    if rsi < 30 or rsi > 70:
        confidence_factors.append(0.8)  # Overbought/oversold adds confidence
    
    if alignment == 'aligned':
        confidence_factors.append(0.9)
    
    confidence = 'medium'
    if len(confidence_factors) >= 2 and sum(confidence_factors) / len(confidence_factors) > 0.7:
        confidence = 'high'
    elif len(confidence_factors) >= 1 and sum(confidence_factors) / len(confidence_factors) > 0.5:
        confidence = 'medium'
    else:
        confidence = 'low'
    
    result = {
        'interval': interval,
        'trend': trend,
        'trend_strength': trend_strength,
        'rsi': rsi,
        'ema20': ema20,
        'ema50': ema50,
        'key_levels': {
            'high': recent_high,
            'low': recent_low
        },
        'fib_levels': fib_levels,
        'latest_close': latest_close,
        'higher_tf_bias': higher_tf_bias,
        'alignment_with_higher_tf': alignment,
        'near_higher_tf_level': near_higher_tf_level,
        'confidence': confidence
    }
    
    if higher_tf_level_value:
        result['higher_tf_level_value'] = higher_tf_level_value
    
    if at_fib != 'none':
        result['at_higher_tf_fib'] = at_fib
        result['higher_tf_fib_price'] = fib_price
    
    return result

def generate_trade_setup(timeframe_analysis: Dict[str, Dict]) -> Optional[Dict]:
    """Generate trade setup based on MTF analysis"""
    # Count aligned timeframes
    bullish_aligned = 0
    bearish_aligned = 0
    total_aligned = 0
    
    for tf, analysis in timeframe_analysis.items():
        if analysis.get('alignment_with_higher_tf') == 'aligned':
            total_aligned += 1
            if analysis.get('trend') == 'bullish':
                bullish_aligned += 1
            elif analysis.get('trend') == 'bearish':
                bearish_aligned += 1
    
    if total_aligned < 3:
        return None
    
    # Determine overall bias
    if bearish_aligned >= total_aligned * 0.7:
        bias = 'bearish'
        confidence = (bearish_aligned / total_aligned) * 100
    elif bullish_aligned >= total_aligned * 0.7:
        bias = 'bullish'
        confidence = (bullish_aligned / total_aligned) * 100
    else:
        bias = 'neutral'
        confidence = 50.0
    
    # Get entry/exit levels from lowest timeframe
    lowest_tf = list(timeframe_analysis.keys())[-1]
    lowest_analysis = timeframe_analysis[lowest_tf]
    
    fib_levels = lowest_analysis.get('fib_levels', {})
    latest_close = lowest_analysis.get('latest_close', 0)
    
    setup = {
        'bias': bias,
        'confidence': confidence,
        'entry_zone': {
            'min': fib_levels.get('0.618', latest_close * 0.99),
            'max': fib_levels.get('0.5', latest_close)
        },
        'stop_loss': fib_levels.get('0.786', latest_close * 0.97),
        'take_profit': fib_levels.get('0.382', latest_close * 1.02),
        'recommended_timeframe': lowest_tf
    }
    
    return setup

def analyze_symbol(symbol: str) -> Dict:
    """Perform complete MTF analysis for a symbol"""
    print(f"\n{'='*70}")
    print(f"Analyzing {symbol}")
    print('='*70)
    
    timeframe_analysis = {}
    higher_tf_bias = 'unknown'
    
    for interval in TIMEFRAMES:
        print(f"  Analyzing {interval}...", end=' ')
        
        analysis = analyze_timeframe(symbol, interval, higher_tf_bias)
        timeframe_analysis[interval] = analysis
        
        # Update higher TF bias for next iteration
        if analysis.get('trend') in ['bullish', 'bearish']:
            higher_tf_bias = analysis['trend']
        
        trend = analysis.get('trend', 'unknown')
        rsi = analysis.get('rsi', 0)
        confidence = analysis.get('confidence', 'low')
        
        print(f"{trend.upper()} | RSI: {rsi:.1f} | Confidence: {confidence}")
        
        time.sleep(0.2)  # Rate limiting
    
    # Generate trade setup
    trade_setup = generate_trade_setup(timeframe_analysis)
    
    # Calculate overall bias
    bullish_count = sum(1 for a in timeframe_analysis.values() if a.get('trend') == 'bullish')
    bearish_count = sum(1 for a in timeframe_analysis.values() if a.get('trend') == 'bearish')
    neutral_count = len(timeframe_analysis) - bullish_count - bearish_count
    
    if bearish_count > bullish_count and bearish_count > neutral_count:
        overall_bias = 'bearish'
    elif bullish_count > bearish_count and bullish_count > neutral_count:
        overall_bias = 'bullish'
    else:
        overall_bias = 'neutral'
    
    confidence_pct = max(bullish_count, bearish_count) / len(timeframe_analysis) * 100
    
    result = {
        'symbol': symbol,
        'timestamp': datetime.now().isoformat(),
        'overall_bias': overall_bias,
        'confidence': confidence_pct,
        'timeframe_analysis': timeframe_analysis,
        'trade_setup': trade_setup
    }
    
    return result

def save_analysis(result: Dict):
    """Save analysis results to JSON"""
    MTF_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"{result['symbol']}_mtf_{timestamp}.json"
    filepath = MTF_DIR / filename
    
    with open(filepath, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n  Saved to: {filepath}")
    return filepath

def print_summary(result: Dict):
    """Print formatted summary of analysis"""
    print(f"\n{'='*70}")
    print(f"SUMMARY: {result['symbol']}")
    print('='*70)
    print(f"Overall Bias: {result['overall_bias'].upper()}")
    print(f"Confidence: {result['confidence']:.1f}%")
    
    if result['trade_setup']:
        setup = result['trade_setup']
        print(f"\nTrade Setup:")
        print(f"  Bias: {setup['bias'].upper()}")
        print(f"  Entry Zone: ${setup['entry_zone']['min']:,.2f} - ${setup['entry_zone']['max']:,.2f}")
        print(f"  Stop Loss: ${setup['stop_loss']:,.2f}")
        print(f"  Take Profit: ${setup['take_profit']:,.2f}")
    else:
        print(f"\nTrade Setup: No clear setup (insufficient alignment)")
    
    print(f"\nTimeframe Breakdown:")
    for tf, analysis in result['timeframe_analysis'].items():
        trend = analysis.get('trend', 'N/A')
        rsi = analysis.get('rsi', 0)
        alignment = analysis.get('alignment_with_higher_tf', 'N/A')
        print(f"  {tf:4}: {trend:8} | RSI: {rsi:5.1f} | {alignment}")

def run_mtf_analysis():
    """Main function to run MTF analysis for all symbols"""
    print("="*70)
    print("MULTI-TIMEFRAME ANALYZER")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    all_results = []
    
    for symbol in SYMBOLS:
        result = analyze_symbol(symbol)
        save_analysis(result)
        print_summary(result)
        all_results.append(result)
        time.sleep(0.5)
    
    print(f"\n{'='*70}")
    print("ANALYSIS COMPLETE")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    return all_results

if __name__ == '__main__':
    run_mtf_analysis()
