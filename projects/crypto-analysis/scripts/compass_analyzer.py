#!/usr/bin/env python3
"""
COMPASS Indicator Calculator
Calculates all technical indicators per timeframe based on checklist specifications
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
FUTURES_DATA_DIR = Path('/root/.openclaw/workspace/data/binance_futures')
OUTPUT_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/analysis/compass')

# Indicator specifications per timeframe (from checklists)
TIMEFRAME_CONFIG = {
    '1w': {
        'ema_fast': 50,
        'ema_slow': 200,
        'rsi_period': 14,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'atr_period': 14,
        'volume_sma': 20,
        'category': 'Long-Term'
    },
    '1d': {
        'ema_fast': 20,
        'ema_slow': 50,
        'rsi_period': 14,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'atr_period': 14,
        'volume_sma': 20,
        'category': 'Daily'
    },
    '4h': {
        'ema_fast': 9,
        'ema_slow': 21,
        'rsi_period': 14,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'atr_period': 14,
        'volume_sma': 20,
        'category': 'Medium'
    },
    '1h': {
        'ema_fast': 9,
        'ema_slow': 25,
        'rsi_period': 14,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'atr_period': 14,
        'volume_sma': 20,
        'category': 'Short'
    },
    '15m': {
        'ema_fast': 9,
        'ema_mid': 21,
        'ema_slow': 50,
        'rsi_period': 7,
        'atr_period': 7,
        'volume_sma': 20,
        'category': 'Ultra-Short'
    },
    '5m': {
        'ema_fast': 9,
        'rsi_period': 5,
        'atr_period': 5,
        'volume_sma': 20,
        'category': 'Scalp'
    }
}

def load_ohlcv(symbol, interval):
    """Load OHLCV data from CSV"""
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    if not filepath.exists():
        return None
    
    df = pd.read_csv(filepath)
    df['datetime'] = pd.to_datetime(df['open_time'], unit='ms')
    df = df.sort_values('datetime')
    return df

def calculate_ema(series, period):
    """Calculate Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()

