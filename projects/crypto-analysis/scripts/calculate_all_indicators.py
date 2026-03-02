#!/usr/bin/env python3
"""
Comprehensive Indicator Calculator - All Timeframes
Based on the PDF specification for each timeframe
"""

import csv
import json
from pathlib import Path
from datetime import datetime
import math

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
INDICATORS_DIR = Path('/root/.openclaw/workspace/data/indicators')
FUTURES_DATA_DIR = Path('/root/.openclaw/workspace/data/futures')
LIQUIDITY_DIR = Path('/root/.openclaw/workspace/data/liquidity')
LIQUIDATION_DIR = Path('/root/.openclaw/workspace/data/liquidations')

def load_data(symbol, interval):
    """Load OHLCV data"""
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    if not filepath.exists():
        return []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return [{
            'timestamp': int(r['open_time']),
            'open': float(r['open']),
            'high': float(r['high']),
            'low': float(r['low']),
            'close': float(r['close']),
            'volume': float(r['volume'])
        } for r in reader]

def load_futures_data(symbol):
    """Load latest futures data (OI and Funding Rate)"""
    latest_file = FUTURES_DATA_DIR / 'latest_futures_data.json'
    if not latest_file.exists():
        return None
    try:
        with open(latest_file, 'r') as f:
            data = json.load(f)
            return data.get(symbol)
    except Exception:
        return None

def load_liquidity_data(symbol):
    """Load liquidity heatmap data"""
    liquidity_file = LIQUIDITY_DIR / 'liquidity_heatmap.json'
    if not liquidity_file.exists():
        return None
    try:
        with open(liquidity_file, 'r') as f:
            data = json.load(f)
            return data.get(symbol)
    except Exception:
        return None

def load_liquidation_data(symbol):
    """Load liquidation heatmap data"""
    liquidation_file = LIQUIDATION_DIR / 'liquidation_heatmap.json'
    if not liquidation_file.exists():
        return None
    try:
        with open(liquidation_file, 'r') as f:
            data = json.load(f)
            return data.get(symbol)
    except Exception:
        return None

def calculate_ema(prices, period):
    """Calculate EMA"""
    if len(prices) < period:
        return [None] * len(prices)
    multiplier = 2 / (period + 1)
    ema = [sum(prices[:period]) / period]
    for p in prices[period:]:
        ema.append((p * multiplier) + (ema[-1] * (1 - multiplier)))
    return [None] * (period - 1) + ema

def calculate_sma(values, period):
    """Calculate SMA"""
    if len(values) < period:
        return [None] * len(values)
    sma = []
    for i in range(len(values)):
        if i < period - 1:
            sma.append(None)
        else:
            sma.append(sum(values[i-period+1:i+1]) / period)
    return sma

def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    if len(prices) < period + 1:
        return [50] * len(prices)
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    rsi = [50] * period
    
    for i in range(period, len(deltas)):
        gains = [d for d in deltas[i-period:i] if d > 0]
        losses = [-d for d in deltas[i-period:i] if d < 0]
        avg_gain = sum(gains) / period if gains else 0.001
        avg_loss = sum(losses) / period if losses else 0.001
        rs = avg_gain / avg_loss
        rsi.append(100 - (100 / (1 + rs)))
    
    return rsi

def calculate_atr(data, period=14):
    """Calculate ATR"""
    atr = [0] * period
    for i in range(period, len(data)):
        high = data[i]['high']
        low = data[i]['low']
        prev_close = data[i-1]['close']
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        atr.append(tr)
    
    # Smooth with SMA
    atr_smooth = []
    for i in range(len(atr)):
        if i < period:
            atr_smooth.append(atr[i])
        else:
            atr_smooth.append((atr_smooth[-1] * (period-1) + atr[i]) / period)
    return atr_smooth

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    
    macd_line = []
    for i in range(len(prices)):
        if ema_fast[i] is None or ema_slow[i] is None:
            macd_line.append(None)
        else:
            macd_line.append(ema_fast[i] - ema_slow[i])
    
    # Signal line (EMA of MACD)
    valid_macd = [m for m in macd_line if m is not None]
    if len(valid_macd) < signal:
        signal_line = [None] * len(macd_line)
    else:
        signal_ema = calculate_ema(valid_macd, signal)
        signal_line = [None] * (len(macd_line) - len(signal_ema)) + signal_ema
    
    # Histogram
    histogram = []
    for i in range(len(macd_line)):
        if macd_line[i] is not None and signal_line[i] is not None:
            histogram.append(macd_line[i] - signal_line[i])
        else:
            histogram.append(None)
    
    return macd_line, signal_line, histogram

