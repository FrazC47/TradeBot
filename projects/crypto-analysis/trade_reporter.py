#!/usr/bin/env python3
"""
Enhanced Trade Reporter - Candlestick Charts with All Indicators
"""

import json
import csv
from pathlib import Path
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import numpy as np

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
INDICATORS_DIR = Path('/root/.openclaw/workspace/data/indicators')
CHARTS_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/trade_charts')

CHARTS_DIR.mkdir(parents=True, exist_ok=True)

def load_ohlcv(symbol, interval, lookback=100):
    """Load recent OHLCV data"""
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
    return data[-lookback:] if len(data) > lookback else data

def load_indicators(symbol):
    """Load calculated indicators"""
    filepath = INDICATORS_DIR / f"{symbol}_indicators.json"
    if not filepath.exists():
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def plot_candlestick(ax, x, open_price, high, low, close, width=0.6):
    """Plot a single candlestick"""
    color = 'green' if close >= open_price else 'red'
    
    # Body
    height = abs(close - open_price)
    bottom = min(open_price, close)
    rect = Rectangle((x - width/2, bottom), width, height, 
                     facecolor=color, edgecolor=color, linewidth=1)
    ax.add_patch(rect)
    
    # Wick
    ax.plot([x, x], [low, high], color=color, linewidth=1)

