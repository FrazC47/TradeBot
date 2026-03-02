#!/usr/bin/env python3
"""
COMPASS Enhanced Chart Generator with Trend Descriptions
Generates charts with indicators, trend analysis, and timeframe comparisons
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, '/root/.openclaw/workspace')
from compass_analyzer import load_ohlcv, calculate_ema, calculate_rsi, calculate_macd, calculate_atr, calculate_vwap, TIMEFRAME_CONFIG

OUTPUT_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/charts/compass/enhanced')
DATA_DIR = Path('/root/.openclaw/workspace/data/binance')

def get_trend_description(trend, rsi, macd_hist, volume_ratio, close, vwap):
    """Generate human-readable trend description"""
    descriptions = []
    
    # Primary trend
    if trend == 'Bullish':
        descriptions.append("📈 BULLISH: Price above key EMAs with upward momentum")
    elif trend == 'Bearish':
        descriptions.append("📉 BEARISH: Price below key EMAs with downward pressure")
    else:
        descriptions.append("➖ NEUTRAL: Price consolidating near equilibrium")
    
    # RSI context
    if rsi > 70:
        descriptions.append("⚠️ RSI Overbought (>70) - Potential pullback risk")
    elif rsi > 55:
        descriptions.append("✅ RSI Bullish Zone (55-70) - Momentum strong")
    elif rsi < 30:
        descriptions.append("⚠️ RSI Oversold (<30) - Potential bounce opportunity")
    elif rsi < 45:
        descriptions.append("❌ RSI Bearish Zone (30-45) - Weak momentum")
    else:
        descriptions.append("➖ RSI Neutral (45-55) - Balanced pressure")
    
    # Volume context
    if volume_ratio > 2.0:
        descriptions.append(f"🔥 High Volume ({volume_ratio:.1f}x) - Strong participation")
    elif volume_ratio > 1.5:
        descriptions.append(f"📊 Confirming Volume ({volume_ratio:.1f}x) - Validating move")
    elif volume_ratio < 0.8:
        descriptions.append(f"💤 Low Volume ({volume_ratio:.1f}x) - Weak conviction")
    
    # VWAP context
    vwap_diff = ((close - vwap) / vwap) * 100
    if vwap_diff > 1:
        descriptions.append(f"💚 Above VWAP (+{vwap_diff:.1f}%) - Buyers in control")
    elif vwap_diff < -1:
        descriptions.append(f"❤️ Below VWAP ({vwap_diff:.1f}%) - Sellers dominant")
    else:
        descriptions.append(f"➖ Near VWAP ({vwap_diff:+.1f}%) - Fair value zone")
    
    # MACD context
    if macd_hist > 0 and macd_hist > abs(macd_hist) * 0.5:
        descriptions.append("📊 MACD Bullish - Momentum accelerating")
    elif macd_hist < 0 and abs(macd_hist) > macd_hist * 0.5:
        descriptions.append("📉 MACD Bearish - Momentum decelerating")
    
    return "\n".join(descriptions)

def get_timeframe_comparison(interval, current_trend, higher_tf_trend):
    """Compare current timeframe with higher timeframe"""
    if higher_tf_trend is None:
        return "No higher timeframe data for comparison"
    
    if current_trend == higher_tf_trend:
        if current_trend == 'Bullish':
            return f"✅ ALIGNED: {interval} confirms higher timeframe bullish trend - Good for longs"
        elif current_trend == 'Bearish':
            return f"✅ ALIGNED: {interval} confirms higher timeframe bearish trend - Good for shorts"
        else:
            return f"➖ CONSOLIDATION: Both timeframes neutral - Wait for breakout"
    else:
        if higher_tf_trend == 'Bullish' and current_trend == 'Bearish':
            return f"⚠️ PULLBACK: {interval} showing pullback within higher TF uptrend - Watch for support"
        elif higher_tf_trend == 'Bearish' and current_trend == 'Bullish':
            return f"⚠️ BOUNCE: {interval} showing bounce within higher TF downtrend - Watch for resistance"
        else:
            return f"🔄 TRANSITION: {interval} may be transitioning - Wait for confirmation"

def generate_enhanced_chart(symbol, interval, higher_tf_data=None, limit=100):
    """Generate comprehensive chart with all indicators and descriptions"""
    df = load_ohlcv(symbol, interval)
    if df is None or len(df) < 50:
        return None
    
    df = df.tail(limit)
    config = TIMEFRAME_CONFIG.get(interval, {})
    
    # Calculate indicators
    ema_fast = calculate_ema(df['close'], config.get('ema_fast', 9))
    ema_slow = calculate_ema(df['close'], config.get('ema_slow', 21))
    ema50 = calculate_ema(df['close'], 50) if len(df) >= 50 else None
    rsi = calculate_rsi(df['close'], config.get('rsi_period', 14))
    macd_line, macd_signal, macd_hist = calculate_macd(df['close'])
    atr = calculate_atr(df)
    vwap = calculate_vwap(df)
    volume_sma = df['volume'].rolling(window=20).mean()
    
    # Get latest values
    latest = df.iloc[-1]
    current_close = latest['close']
    current_rsi = rsi.iloc[-1]
    current_macd_hist = macd_hist.iloc[-1]
    current_volume_ratio = latest['volume'] / volume_sma.iloc[-1] if volume_sma.iloc[-1] > 0 else 0
    current_vwap = vwap.iloc[-1]
    
    # Determine trend
    trend = 'Neutral'
    if current_close > ema_fast.iloc[-1] > ema_slow.iloc[-1]:
        trend = 'Bullish'
    elif current_close < ema_slow.iloc[-1] < ema_fast.iloc[-1]:
        trend = 'Bearish'
    
    # Create figure with extra space for text
    fig = plt.figure(figsize=(16, 16), facecolor='#0d1117')
    gs = fig.add_gridspec(5, 1, height_ratios=[4, 1.5, 1.5, 1.5, 2.5], hspace=0.08)
    
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
    ax1.plot(x_vals, ema_fast.tail(limit), color='#ffa500', linewidth=2, label=f"EMA{config.get('ema_fast', 9)}", alpha=0.9)
    ax1.plot(x_vals, ema_slow.tail(limit), color='#2196f3', linewidth=2, label=f"EMA{config.get('ema_slow', 21)}", alpha=0.9)
    if ema50 is not None:
        ax1.plot(x_vals, ema50.tail(limit), color='#9c27b0', linewidth=2, label='EMA50', alpha=0.9)
    
    # Plot VWAP
    ax1.plot(x_vals, vwap.tail(limit), color='#ffeb3b', linewidth=2, label='VWAP', linestyle='--', alpha=0.8)
    
    # Title with trend
    title_color = '#26a69a' if trend == 'Bullish' else '#ef5350' if trend == 'Bearish' else '#8b949e'
    ax1.set_title(f'{symbol} {interval} - {trend} | Price: ${current_close:,.2f}', 
                  color=title_color, fontsize=14, fontweight='bold', pad=10)
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
    ax2.plot(x_vals, volume_sma.tail(limit), color='#2196f3', linewidth=1.5, label='Volume SMA20')
    ax2.set_ylabel('Volume', color='#e6edf3')
    ax2.tick_params(colors='#8b949e')
    ax2.legend(loc='upper left', facecolor='#0d1117', edgecolor='#30363d', labelcolor='#e6edf3')
    ax2.grid(True, alpha=0.2, color='#30363d')
    ax2.set_xticks([])
    
    # RSI
    ax3 = fig.add_subplot(gs[2])
    ax3.set_facecolor('#0d1117')
    ax3.plot(x_vals, rsi.tail(limit), color='#2196f3', linewidth=2)
    ax3.axhline(y=70, color='#ef5350', linestyle='--', alpha=0.7, label='Overbought (70)')
    ax3.axhline(y=30, color='#26a69a', linestyle='--', alpha=0.7, label='Oversold (30)')
    ax3.axhline(y=50, color='#8b949e', linestyle='-', alpha=0.3)
    ax3.fill_between(x_vals, 30, 70, alpha=0.05, color='#8b949e')
    ax3.set_ylabel(f'RSI({config.get("rsi_period", 14)})', color='#e6edf3')
    ax3.set_ylim(0, 100)
    ax3.tick_params(colors='#8b949e')
    ax3.legend(loc='upper left', facecolor='#0d1117', edgecolor='#30363d', labelcolor='#e6edf3')
    ax3.grid(True, alpha=0.2, color='#30363d')
    ax3.set_xticks([])
    
    # MACD
    ax4 = fig.add_subplot(gs[3])
    ax4.set_facecolor('#0d1117')
    ax4.plot(x_vals, macd_line.tail(limit), color='#2196f3', linewidth=1.5, label='MACD')
    ax4.plot(x_vals, macd_signal.tail(limit), color='#ffa500', linewidth=1.5, label='Signal')
    
    hist_vals = macd_hist.tail(limit).values
    for i, val in enumerate(hist_vals):
        color = '#26a69a' if val >= 0 else '#ef5350'
        ax4.bar(i, val, color=color, alpha=0.7, width=0.8)
    
    ax4.axhline(y=0, color='#8b949e', linestyle='-', alpha=0.3)
    ax4.set_ylabel('MACD', color='#e6edf3')
    ax4.tick_params(colors='#8b949e')
    ax4.legend(loc='upper left', facecolor='#0d1117', edgecolor='#30363d', labelcolor='#e6edf3')
    ax4.grid(True, alpha=0.2, color='#30363d')
    ax4.set_xticks([])
    
    # Text description panel
    ax5 = fig.add_subplot(gs[4])
    ax5.set_facecolor('#161b22')
    ax5.axis('off')
    
    # Generate descriptions
    trend_desc = get_trend_description(
        trend, current_rsi, current_macd_hist, 
        current_volume_ratio, current_close, current_vwap
    )
    
    higher_trend = higher_tf_data.get('trend') if higher_tf_data else None
    comparison = get_timeframe_comparison(interval, trend, higher_trend)
    
    # Add text
    y_pos = 0.95
    ax5.text(0.02, y_pos, f"📊 TREND ANALYSIS - {interval}", 
             fontsize=12, fontweight='bold', color='#e6edf3', 
             transform=ax5.transAxes, verticalalignment='top')
    
    y_pos -= 0.12
    for line in trend_desc.split('\n'):
        color = '#e6edf3'
        if '✅' in line or '📈' in line or '💚' in line:
            color = '#26a69a'
        elif '❌' in line or '📉' in line or '❤️' in line:
            color = '#ef5350'
        elif '⚠️' in line:
            color = '#ffa500'
        
        ax5.text(0.02, y_pos, line, fontsize=9, color=color,
                transform=ax5.transAxes, verticalalignment='top')
        y_pos -= 0.09
    
    # Add timeframe comparison
    y_pos -= 0.05
    ax5.text(0.02, y_pos, f"🔗 TIMEFRAME ALIGNMENT", 
             fontsize=11, fontweight='bold', color='#e6edf3', 
             transform=ax5.transAxes, verticalalignment='top')
    
    y_pos -= 0.10
    comp_color = '#26a69a' if '✅' in comparison else '#ef5350' if '❌' in comparison else '#ffa500' if '⚠️' in comparison else '#e6edf3'
    ax5.text(0.02, y_pos, comparison, fontsize=9, color=comp_color,
            transform=ax5.transAxes, verticalalignment='top', wrap=True)
    
    # Add stats
    y_pos -= 0.15
    stats_text = f"ATR: ${atr.iloc[-1]:.2f} | Volume Ratio: {current_volume_ratio:.2f}x | VWAP: ${current_vwap:,.2f}"
    ax5.text(0.02, y_pos, stats_text, fontsize=9, color='#8b949e',
            transform=ax5.transAxes, verticalalignment='top')
    
    # X-axis labels on bottom
    ax4.set_xticks(range(0, len(df), max(1, len(df)//6)))
    ax4.set_xticklabels([df.iloc[i]['datetime'].strftime('%m/%d %H:%M') for i in range(0, len(df), max(1, len(df)//6))], 
                         rotation=45, ha='right', color='#8b949e')
    
    plt.tight_layout()
    
    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{symbol}_{interval}_enhanced.png"
    plt.savefig(output_file, dpi=150, facecolor='#0d1117', edgecolor='none', 
                bbox_inches='tight', pad_inches=0.3)
    plt.close()
    
    return output_file, {'trend': trend, 'close': current_close, 'rsi': current_rsi}

def generate_all_enhanced_charts():
    """Generate enhanced charts for all symbols with timeframe comparisons"""
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    intervals = ['1d', '4h', '1h']  # Order matters for hierarchy
    
    print("="*70)
    print("COMPASS Enhanced Chart Generator")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    for symbol in symbols:
        print(f"\n{symbol}:")
        
        # First pass: collect data for all timeframes
        tf_data = {}
        for interval in intervals:
            df = load_ohlcv(symbol, interval)
            if df is not None and len(df) >= 50:
                ema9 = calculate_ema(df['close'], 9)
                ema21 = calculate_ema(df['close'], 21)
                latest = df.iloc[-1]
                
                trend = 'Neutral'
                if latest['close'] > ema9.iloc[-1] > ema21.iloc[-1]:
                    trend = 'Bullish'
                elif latest['close'] < ema21.iloc[-1] < ema9.iloc[-1]:
                    trend = 'Bearish'
                
                tf_data[interval] = {'trend': trend, 'close': latest['close']}
        
        # Second pass: generate charts with comparisons
        for i, interval in enumerate(intervals):
            print(f"  {interval}...", end=' ')
            try:
                # Get higher timeframe data if available
                higher_tf = tf_data.get(intervals[i-1]) if i > 0 else None
                
                result = generate_enhanced_chart(symbol, interval, higher_tf, limit=80)
                if result:
                    print(f"✓ {result[0].name}")
                else:
                    print("✗ no data")
            except Exception as e:
                print(f"✗ error: {e}")
    
    print(f"\n{'='*70}")
    print(f"Enhanced charts saved to: {OUTPUT_DIR}")
    print('='*70)

if __name__ == '__main__':
    generate_all_enhanced_charts()