def calculate_vwap(data, anchor_type='session'):
    """Calculate VWAP"""
    vwap = []
    cum_typical_vol = 0
    cum_vol = 0
    
    for candle in data:
        typical = (candle['high'] + candle['low'] + candle['close']) / 3
        vol = candle['volume']
        cum_typical_vol += typical * vol
        cum_vol += vol
        vwap.append(cum_typical_vol / cum_vol if cum_vol > 0 else typical)
    
    return vwap

def calculate_fibonacci(high, low):
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

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    sma = calculate_sma(prices, period)
    upper = []
    lower = []
    
    for i in range(len(prices)):
        if sma[i] is None:
            upper.append(None)
            lower.append(None)
        else:
            # Calculate standard deviation
            slice_prices = prices[max(0, i-period+1):i+1]
            mean = sum(slice_prices) / len(slice_prices)
            variance = sum((p - mean) ** 2 for p in slice_prices) / len(slice_prices)
            std = math.sqrt(variance)
            upper.append(sma[i] + (std_dev * std))
            lower.append(sma[i] - (std_dev * std))
    
    return upper, sma, lower

def calculate_obv(data):
    """Calculate On-Balance Volume (OBV)"""
    obv = [0]
    for i in range(1, len(data)):
        if data[i]['close'] > data[i-1]['close']:
            obv.append(obv[-1] + data[i]['volume'])
        elif data[i]['close'] < data[i-1]['close']:
            obv.append(obv[-1] - data[i]['volume'])
        else:
            obv.append(obv[-1])
    return obv

def calculate_cvd(data):
    """Calculate Cumulative Volume Delta (CVD) - simplified using close vs open"""
    cvd = [0]
    for i in range(1, len(data)):
        # Estimate delta: positive if close > open, negative if close < open
        if data[i]['close'] > data[i]['open']:
            delta = data[i]['volume'] * ((data[i]['close'] - data[i]['open']) / (data[i]['high'] - data[i]['low'] + 0.0001))
        elif data[i]['close'] < data[i]['open']:
            delta = -data[i]['volume'] * ((data[i]['open'] - data[i]['close']) / (data[i]['high'] - data[i]['low'] + 0.0001))
        else:
            delta = 0
        cvd.append(cvd[-1] + delta)
    return cvd