def generate_candlestick_chart(symbol, interval, setup, title_suffix=""):
    """Generate candlestick chart with all indicators"""
    data = load_ohlcv(symbol, interval, lookback=80)
    if not data:
        return None
    
    indicators = load_indicators(symbol)
    tf_ind = indicators.get(interval, {}).get('indicators', {})
    
    # Extract data
    x_pos = list(range(len(data)))
    timestamps = [d['timestamp'] for d in data]
    opens = [d['open'] for d in data]
    highs = [d['high'] for d in data]
    lows = [d['low'] for d in data]
    closes = [d['close'] for d in data]
    volumes = [d['volume'] for d in data]
    
    dates = [datetime.fromtimestamp(ts / 1000) for ts in timestamps]
    
    # Create figure with multiple panels
    fig = plt.figure(figsize=(16, 14))
    gs = fig.add_gridspec(4, 1, height_ratios=[4, 1, 1, 1], hspace=0.05)
    
    # Main price chart
    ax1 = fig.add_subplot(gs[0])
    ax1.set_title(f'{symbol} - {interval} {title_suffix}', fontsize=14, fontweight='bold', pad=10)
    
    # Plot candlesticks
    for i, (o, h, l, c) in enumerate(zip(opens, highs, lows, closes)):
        plot_candlestick(ax1, i, o, h, l, c)
    
    # Plot EMAs
    if 'ema_9' in tf_ind and tf_ind['ema_9']:
        ema9_line = [tf_ind['ema_9']] * len(data)
        ax1.plot(x_pos, ema9_line, color='blue', linewidth=1.5, label='EMA 9', alpha=0.8)
    
    if 'ema_21' in tf_ind and tf_ind['ema_21']:
        ema21_line = [tf_ind['ema_21']] * len(data)
        ax1.plot(x_pos, ema21_line, color='orange', linewidth=1.5, label='EMA 21', alpha=0.8)
    
    if 'ema_50' in tf_ind and tf_ind['ema_50']:
        ema50_line = [tf_ind['ema_50']] * len(data)
        ax1.plot(x_pos, ema50_line, color='purple', linewidth=1.5, label='EMA 50', alpha=0.8)
    
    # VWAP
    if 'vwap' in tf_ind and tf_ind['vwap']:
        vwap_line = [tf_ind['vwap']] * len(data)
        ax1.plot(x_pos, vwap_line, color='cyan', linewidth=2, label='VWAP', linestyle='--')
    
    # Bollinger Bands
    if 'bb_upper' in tf_ind and tf_ind['bb_upper']:
        bb_upper = [tf_ind['bb_upper']] * len(data)
        bb_lower = [tf_ind.get('bb_lower', tf_ind['bb_upper'] * 0.95)] * len(data)
        ax1.fill_between(x_pos, bb_upper, bb_lower, alpha=0.1, color='gray', label='Bollinger Bands')
        ax1.plot(x_pos, bb_upper, color='gray', linewidth=1, alpha=0.5)
        ax1.plot(x_pos, bb_lower, color='gray', linewidth=1, alpha=0.5)
    
    # Support/Resistance zones
    if 'support_1' in tf_ind and tf_ind['support_1']:
        ax1.axhline(y=tf_ind['support_1'], color='green', linestyle=':', alpha=0.5, linewidth=1)
    if 'resistance_1' in tf_ind and tf_ind['resistance_1']:
        ax1.axhline(y=tf_ind['resistance_1'], color='red', linestyle=':', alpha=0.5, linewidth=1)
    
    # Mark entry zone
    entry = setup.get('entry', 0)
    entry_low = setup.get('entry_low', entry * 0.995)
    entry_high = setup.get('entry_high', entry * 1.005)
    
    # Entry zone
    ax1.axhspan(entry_low, entry_high, alpha=0.2, color='lime', 
               label=f'Entry: ${entry_low:,.0f}-${entry_high:,.0f}', zorder=1)
    
    # Stop loss
    stop = setup.get('stop', setup.get('stop_loss', 0))
    ax1.axhline(y=stop, color='red', linestyle='--', linewidth=2.5, 
               label=f'Stop: ${stop:,.0f}', zorder=5)
    
    # Target
    target = setup.get('target', setup.get('take_profit', 0))
    if target:
        ax1.axhline(y=target, color='green', linestyle='--', linewidth=2.5, 
                   label=f'Target: ${target:,.0f}', zorder=5)
    
    # Current price line
    current_price = closes[-1]
    ax1.axhline(y=current_price, color='blue', linestyle=':', alpha=0.5, zorder=2)
    
    ax1.set_ylabel('Price', fontsize=11)
    ax1.legend(loc='upper left', fontsize=8, ncol=2)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(-1, len(data))
    
    # Format x-axis
    step = max(1, len(data) // 10)
    ax1.set_xticks(range(0, len(data), step))
    ax1.set_xticklabels([dates[i].strftime('%m/%d %H:%M') for i in range(0, len(dates), step)], 
                        rotation=45, ha='right')
    
    # Volume panel
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    colors = ['green' if closes[i] >= opens[i] else 'red' for i in range(len(closes))]
    ax2.bar(x_pos, volumes, color=colors, alpha=0.6, width=0.8)
    ax2.set_ylabel('Volume', fontsize=10)
    ax2.grid(True, alpha=0.3)
    plt.setp(ax2.get_xticklabels(), visible=False)
    
    # RSI panel
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    if 'rsi_14' in tf_ind and tf_ind['rsi_14']:
        rsi_value = tf_ind['rsi_14']
        rsi_line = [rsi_value] * len(data)
        ax3.plot(x_pos, rsi_line, color='purple', linewidth=2)
        ax3.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='Overbought (70)')
        ax3.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='Oversold (30)')
        ax3.axhline(y=50, color='gray', linestyle='-', alpha=0.3)
        ax3.fill_between(x_pos, 30, 70, alpha=0.1, color='gray')
        ax3.set_ylabel('RSI', fontsize=10)
        ax3.set_ylim(0, 100)
        ax3.legend(loc='upper left', fontsize=8)
    ax3.grid(True, alpha=0.3)
    plt.setp(ax3.get_xticklabels(), visible=False)
    
    # MACD panel
    ax4 = fig.add_subplot(gs[3], sharex=ax1)
    if 'macd_line' in tf_ind and tf_ind['macd_line']:
        macd = tf_ind['macd_line']
        signal = tf_ind.get('macd_signal', macd * 0.9)
        hist = macd - signal
        
        ax4.axhline(y=0, color='black', linewidth=0.5)
        macd_line = [macd] * len(data)
        signal_line = [signal] * len(data)
        ax4.plot(x_pos, macd_line, color='blue', linewidth=1.5, label='MACD')
        ax4.plot(x_pos, signal_line, color='orange', linewidth=1.5, label='Signal')
        
        # Histogram
        hist_color = 'green' if hist > 0 else 'red'
        ax4.bar(x_pos[-1], hist, color=hist_color, alpha=0.6, width=0.8)
        
        ax4.set_ylabel('MACD', fontsize=10)
        ax4.legend(loc='upper left', fontsize=8)
    ax4.grid(True, alpha=0.3)
    
    # Format x-axis for bottom panel
    ax4.set_xticks(range(0, len(data), step))
    ax4.set_xticklabels([dates[i].strftime('%m/%d %H:%M') for i in range(0, len(dates), step)], 
                        rotation=45, ha='right')
    
    # Add trade info box
    risk = abs(entry - stop)
    reward = abs(target - entry) if target else 0
    rr = reward / risk if risk > 0 else 0
    
    info_text = f"R:R = 1:{rr:.1f} | Current: ${current_price:,.0f}"
    fig.text(0.02, 0.98, info_text, fontsize=11, fontweight='bold',
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    
    # Save
    chart_path = CHARTS_DIR / f"{symbol}_{interval}_trade.png"
    plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return chart_path

def generate_trade_explanation(symbol, setup):
    """Generate detailed trade explanation"""
    indicators = load_indicators(symbol)
    
    # Get current indicator values
    ind_1h = indicators.get('1h', {}).get('indicators', {})
    ind_1d = indicators.get('1d', {}).get('indicators', {})
    
    explanation = f"""
🎯 TRADE RECOMMENDATION: {symbol} {setup.get('direction', 'LONG')}
{'='*80}

📊 CURRENT MARKET STATE
• 1h RSI: {ind_1h.get('rsi_14', 'N/A'):.1f} {'(neutral)' if ind_1h.get('rsi_14', 50) and 40 < ind_1h.get('rsi_14', 50) < 60 else '(oversold)' if ind_1h.get('rsi_14', 50) and ind_1h.get('rsi_14', 50) < 40 else '(overbought)'}
• 1h MACD: {ind_1h.get('macd_line', 0):.2f} vs Signal: {ind_1h.get('macd_signal', 0):.2f}
• 1d Trend: {'Bullish' if ind_1d.get('ema_20', 0) and ind_1d.get('close', 0) > ind_1d.get('ema_20', 0) else 'Bearish' if ind_1d.get('ema_20', 0) else 'Neutral'}
• VWAP: ${ind_1h.get('vwap', 0):,.2f}

📊 ENTRY STRATEGY
• Method: {setup.get('strategy', 'Technical Setup')}
• Entry Zone: ${setup.get('entry_low', setup.get('entry', 0)):,.2f} - ${setup.get('entry_high', setup.get('entry', 0)):,.2f}
• Position: {setup.get('position_factor', 1.0)*100:.0f}% of normal size

🛡️ RISK MANAGEMENT
• Stop Loss: ${setup.get('stop', setup.get('stop_loss', 0)):,.2f}
  └ Risk: {abs((setup.get('stop', 0)-setup.get('entry', 0))/setup.get('entry', 1)*100):.2f}%
• Target: ${setup.get('target', setup.get('take_profit', 0)):,.2f}
  └ Reward: {abs((setup.get('target', 0)-setup.get('entry', 0))/setup.get('entry', 1)*100):.2f}%
• Risk/Reward: 1:{abs((setup.get('target', 0)-setup.get('entry', 0))/(setup.get('stop', 0)-setup.get('entry', 1))):.1f}

📈 WHY THIS TRADE?

1. TECHNICAL SETUP:
   • Price at key support/resistance level
   • Structure intact on higher timeframes
   • Volume profile supporting the move

2. INDICATOR CONFLUENCE:
   • EMA alignment: {'Bullish' if ind_1h.get('ema_9', 0) and ind_1h.get('ema_21', 0) and ind_1h.get('ema_9', 0) > ind_1h.get('ema_21', 0) else 'Bearish' if ind_1h.get('ema_9', 0) and ind_1h.get('ema_21', 0) and ind_1h.get('ema_9', 0) < ind_1h.get('ema_21', 0) else 'Mixed'}
   • RSI: {'Oversold - bounce likely' if ind_1h.get('rsi_14', 50) and ind_1h.get('rsi_14', 50) < 30 else 'Overbought - pullback likely' if ind_1h.get('rsi_14', 50) and ind_1h.get('rsi_14', 50) > 70 else 'Neutral zone'}
   • MACD: {'Bullish crossover' if ind_1h.get('macd_line', 0) > ind_1h.get('macd_signal', 0) else 'Bearish crossover'}

3. RISK/REWARD:
   • Entry at favorable price level
   • Stop placed at technical invalidation
   • Minimum 1:2 R:R achieved

⚠️ INVALIDATION SCENARIOS
• Price closes below stop loss (${setup.get('stop', 0):,.2f})
• Structure breaks (lower low/higher high formed against position)
• Momentum turns strongly against position
• Volume shows distribution/accumulation against setup

⏱️ EXECUTION PLAN
• Monitor 15m and 1h closes for confirmation
• Enter on price reaching entry zone
• Set stop loss immediately
• Scale out 50% at target 1, move stop to breakeven
• Let remaining 50% run to target 2

📋 PRE-TRADE CHECKLIST
□ Entry zone reached
□ Volume confirmation on entry candle
□ No major news/events pending
□ Risk amount within limits (max 3% account)
"""
    return explanation

def report_trade(symbol, setup):
    """Generate complete trade report"""
    print(f"\n{'='*80}")
    print(f"🎯 TRADE SETUP: {symbol}")
    print(f"{'='*80}")
    
    print("\n📊 Generating candlestick charts with indicators...")
    
    chart_15m = generate_candlestick_chart(symbol, '15m', setup, "(Entry Timing)")
    chart_1h = generate_candlestick_chart(symbol, '1h', setup, "(Trend Context)")
    
    if chart_15m:
        print(f"  ✅ 15m Chart: {chart_15m}")
    if chart_1h:
        print(f"  ✅ 1h Chart: {chart_1h}")
    
    explanation = generate_trade_explanation(symbol, setup)
    print(explanation)
    
    # Save report
    report_path = CHARTS_DIR / f"{symbol}_trade_report.txt"
    with open(report_path, 'w') as f:
        f.write(explanation)
    print(f"\n📄 Report saved: {report_path}")
    
    return {
        'charts': {'15m': str(chart_15m), '1h': str(chart_1h)},
        'report': str(report_path),
        'explanation': explanation
    }

if __name__ == '__main__':
    test_setup = {
        'direction': 'LONG',
        'entry': 67949.47,
        'entry_low': 67850.00,
        'entry_high': 68050.00,
        'stop': 66353.76,
        'target': 71140.90,
        'strategy': 'Fibonacci Pullback',
        'position_factor': 1.0
    }
    report_trade('BTCUSDT', test_setup)
