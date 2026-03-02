#!/usr/bin/env python3
"""
COMPASS Chart Generator with Indicators
Generates charts with all technical indicators overlaid
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, '/root/.openclaw/workspace')
from compass_analyzer import load_ohlcv, calculate_ema, calculate_rsi, calculate_macd, calculate_atr, calculate_vwap

OUTPUT_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/charts/compass')
DATA_DIR = Path('/root/.openclaw/workspace/data/binance')

def generate_compass_chart(symbol, interval, limit=100):
    """Generate a comprehensive chart with all COMPASS indicators"""
    df = load_ohlcv(symbol, interval)
    if df is None or len(df) < 50:
        return None
    
    df = df.tail(limit)
    
    # Calculate indicators
    ema9 = calculate_ema(df['close'], 9)
    ema21 = calculate_ema(df['close'], 21)
    ema50 = calculate_ema(df['close'], 50) if len(df) >= 50 else None
    rsi = calculate_rsi(df['close'], 14)
    macd_line, macd_signal, macd_hist = calculate_macd(df['close'])
    atr = calculate_atr(df)
    vwap = calculate_vwap(df)
    
    # Create figure with subplots
    fig = plt.figure(figsize=(14, 12), facecolor='#0d1117')
    gs = fig.add_gridspec(4, 1, height_ratios=[3, 1, 1, 1], hspace=0.05)
    
    # Main price chart
    ax1 = fig.add_subplot(gs[0])
    ax1.set_facecolor('#0d1117')
    
    # Plot candlesticks
    for i, (idx, row) in enumerate(df.iterrows()):
        x = i
        color = '#26a69a' if row['close'] >= row['open'] else '#ef5350'
        
        # Wick
        ax1.plot([x, x], [row['low'], row['high']], color='#8b949e', linewidth=0.5)
        
        # Body
        height = abs(row['close'] - row['open'])
        bottom = min(row['open'], row['close'])
        rect = plt.Rectangle((x-0.4, bottom), 0.8, height, facecolor=color, edgecolor=color)
        ax1.add_patch(rect)
    
    # Plot EMAs
    x_vals = range(len(df))
    ax1.plot(x_vals, ema9.tail(limit), color='#ffa500', linewidth=1.5, label='EMA9', alpha=0.9)
    ax1.plot(x_vals, ema21.tail(limit), color='#2196f3', linewidth=1.5, label='EMA21', alpha=0.9)
    if ema50 is not None:
        ax1.plot(x_vals, ema50.tail(limit), color='#9c27b0', linewidth=1.5, label='EMA50', alpha=0.9)
    
    # Plot VWAP
    ax1.plot(x_vals, vwap.tail(limit), color='#ffeb3b', linewidth=1.5, label='VWAP', linestyle='--', alpha=0.8)
    
    # Formatting
    ax1.set_title(f'{symbol} {interval} - COMPASS Analysis', color='#e6edf3', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Price', color='#e6edf3')
    ax1.tick_params(colors='#8b949e')
    ax1.legend(loc='upper left', facecolor='#0d1117', edgecolor='#30363d', labelcolor='#e6edf3')
    ax1.grid(True, alpha=0.2, color='#30363d')
    ax1.set_xticks([])
    
    # Volume
    ax2 = fig.add_subplot(gs[1])
    ax2.set_facecolor('#0d1117')
    colors = ['#26a69a' if df.iloc[i]['close'] >= df.iloc[i]['open'] else '#ef5350' for i in range(len(df))]
    ax2.bar(x_vals, df['volume'], color=colors, alpha=0.7, width=0.8)
    ax2.set_ylabel('Volume', color='#e6edf3')
    ax2.tick_params(colors='#8b949e')
    ax2.grid(True, alpha=0.2, color='#30363d')
    ax2.set_xticks([])
    
    # RSI
    ax3 = fig.add_subplot(gs[2])
    ax3.set_facecolor('#0d1117')
    ax3.plot(x_vals, rsi.tail(limit), color='#2196f3', linewidth=1.5)
    ax3.axhline(y=70, color='#ef5350', linestyle='--', alpha=0.5, label='Overbought')
    ax3.axhline(y=30, color='#26a69a', linestyle='--', alpha=0.5, label='Oversold')
    ax3.axhline(y=50, color='#8b949e', linestyle='-', alpha=0.3)
    ax3.fill_between(x_vals, 30, 70, alpha=0.1, color='#8b949e')
    ax3.set_ylabel('RSI(14)', color='#e6edf3')
    ax3.set_ylim(0, 100)
    ax3.tick_params(colors='#8b949e')
    ax3.grid(True, alpha=0.2, color='#30363d')
    ax3.set_xticks([])
    
    # MACD
    ax4 = fig.add_subplot(gs[3])
    ax4.set_facecolor('#0d1117')
    ax4.plot(x_vals, macd_line.tail(limit), color='#2196f3', linewidth=1.5, label='MACD')
    ax4.plot(x_vals, macd_signal.tail(limit), color='#ffa500', linewidth=1.5, label='Signal')
    
    # MACD histogram
    hist_vals = macd_hist.tail(limit).values
    for i, val in enumerate(hist_vals):
        color = '#26a69a' if val >= 0 else '#ef5350'
        ax4.bar(i, val, color=color, alpha=0.7, width=0.8)
    
    ax4.axhline(y=0, color='#8b949e', linestyle='-', alpha=0.3)
    ax4.set_ylabel('MACD', color='#e6edf3')
    ax4.tick_params(colors='#8b949e')
    ax4.grid(True, alpha=0.2, color='#30363d')
    ax4.legend(loc='upper left', facecolor='#0d1117', edgecolor='#30363d', labelcolor='#e6edf3')
    
    # X-axis labels
    ax4.set_xticks(range(0, len(df), max(1, len(df)//6)))
    ax4.set_xticklabels([df.iloc[i]['datetime'].strftime('%m/%d %H:%M') for i in range(0, len(df), max(1, len(df)//6))], 
                         rotation=45, ha='right', color='#8b949e')
    
    # Add current stats as text
    latest = df.iloc[-1]
    stats_text = f"Close: ${latest['close']:,.2f} | RSI: {rsi.iloc[-1]:.1f} | ATR: {atr.iloc[-1]:.2f}"
    fig.text(0.02, 0.98, stats_text, fontsize=10, color='#e6edf3', va='top')
    
    plt.tight_layout()
    
    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{symbol}_{interval}_compass.png"
    plt.savefig(output_file, dpi=150, facecolor='#0d1117', edgecolor='none', bbox_inches='tight')
    plt.close()
    
    return output_file

def generate_all_compass_charts():
    """Generate charts for all symbols and timeframes"""
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    intervals = ['1h', '4h', '1d']
    
    print("="*70)
    print("COMPASS Chart Generator")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    generated = []
    for symbol in symbols:
        print(f"\n{symbol}:")
        for interval in intervals:
            print(f"  {interval}...", end=' ')
            try:
                result = generate_compass_chart(symbol, interval)
                if result:
                    print(f"✓ {result.name}")
                    generated.append(result)
                else:
                    print("✗ no data")
            except Exception as e:
                print(f"✗ error: {e}")
    
    print(f"\n{'='*70}")
    print(f"Generated {len(generated)} charts")
    print(f"Output: {OUTPUT_DIR}")
    print('='*70)
    
    return generated

if __name__ == '__main__':
    generate_all_compass_charts()