def calculate_support_resistance(data, lookback=20, zone_threshold=0.005):
    """
    Calculate Support and Resistance zones from swing highs/lows
    Returns dict with support_zones and resistance_zones
    """
    highs = [c['high'] for c in data]
    lows = [c['low'] for c in data]
    
    # Find local maxima (swing highs) and minima (swing lows)
    swing_highs = []
    swing_lows = []
    
    for i in range(2, len(data) - 2):
        # Swing high: higher than 2 candles before and after
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            swing_highs.append((i, highs[i]))
        # Swing low: lower than 2 candles before and after
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            swing_lows.append((i, lows[i]))
    
    # Cluster swing points into zones
    def cluster_levels(levels, threshold):
        """Cluster price levels that are within threshold % of each other"""
        if not levels:
            return []
        sorted_levels = sorted(levels, key=lambda x: x[1])
        clusters = [[sorted_levels[0]]]
        
        for level in sorted_levels[1:]:
            avg_cluster = sum([l[1] for l in clusters[-1]]) / len(clusters[-1])
            if abs(level[1] - avg_cluster) / avg_cluster < threshold:
                clusters[-1].append(level)
            else:
                clusters.append([level])
        
        # Return zone centers with strength (number of touches)
        zones = []
        for cluster in clusters:
            avg_price = sum([l[1] for l in cluster]) / len(cluster)
            zones.append({
                'price': round(avg_price, 2),
                'touches': len(cluster),
                'range': (min([l[1] for l in cluster]), max([l[1] for l in cluster]))
            })
        return zones
    
    # Get recent swing points only (last 'lookback' candles)
    recent_highs = [sh for sh in swing_highs if sh[0] >= len(data) - lookback]
    recent_lows = [sl for sl in swing_lows if sl[0] >= len(data) - lookback]
    
    resistance_zones = cluster_levels(recent_highs, zone_threshold)
    support_zones = cluster_levels(recent_lows, zone_threshold)
    
    return {
        'support_zones': sorted(support_zones, key=lambda x: x['price'], reverse=True)[:3],  # Top 3
        'resistance_zones': sorted(resistance_zones, key=lambda x: x['price'])[:3],  # Bottom 3
        'swing_highs_count': len(swing_highs),
        'swing_lows_count': len(swing_lows)
    }

def calculate_volume_delta(data):
    """Calculate Volume Delta (buy vs sell volume estimate) per candle"""
    delta = []
    for candle in data:
        range_size = candle['high'] - candle['low']
        if range_size == 0:
            delta.append(0)
        else:
            # Estimate: closer to high = more buying, closer to low = more selling
            position = (candle['close'] - candle['low']) / range_size
            delta.append(candle['volume'] * (2 * position - 1))  # -vol to +vol
    return delta

