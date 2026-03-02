#!/usr/bin/env python3
"""
Generate static PNG candlestick charts with MACD overlay on price chart
"""

import csv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path
import numpy as np

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
OUTPUT_DIR = Path('/root/.openclaw/workspace/charts_png')

def load_ohlcv_data(symbol: str, interval: str, limit: int = 100):
    """Load OHLCV data from CSV"""
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    
    if not filepath.exists():
        return []
    
    data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                data.append({
                    'datetime': datetime.fromtimestamp(int(row['open_time']) / 1000),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume'])
                })
            except (ValueError, KeyError):
                continue
    
    return data[-limit:] if len(data) > limit else data

def calculate_ema(prices, period):
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return [np.nan] * len(prices)
    
    multiplier = 2 / (period + 1)
    ema = [np.nan] * (period - 1)
    ema.append(sum(prices[:period]) / period)
    
    for i in range(period, len(prices)):
        ema.append((prices[i] - ema[-1]) * multiplier + ema[-1])
    
    return ema

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD indicator"""
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    
    macd_line = [f - s if not (np.isnan(f) or np.isnan(s)) else np.nan 
                 for f, s in zip(ema_fast, ema_slow)]
    
    signal_line = calculate_ema([x for x in macd_line if not np.isnan(x)], signal)
    signal_padded = [np.nan] * (len(macd_line) - len(signal_line)) + signal_line
    
    histogram = [m - s if not (np.isnan(m) or np.isnan(s)) else np.nan 
                 for m, s in zip(macd_line, signal_padded)]
    
    return macd_line, signal_padded, histogram

def generate_candlestick_chart(symbol: str, interval: str, data: list):
    """Generate a candlestick chart with MACD overlay on price chart"""
    if not data:
        return None
    
    # Create figure with two subplots (price+MACD and volume)
    fig = plt.figure(figsize=(12, 10), facecolor='#131722')
    gs = fig.add_gridspec(2, 1, height_ratios=[4, 1], hspace=0.05)
    
    ax1 = fig.add_subplot(gs[0])  # Price + MACD overlay
    ax2 = fig.add_subplot(gs[1])  # Volume
    
    # Colors
    up_color = '#26a69a'
    down_color = '#ef5350'
    wick_color = '#787b86'
    macd_color = '#2196f3'
    signal_color = '#ff9800'
    
    # Calculate MACD
    closes = [d['close'] for d in data]
    macd_line, signal_line, histogram = calculate_macd(closes)
    
    # Normalize MACD to fit on price chart (scale to price range)
    price_min = min(d['low'] for d in data)
    price_max = max(d['high'] for d in data)
    price_range = price_max - price_min
    
    # Find MACD range for scaling
    valid_macd = [x for x in macd_line if not np.isnan(x)]
    valid_signal = [x for x in signal_line if not np.isnan(x)]
    valid_hist = [x for x in histogram if not np.isnan(x)]
    
    if valid_macd and valid_signal:
        macd_min = min(min(valid_macd), min(valid_signal))
        macd_max = max(max(valid_macd), max(valid_signal))
        macd_range = macd_max - macd_min if macd_max != macd_min else 1
        
        # Scale MACD to bottom 20% of price chart
        macd_scale = price_range * 0.15 / macd_range
        macd_offset = price_min - price_range * 0.05
        
        # Plot scaled MACD lines
        x_vals = range(len(data))
        scaled_macd = [m * macd_scale + macd_offset if not np.isnan(m) else np.nan for m in macd_line]
        scaled_signal = [s * macd_scale + macd_offset if not np.isnan(s) else np.nan for s in signal_line]
        
        ax1.plot(x_vals, scaled_macd, color=macd_color, linewidth=1.5, label='MACD', alpha=0.9)
        ax1.plot(x_vals, scaled_signal, color=signal_color, linewidth=1.5, label='Signal', alpha=0.9)
        
        # Plot MACD histogram as bars at bottom
        for i, h in enumerate(histogram):
            if not np.isnan(h):
                scaled_h = h * macd_scale
                color = up_color if h >= 0 else down_color
                ax1.bar(i, scaled_h, bottom=macd_offset, color=color, alpha=0.4, width=0.6)
    
    # Plot candlesticks on top
    for i, d in enumerate(data):
        x = i
        is_up = d['close'] >= d['open']
        color = up_color if is_up else down_color
        
        # Draw wick
        ax1.plot([x, x], [d['low'], d['high']], color=wick_color, linewidth=0.5, zorder=3)
        
        # Draw body
        height = abs(d['close'] - d['open'])
        bottom = min(d['open'], d['close'])
        rect = plt.Rectangle((x - 0.4, bottom), 0.8, height, 
                             facecolor=color, edgecolor=color, linewidth=1, zorder=4)
        ax1.add_patch(rect)
    
    # Format price chart
    ax1.set_facecolor('#131722')
    ax1.tick_params(colors='#d1d4dc')
    ax1.grid(True, alpha=0.2, color='#2a2e39')
    ax1.set_ylabel('Price', color='#d1d4dc', fontsize=12)
    ax1.set_title(f'{symbol} {interval} Chart with MACD Overlay', color='#d1d4dc', fontsize=14, fontweight='bold')
    ax1.set_xticks([])
    ax1.legend(loc='upper left', facecolor='#131722', edgecolor='#2a2e39', 
               labelcolor='#d1d4dc', fontsize=9)
    
    # Plot volume in bottom panel
    volumes = [d['volume'] for d in data]
    colors = [up_color if data[i]['close'] >= data[i]['open'] else down_color 
              for i in range(len(data))]
    
    ax2.bar(range(len(data)), volumes, color=colors, alpha=0.7, width=0.8)
    ax2.set_facecolor('#131722')
    ax2.tick_params(colors='#d1d4dc')
    ax2.grid(True, alpha=0.2, color='#2a2e39')
    ax2.set_ylabel('Volume', color='#d1d4dc', fontsize=10)
    ax2.set_xlabel('Time →', color='#d1d4dc', fontsize=10)
    
    # Add current price annotation
    latest = data[-1]
    prev = data[-2] if len(data) > 1 else latest
    change = latest['close'] - prev['close']
    change_pct = (change / prev['close']) * 100 if prev['close'] else 0
    
    price_text = f"${latest['close']:,.2f}"
    change_text = f"{'+' if change >= 0 else ''}{change:,.2f} ({'+' if change_pct >= 0 else ''}{change_pct:.2f}%)"
    change_color = up_color if change >= 0 else down_color
    
    fig.text(0.02, 0.98, price_text, fontsize=20, fontweight='bold', 
             color='#d1d4dc', va='top')
    fig.text(0.02, 0.95, change_text, fontsize=12, color=change_color, va='top')
    
    # Add stats
    stats_text = f"O: ${latest['open']:,.2f}  H: ${latest['high']:,.2f}  L: ${latest['low']:,.2f}  C: ${latest['close']:,.2f}"
    fig.text(0.98, 0.98, stats_text, fontsize=10, color='#787b86', va='top', ha='right')
    
    plt.tight_layout()
    
    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{symbol}_{interval}.png"
    plt.savefig(output_file, dpi=150, facecolor='#131722', edgecolor='none', 
                bbox_inches='tight', pad_inches=0.3)
    plt.close()
    
    return output_file

def main():
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    intervals = ['1M', '1w', '1d', '4h', '1h', '15m']
    
    print("Generating PNG charts with MACD overlay...")
    
    for symbol in symbols:
        print(f"\n{'='*60}")
        print(f"Generating charts for {symbol}")
        print('='*60)
        for interval in intervals:
            print(f"  {interval}...", end=' ')
            limit = 60 if interval in ['15m', '1h'] else 80
            data = load_ohlcv_data(symbol, interval, limit=limit)
            if data:
                output = generate_candlestick_chart(symbol, interval, data)
                if output:
                    print(f"✓")
                else:
                    print("✗ failed")
            else:
                print("✗ no data")
    
    print(f"\n{'='*60}")
    print(f"Charts with MACD overlay saved to: {OUTPUT_DIR}")
    print('='*60)

if __name__ == '__main__':
    main()