def calculate_rsi(series, period=14):
    """Calculate Relative Strength Index"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(series, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    ema_fast = calculate_ema(series, fast)
    ema_slow = calculate_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def calculate_vwap(df):
    """Calculate VWAP (Volume Weighted Average Price)"""
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
    return vwap

def calculate_fibonacci_retracement(swing_high, swing_low):
    """Calculate Fibonacci retracement levels"""
    diff = swing_high - swing_low
    levels = {
        '0.0': swing_high,
        '0.236': swing_high - 0.236 * diff,
        '0.382': swing_high - 0.382 * diff,
        '0.5': swing_high - 0.5 * diff,
        '0.618': swing_high - 0.618 * diff,
        '0.786': swing_high - 0.786 * diff,
        '1.0': swing_low
    }
    return levels

def get_futures_data(symbol):
    """Load latest futures data"""
    data = {}
    
    # Open Interest
    oi_file = FUTURES_DATA_DIR / symbol / 'open_interest.csv'
    if oi_file.exists():
        oi_df = pd.read_csv(oi_file)
        if not oi_df.empty:
            latest = oi_df.iloc[-1]
            data['oi'] = float(latest['sumOpenInterest'])
            data['oi_value'] = float(latest['sumOpenInterestValue'])
    
    # Funding Rate
    funding_file = FUTURES_DATA_DIR / symbol / 'funding_rate.csv'
    if funding_file.exists():
        fund_df = pd.read_csv(funding_file)
        if not fund_df.empty:
            latest = fund_df.iloc[-1]
            data['funding_rate'] = float(latest['fundingRate'])
            data['mark_price'] = float(latest['markPrice'])
    
    # Long/Short Ratio
    ls_file = FUTURES_DATA_DIR / symbol / 'long_short_ratio.csv'
    if ls_file.exists():
        ls_df = pd.read_csv(ls_file)
        if not ls_df.empty:
            latest = ls_df.iloc[-1]
            data['long_account'] = float(latest['longAccount'])
            data['short_account'] = float(latest['shortAccount'])
            data['ls_ratio'] = float(latest['longShortRatio'])
    
    return data

def analyze_timeframe(symbol, interval):
    """Analyze a single timeframe and return indicator values"""
    df = load_ohlcv(symbol, interval)
    if df is None or len(df) < 50:
        return None
    
    config = TIMEFRAME_CONFIG.get(interval, {})
    if not config:
        return None
    
    latest = df.iloc[-1]
    result = {
        'timestamp': int(latest['open_time']),
        'datetime': latest['datetime'].isoformat(),
        'open': float(latest['open']),
        'high': float(latest['high']),
        'low': float(latest['low']),
        'close': float(latest['close']),
        'volume': float(latest['volume']),
        'category': config.get('category', 'Unknown')
    }
    
    # EMAs
    if 'ema_fast' in config:
        result['ema_fast'] = calculate_ema(df['close'], config['ema_fast']).iloc[-1]
    if 'ema_slow' in config:
        result['ema_slow'] = calculate_ema(df['close'], config['ema_slow']).iloc[-1]
    if 'ema_mid' in config:
        result['ema_mid'] = calculate_ema(df['close'], config['ema_mid']).iloc[-1]
    
    # RSI
    if 'rsi_period' in config:
        result['rsi'] = calculate_rsi(df['close'], config['rsi_period']).iloc[-1]
    
    # MACD (for timeframes that use it)
    if 'macd_fast' in config:
        macd_line, signal_line, histogram = calculate_macd(
            df['close'], 
            config['macd_fast'],
            config['macd_slow'],
            config['macd_signal']
        )
        result['macd'] = macd_line.iloc[-1]
        result['macd_signal'] = signal_line.iloc[-1]
        result['macd_histogram'] = histogram.iloc[-1]
    
    # ATR
    if 'atr_period' in config:
        result['atr'] = calculate_atr(df, config['atr_period']).iloc[-1]
    
    # VWAP
    result['vwap'] = calculate_vwap(df).iloc[-1]
    
    # Volume SMA
    if 'volume_sma' in config:
        result['volume_sma'] = df['volume'].rolling(window=config['volume_sma']).mean().iloc[-1]
        result['volume_ratio'] = result['volume'] / result['volume_sma'] if result['volume_sma'] > 0 else 0
    
    # Trend determination
    result['trend'] = determine_trend(result, config)
    
    return result

def determine_trend(indicators, config):
    """Determine trend based on indicator configuration"""
    close = indicators.get('close', 0)
    
    # EMA-based trend
    ema_fast = indicators.get('ema_fast')
    ema_slow = indicators.get('ema_slow')
    
    if ema_fast and ema_slow:
        if close > ema_fast > ema_slow:
            return 'Bullish'
        elif close < ema_slow < ema_fast:
            return 'Bearish'
        else:
            return 'Neutral'
    
    # VWAP-based fallback
    vwap = indicators.get('vwap')
    if vwap:
        if close > vwap * 1.005:
            return 'Bullish'
        elif close < vwap * 0.995:
            return 'Bearish'
    
    return 'Neutral'

def calculate_compass_score(timeframe_analysis):
    """Calculate overall COMPASS score and signal"""
    scores = {
        '1w': 0, '1d': 0, '4h': 0, '1h': 0, '15m': 0, '5m': 0
    }
    weights = {
        '1w': 0.30, '1d': 0.25, '4h': 0.20, '1h': 0.15, '15m': 0.07, '5m': 0.03
    }
    
    for tf, data in timeframe_analysis.items():
        if data is None:
            continue
        
        score = 0
        
        # Trend alignment (max 40 points)
        trend = data.get('trend', 'Neutral')
        if trend == 'Bullish':
            score += 40
        elif trend == 'Bearish':
            score -= 40
        
        # RSI position (max 20 points)
        rsi = data.get('rsi', 50)
        if 45 <= rsi <= 65:
            score += 20
        elif 30 <= rsi < 45 or 65 < rsi <= 70:
            score += 10
        
        # Volume confirmation (max 20 points)
        vol_ratio = data.get('volume_ratio', 0)
        if vol_ratio >= 1.5:
            score += 20
        elif vol_ratio >= 1.2:
            score += 10
        
        # VWAP position (max 20 points)
        close = data.get('close', 0)
        vwap = data.get('vwap', close)
        if close > vwap * 1.01:
            score += 20
        elif close < vwap * 0.99:
            score -= 20
        
        scores[tf] = max(-100, min(100, score))
    
    # Weighted total
    total_score = sum(scores[tf] * weights[tf] for tf in scores)
    
    # Determine signal
    if total_score >= 60:
        signal = 'Long'
        confidence = 'High' if total_score >= 75 else 'Medium'
    elif total_score <= -60:
        signal = 'Short'
        confidence = 'High' if total_score <= -75 else 'Medium'
    else:
        signal = 'Flat'
        confidence = 'Low'
    
    return {
        'total_score': round(total_score, 2),
        'timeframe_scores': scores,
        'signal': signal,
        'confidence': confidence,
        'alignment': calculate_alignment(scores)
    }

def calculate_alignment(scores):
    """Calculate how aligned timeframes are"""
    bullish_count = sum(1 for s in scores.values() if s > 20)
    bearish_count = sum(1 for s in scores.values() if s < -20)
    neutral_count = sum(1 for s in scores.values() if -20 <= s <= 20)
    
    total = len([s for s in scores.values() if s != 0])
    if total == 0:
        return 'No Data'
    
    if bullish_count / total >= 0.7:
        return 'Strongly Bullish'
    elif bearish_count / total >= 0.7:
        return 'Strongly Bearish'
    elif bullish_count / total >= 0.5:
        return 'Moderately Bullish'
    elif bearish_count / total >= 0.5:
        return 'Moderately Bearish'
    else:
        return 'Mixed/Neutral'

def generate_trade_setup(symbol, timeframe_analysis, compass_score, futures_data):
    """Generate trade setup if signal is not Flat"""
    signal = compass_score['signal']
    if signal == 'Flat':
        return None
    
    # Get latest 1H data for entry zone calculation
    h1_data = timeframe_analysis.get('1h', {})
    if not h1_data:
        return None
    
    close = h1_data.get('close', 0)
    atr = h1_data.get('atr', close * 0.01)
    
    # Calculate entry zone (current price ± 0.5 ATR)
    entry_zone_low = close - (atr * 0.5)
    entry_zone_high = close + (atr * 0.5)
    
    # Stop loss (1.5x ATR for swing, 1x for scalp)
    if signal == 'Long':
        stop_loss = close - (atr * 1.5)
    else:
        stop_loss = close + (atr * 1.5)
    
    # Targets (2:1 and 3:1 R:R)
    risk = abs(close - stop_loss)
    target_1 = close + (risk * 2) if signal == 'Long' else close - (risk * 2)
    target_2 = close + (risk * 3) if signal == 'Long' else close - (risk * 3)
    
    return {
        'bias': signal,
        'entry_zone': [round(entry_zone_low, 2), round(entry_zone_high, 2)],
        'stop_loss': round(stop_loss, 2),
        'target_1': round(target_1, 2),
        'target_2': round(target_2, 2),
        'rr_ratio_1': '1:2',
        'rr_ratio_2': '1:3',
        'risk_amount': round(risk, 2),
        'position_size_example': f"Risk $100 = {int(100/risk)} units"
    }

def analyze_symbol(symbol):
    """Complete COMPASS analysis for a symbol"""
    print(f"\n{'='*70}")
    print(f"COMPASS Analysis: {symbol}")
    print('='*70)
    
    intervals = ['1w', '1d', '4h', '1h', '15m', '5m']
    timeframe_analysis = {}
    
    for interval in intervals:
        print(f"  Analyzing {interval}...", end=' ')
        result = analyze_timeframe(symbol, interval)
        if result:
            timeframe_analysis[interval] = result
            trend = result.get('trend', 'Unknown')
            print(f"✓ ({trend})")
        else:
            print("✗ no data")
    
    # Calculate COMPASS score
    print(f"\n  Calculating COMPASS score...")
    compass_score = calculate_compass_score(timeframe_analysis)
    
    # Get futures data
    print(f"  Loading futures data...")
    futures_data = get_futures_data(symbol)
    
    # Generate trade setup if applicable
    trade_setup = generate_trade_setup(symbol, timeframe_analysis, compass_score, futures_data)
    
    # Build complete result
    analysis = {
        'symbol': symbol,
        'timestamp': datetime.now().isoformat(),
        'timeframes': timeframe_analysis,
        'compass_score': compass_score,
        'futures_data': futures_data,
        'trade_setup': trade_setup,
        'summary': {
            'signal': compass_score['signal'],
            'confidence': compass_score['confidence'],
            'alignment': compass_score['alignment'],
            'score': compass_score['total_score']
        }
    }
    
    # Save to file
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{symbol}_compass_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    print(f"\n  Signal: {compass_score['signal']} ({compass_score['confidence']} confidence)")
    print(f"  Score: {compass_score['total_score']}/100")
    print(f"  Alignment: {compass_score['alignment']}")
    if trade_setup:
        print(f"  Entry Zone: {trade_setup['entry_zone']}")
        print(f"  Stop: {trade_setup['stop_loss']}")
        print(f"  Targets: {trade_setup['target_1']} / {trade_setup['target_2']}")
    print(f"  Output: {output_file}")
    
    return analysis

def main():
    """Main analysis function"""
    print("="*70)
    print("COMPASS Multi-Timeframe Analysis Engine")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    results = {}
    
    for symbol in symbols:
        results[symbol] = analyze_symbol(symbol)
    
    # Save combined summary
    summary_file = OUTPUT_DIR / f"compass_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n{'='*70}")
    print("Analysis complete")
    print(f"Summary: {summary_file}")
    print('='*70)
    
    return results

if __name__ == '__main__':
    main()
