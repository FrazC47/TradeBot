#!/usr/bin/env python3
"""
Chart Generator - Visualize indicators for verification
Improved version: Shows actual indicator lines, fewer candles, better visibility
"""

import json
import csv
from pathlib import Path
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
CHARTS_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/charts')

def load_ohlcv(symbol, interval, max_candles=40):
    """Load OHLCV data - limited to recent candles"""
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
    
    return data[-max_candles:] if len(data) > max_candles else data

def calculate_ema(prices, period):
    """Calculate EMA series"""
    if len(prices) < period:
        return [None] * len(prices)
    multiplier = 2 / (period + 1)
    ema = [sum(prices[:period]) / period]
    for p in prices[period:]:
        ema.append((p * multiplier) + (ema[-1] * (1 - multiplier)))
    return [None] * (period - 1) + ema

def calculate_vwap(data):
    """Calculate VWAP series"""
    vwap = []
    cum_typical_vol = 0.0
    cum_vol = 0.0
    for candle in data:
        typical = (candle['high'] + candle['low'] + candle['close']) / 3.0
        vol = candle['volume']
        cum_typical_vol += typical * vol
        cum_vol += vol
        vwap.append(cum_typical_vol / cum_vol if cum_vol > 0 else typical)
    return vwap

def calculate_rsi(prices, period=14):
    """Calculate RSI series"""
    n = len(prices)
    if n < period + 1:
        return [50.0] * n
    
    gains = [0.0] * n
    losses = [0.0] * n
    for i in range(1, n):
        d = prices[i] - prices[i-1]
        gains[i] = max(d, 0.0)
        losses[i] = max(-d, 0.0)
    
    avg_gain = sum(gains[1:period+1]) / period
    avg_loss = sum(losses[1:period+1]) / period
    
    rsi = [50.0] * n
    if avg_loss > 0:
        rs = avg_gain / avg_loss
        rsi[period] = 100.0 - (100.0 / (1.0 + rs))
    
    for i in range(period + 1, n):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss > 0:
            rs = avg_gain / avg_loss
            rsi[i] = 100.0 - (100.0 / (1.0 + rs))
    
    return rsi

def generate_chart(symbol, interval, max_candles=40):
    """Generate chart with actual indicator lines"""
    
    ohlcv = load_ohlcv(symbol, interval, max_candles)
    if not ohlcv:
        print(f"No data for {symbol}/{interval}")
        return None
    
    dates = [datetime.fromtimestamp(c['timestamp'] / 1000) for c in ohlcv]
    closes = [c['close'] for c in ohlcv]
    highs = [c['high'] for c in ohlcv]
    lows = [c['low'] for c in ohlcv]
    volumes = [c['volume'] for c in ohlcv]
    
    # Calculate indicators
    ema_9 = calculate_ema(closes, 9)
    ema_21 = calculate_ema(closes, 21)
    ema_50 = calculate_ema(closes, 50) if len(closes) >= 50 else None
    vwap = calculate_vwap(ohlcv)
    rsi = calculate_rsi(closes, 14)
    
    # Create figure
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), 
                             gridspec_kw={'height_ratios': [3, 1, 1], 'hspace': 0.05})
    
    # Price chart
    ax1 = axes[0]
    ax1.set_title(f'{symbol} - {interval} (Last {len(ohlcv)} Candles)', 
                  fontsize=14, fontweight='bold')
    
    # Price line with high/low range
    ax1.plot(dates, closes, color='black', linewidth=2, label='Close')
    ax1.fill_between(dates, lows, highs, alpha=0.15, color='gray')
    
    # EMAs as actual lines
    if any(ema_9):
        ax1.plot(dates, ema_9, color='blue', linewidth=1.5, label='EMA 9', alpha=0.9)
    if any(ema_21):
        ax1.plot(dates, ema_21, color='orange', linewidth=1.5, label='EMA 21', alpha=0.9)
    if ema_50 and any(ema_50):
        ax1.plot(dates, ema_50, color='green', linewidth=1.5, label='EMA 50', alpha=0.9)
    
    # VWAP
    ax1.plot(dates, vwap, color='magenta', linewidth=1.5, linestyle='--', 
            label='VWAP', alpha=0.9)
    
    # Current price
    ax1.axhline(y=closes[-1], color='red', linestyle=':', alpha=0.5)
    ax1.text(dates[-1], closes[-1], f'  ${closes[-1]:,.0f}', 
            fontsize=10, color='red', fontweight='bold', va='center')
    
    ax1.set_ylabel('Price', fontsize=11)
    ax1.legend(loc='upper left', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(dates[0], dates[-1])
    
    # Volume
    ax2 = axes[1]
    colors = ['green' if closes[i] >= closes[i-1] else 'red' for i in range(1, len(closes))]
    colors = ['gray'] + colors
    ax2.bar(dates, volumes, color=colors, alpha=0.6, width=0.6)
    ax2.set_ylabel('Volume', fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(dates[0], dates[-1])
    
    # RSI
    ax3 = axes[2]
    ax3.plot(dates, rsi, color='purple', linewidth=2, label='RSI 14')
    ax3.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='Overbought')
    ax3.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='Oversold')
    ax3.axhline(y=50, color='gray', linestyle='-', alpha=0.3)
    ax3.fill_between(dates, 30, 70, alpha=0.1, color='gray')
    ax3.set_ylim(0, 100)
    ax3.set_ylabel('RSI', fontsize=11)
    ax3.set_xlabel('Date', fontsize=11)
    ax3.legend(loc='upper left', fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(dates[0], dates[-1])
    
    # Format x-axis
    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')
    
    plt.tight_layout()
    
    # Save
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    chart_path = CHARTS_DIR / f'{symbol}_{interval}_chart.png'
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Chart saved: {chart_path}")
    print(f"   Candles shown: {len(ohlcv)}")
    print(f"   Current price: ${closes[-1]:,.2f}")
    print(f"   RSI: {rsi[-1]:.1f}")
    
    return chart_path

def main():
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'BTCUSDT'
    interval = sys.argv[2] if len(sys.argv) > 2 else '1d'
    
    print(f"Generating improved chart for {symbol}/{interval}...")
    chart_path = generate_chart(symbol, interval)
    
    if chart_path:
        print(f"\n✅ Chart ready: {chart_path}")
    else:
        print("❌ Failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