def calculate_indicators_for_timeframe(symbol, interval):
    """Calculate all indicators for a specific timeframe based on PDF spec"""
    data = load_data(symbol, interval)
    if not data:
        return None
    
    prices = [c['close'] for c in data]
    highs = [c['high'] for c in data]
    lows = [c['low'] for c in data]
    volumes = [c['volume'] for c in data]
    
    indicators = {
        'symbol': symbol,
        'interval': interval,
        'timestamp': data[-1]['timestamp'],
        'close': data[-1]['close'],
        'indicators': {}
    }
    
    # Timeframe-specific indicators based on PDF
    if interval == '1M':
        # Monthly: EMA 50/200, MACD, Volume 20 SMA, Fibonacci (similar to Weekly but higher timeframe)
        indicators['indicators']['ema_50'] = calculate_ema(prices, 50)[-1]
        indicators['indicators']['ema_200'] = calculate_ema(prices, 200)[-1]
        macd_line, signal_line, hist = calculate_macd(prices, 12, 26, 9)
        indicators['indicators']['macd_line'] = macd_line[-1]
        indicators['indicators']['macd_signal'] = signal_line[-1]
        indicators['indicators']['macd_hist'] = hist[-1]
        indicators['indicators']['volume_sma_20'] = calculate_sma(volumes, 20)[-1]
        
        # Fibonacci from last major swing (12 periods = 1 year)
        swing_high = max(highs[-12:])
        swing_low = min(lows[-12:])
        indicators['indicators']['fib_levels'] = calculate_fibonacci(swing_high, swing_low)
        # Support/Resistance zones for monthly
        sr_zones = calculate_support_resistance(data, lookback=24, zone_threshold=0.02)
        indicators['indicators']['support_resistance'] = sr_zones
        
    elif interval == '1w':
        # Weekly: EMA 50/200, MACD, Volume 20 SMA, Fibonacci
        indicators['indicators']['ema_50'] = calculate_ema(prices, 50)[-1]
        indicators['indicators']['ema_200'] = calculate_ema(prices, 200)[-1]
        macd_line, signal_line, hist = calculate_macd(prices, 12, 26, 9)
        indicators['indicators']['macd_line'] = macd_line[-1]
        indicators['indicators']['macd_signal'] = signal_line[-1]
        indicators['indicators']['macd_hist'] = hist[-1]
        indicators['indicators']['volume_sma_20'] = calculate_sma(volumes, 20)[-1]
        
        # Fibonacci from last major swing (20 periods)
        swing_high = max(highs[-20:])
        swing_low = min(lows[-20:])
        indicators['indicators']['fib_levels'] = calculate_fibonacci(swing_high, swing_low)
        # NEW: Support/Resistance zones
        sr_zones = calculate_support_resistance(data, lookback=50, zone_threshold=0.01)
        indicators['indicators']['support_resistance'] = sr_zones
        
    elif interval == '1d':
        # Daily: EMA 20/50, VWAP, RSI 14, MACD, ATR 14, Volume 20 SMA, Fibonacci
        indicators['indicators']['ema_20'] = calculate_ema(prices, 20)[-1]
        indicators['indicators']['ema_50'] = calculate_ema(prices, 50)[-1]
        indicators['indicators']['vwap'] = calculate_vwap(data)[-1]
        indicators['indicators']['rsi_14'] = calculate_rsi(prices, 14)[-1]
        macd_line, signal_line, hist = calculate_macd(prices, 12, 26, 9)
        indicators['indicators']['macd_line'] = macd_line[-1]
        indicators['indicators']['macd_signal'] = signal_line[-1]
        indicators['indicators']['macd_hist'] = hist[-1]
        indicators['indicators']['atr_14'] = calculate_atr(data, 14)[-1]
        indicators['indicators']['volume_sma_20'] = calculate_sma(volumes, 20)[-1]
        
        swing_high = max(highs[-20:])
        swing_low = min(lows[-20:])
        indicators['indicators']['fib_levels'] = calculate_fibonacci(swing_high, swing_low)
        # NEW: Support/Resistance zones
        sr_zones = calculate_support_resistance(data, lookback=30, zone_threshold=0.008)
        indicators['indicators']['support_resistance'] = sr_zones
        
    elif interval == '4h':
        # 4H: EMA 9/21, RSI 14, MACD, VWAP, Volume 20 SMA, ATR 14, OI, Funding
        indicators['indicators']['ema_9'] = calculate_ema(prices, 9)[-1]
        indicators['indicators']['ema_21'] = calculate_ema(prices, 21)[-1]
        indicators['indicators']['rsi_14'] = calculate_rsi(prices, 14)[-1]
        macd_line, signal_line, hist = calculate_macd(prices, 12, 26, 9)
        indicators['indicators']['macd_line'] = macd_line[-1]
        indicators['indicators']['macd_signal'] = signal_line[-1]
        indicators['indicators']['macd_hist'] = hist[-1]
        indicators['indicators']['vwap'] = calculate_vwap(data)[-1]
        indicators['indicators']['volume_sma_20'] = calculate_sma(volumes, 20)[-1]
        indicators['indicators']['atr_14'] = calculate_atr(data, 14)[-1]
        # CVD/OBV for 4H (trend confirmation)
        indicators['indicators']['obv'] = calculate_obv(data)[-1]
        indicators['indicators']['cvd'] = calculate_cvd(data)[-1]
        # NEW: Open Interest and Funding Rate from Futures API
        futures_data = load_futures_data(symbol)
        if futures_data:
            indicators['indicators']['open_interest'] = futures_data['open_interest']
            indicators['indicators']['funding_rate'] = futures_data['funding_rate']
        
    elif interval == '1h':
        # 1H: EMA 9/25, RSI 14, VWAP, Volume 20 SMA, ATR 14
        indicators['indicators']['ema_9'] = calculate_ema(prices, 9)[-1]
        indicators['indicators']['ema_25'] = calculate_ema(prices, 25)[-1]
        indicators['indicators']['rsi_14'] = calculate_rsi(prices, 14)[-1]
        indicators['indicators']['vwap'] = calculate_vwap(data)[-1]
        indicators['indicators']['volume_sma_20'] = calculate_sma(volumes, 20)[-1]
        indicators['indicators']['atr_14'] = calculate_atr(data, 14)[-1]
        # NEW: CVD/OBV for 1H
        indicators['indicators']['obv'] = calculate_obv(data)[-1]
        indicators['indicators']['cvd'] = calculate_cvd(data)[-1]
        
    elif interval == '15m':
        # 15M: EMA 9/21/50, RSI 7 or 9, VWAP, CVD/OBV, ATR 7, Liquidity Heatmap
        indicators['indicators']['ema_9'] = calculate_ema(prices, 9)[-1]
        indicators['indicators']['ema_21'] = calculate_ema(prices, 21)[-1]
        indicators['indicators']['ema_50'] = calculate_ema(prices, 50)[-1]
        indicators['indicators']['rsi_9'] = calculate_rsi(prices, 9)[-1]
        indicators['indicators']['vwap'] = calculate_vwap(data)[-1]
        indicators['indicators']['atr_7'] = calculate_atr(data, 7)[-1]
        # CVD and OBV
        indicators['indicators']['obv'] = calculate_obv(data)[-1]
        indicators['indicators']['cvd'] = calculate_cvd(data)[-1]
        # NEW: Liquidity Heatmap data
        liquidity = load_liquidity_data(symbol)
        if liquidity:
            indicators['indicators']['liquidity'] = {
                'support_walls': liquidity.get('support_walls', [])[:3],
                'resistance_walls': liquidity.get('resistance_walls', [])[:3],
                'imbalance_1pct': liquidity.get('liquidity_profile', {}).get('1%', {}).get('imbalance', 0)
            }
        
    elif interval == '5m':
        # 5M: EMA 9, RSI 5 or 7, VWAP, Volume, ATR 5, Liquidation Heatmap
        indicators['indicators']['ema_9'] = calculate_ema(prices, 9)[-1]
        indicators['indicators']['rsi_7'] = calculate_rsi(prices, 7)[-1]
        indicators['indicators']['vwap'] = calculate_vwap(data)[-1]
        indicators['indicators']['atr_5'] = calculate_atr(data, 5)[-1]
        # Volume Delta
        vol_delta = calculate_volume_delta(data)
        indicators['indicators']['volume_delta'] = vol_delta[-1]
        # NEW: Liquidation Heatmap data
        liquidation = load_liquidation_data(symbol)
        if liquidation:
            indicators['indicators']['liquidation'] = {
                'nearest_long_liq': liquidation.get('nearest_long_liquidation'),
                'nearest_short_liq': liquidation.get('nearest_short_liquidation'),
                'long_short_ratio': liquidation.get('long_short_ratio'),
                'funding_bias': liquidation.get('funding_impact', {}).get('bias')
            }
    
    return indicators

def main():
    print("=" * 90)
    print("COMPREHENSIVE INDICATOR CALCULATOR")
    print("=" * 90)
    print()
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']
    timeframes = ['1M', '1w', '1d', '4h', '1h', '15m', '5m']
    
    INDICATORS_DIR.mkdir(parents=True, exist_ok=True)
    
    for symbol in symbols:
        print(f"\n{symbol}:")
        print("-" * 90)
        
        all_indicators = {}
        
        for interval in timeframes:
            result = calculate_indicators_for_timeframe(symbol, interval)
            if result:
                all_indicators[interval] = result
                print(f"  {interval:3s}: ✅ Calculated {len(result['indicators'])} indicators")
            else:
                print(f"  {interval:3s}: ❌ No data")
        
        # Save to file
        output_file = INDICATORS_DIR / f"{symbol}_indicators.json"
        with open(output_file, 'w') as f:
            json.dump(all_indicators, f, indent=2, default=str)
        print(f"  Saved to: {output_file}")
    
    print()
    print("=" * 90)
    print("INDICATOR CALCULATION COMPLETE")
    print("=" * 90)

if __name__ == "__main__":
    main()
