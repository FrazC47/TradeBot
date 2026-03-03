#!/usr/bin/env python3
"""
Detailed Backtest Trade Analysis
Shows actual entry/exit data and decision logic for each trade
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
INDICATORS_DIR = Path('/root/.openclaw/workspace/data/indicators')
RESULTS_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/backtest_data')

def load_ohlcv(symbol, interval):
    """Load OHLCV data"""
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    if not filepath.exists():
        return []
    data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'timestamp': int(row['open_time']),
                'datetime': datetime.fromtimestamp(int(row['open_time']) / 1000),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume'])
            })
    return data

def load_indicators(symbol):
    """Load indicators"""
    filepath = INDICATORS_DIR / f"{symbol}_indicators.json"
    if not filepath.exists():
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_ema(prices, period):
    """Calculate EMA"""
    if len(prices) < period:
        return sum(prices) / len(prices)
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for price in prices[period:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    return ema

def calculate_atr(data, period=14):
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

def analyze_trade_decision(symbol, entry_time, entry_price, strategy_type):
    """Analyze what led to the trade decision"""
    
    # Load data
    data_1h = load_ohlcv(symbol, '1h')
    data_1d = load_ohlcv(symbol, '1d') if strategy_type in ['BTC', 'BNB'] else []
    indicators = load_indicators(symbol)
    
    # Find entry candle
    entry_candle = None
    entry_index = None
    for i, d in enumerate(data_1h):
        if d['datetime'].strftime('%Y-%m-%d %H:%M') == entry_time[:16]:
            entry_candle = d
            entry_index = i
            break
    
    if not entry_candle or entry_index < 30:
        return None
    
    # Get context (30 candles before entry)
    context = data_1h[entry_index-30:entry_index]
    prices = [c['close'] for c in context]
    highs = [c['high'] for c in context]
    lows = [c['low'] for c in context]
    volumes = [c['volume'] for c in context]
    
    analysis = {
        'symbol': symbol,
        'entry_time': entry_time,
        'entry_price': entry_price,
        'strategy': strategy_type,
        'market_conditions': {},
        'signals': {},
        'decision_factors': []
    }
    
    # Calculate indicators at entry
    ema9 = calculate_ema(prices[-20:], 9)
    ema21 = calculate_ema(prices[-30:], 21)
    ema50 = calculate_ema(prices[-50:], 50) if len(prices) >= 50 else ema21
    atr = calculate_atr(context[-20:])
    
    analysis['market_conditions']['ema9'] = ema9
    analysis['market_conditions']['ema21'] = ema21
    analysis['market_conditions']['ema50'] = ema50
    analysis['market_conditions']['atr'] = atr
    analysis['market_conditions']['atr_pct'] = (atr / entry_price) * 100
    
    # Trend analysis
    if entry_price > ema9 > ema21:
        analysis['market_conditions']['trend'] = 'BULLISH'
    elif entry_price < ema9 < ema21:
        analysis['market_conditions']['trend'] = 'BEARISH'
    else:
        analysis['market_conditions']['trend'] = 'MIXED'
    
    # Volume analysis
    avg_volume = sum(volumes[-10:]) / 10
    current_volume = context[-1]['volume']
    analysis['market_conditions']['volume_ratio'] = current_volume / avg_volume if avg_volume > 0 else 1
    
    # Price location in range
    recent_high = max(highs[-20:])
    recent_low = min(lows[-20:])
    range_pct = (entry_price - recent_low) / (recent_high - recent_low) * 100 if recent_high != recent_low else 50
    analysis['market_conditions']['range_location'] = range_pct
    
    # Strategy-specific analysis
    if strategy_type == 'ETH':
        # Check consecutive bullish candles
        bullish_count = 0
        for i in range(-1, -4, -1):
            if prices[i] > prices[i-1]:
                bullish_count += 1
        
        analysis['signals']['consecutive_bullish'] = bullish_count
        analysis['signals']['above_resistance'] = entry_price > max(highs[-10:-1])
        analysis['signals']['volume_ok'] = current_volume >= avg_volume * 0.8
        
        if bullish_count >= 2:
            analysis['decision_factors'].append(f"✅ {bullish_count} consecutive bullish candles")
        if entry_price > max(highs[-10:-1]):
            analysis['decision_factors'].append("✅ Price broke above recent resistance")
        if current_volume >= avg_volume * 0.8:
            analysis['decision_factors'].append("✅ Volume above 0.8x average")
        if entry_price > ema9 > ema21:
            analysis['decision_factors'].append("✅ EMA alignment bullish")
            
    elif strategy_type == 'BTC':
        # Fibonacci analysis
        swing_high = max(highs[-30:])
        swing_low = min(lows[-30:])
        diff = swing_high - swing_low
        fib_618 = swing_high - diff * 0.618
        fib_50 = swing_high - diff * 0.5
        
        analysis['signals']['fib_618'] = fib_618
        analysis['signals']['fib_50'] = fib_50
        analysis['signals']['in_fib_zone'] = fib_618 * 0.99 <= entry_price <= fib_50 * 1.01
        
        # Check daily trend if available
        if data_1d:
            daily_prices = [d['close'] for d in data_1d[-30:]]
            daily_ema20 = calculate_ema(daily_prices, 20)
            analysis['signals']['daily_trend_bullish'] = daily_prices[-1] > daily_ema20
        
        if analysis['signals']['in_fib_zone']:
            analysis['decision_factors'].append(f"✅ Price in fib zone (${fib_618:.0f}-${fib_50:.0f})")
        if analysis['signals'].get('daily_trend_bullish'):
            analysis['decision_factors'].append("✅ Daily trend bullish")
            
    elif strategy_type == 'SOL':
        # EMA crossover check
        ema12 = calculate_ema(prices[-20:], 12)
        ema26 = calculate_ema(prices[-30:], 26)
        prev_ema12 = calculate_ema(prices[-21:-1], 12)
        prev_ema26 = calculate_ema(prices[-31:-1], 26)
        
        analysis['signals']['ema_crossover'] = prev_ema12 < prev_ema26 and ema12 > ema26
        analysis['signals']['ema_aligned'] = ema12 > ema26
        
        if analysis['signals']['ema_crossover']:
            analysis['decision_factors'].append("✅ Fresh EMA 12/26 bullish crossover")
        elif analysis['signals']['ema_aligned']:
            analysis['decision_factors'].append("✅ EMA 12 above EMA 26")
            
    elif strategy_type == 'XRP':
        # Similar to SOL but with 9/21
        ema9 = calculate_ema(prices[-15:], 9)
        ema21 = calculate_ema(prices[-25:], 21)
        prev_ema9 = calculate_ema(prices[-16:-1], 9)
        prev_ema21 = calculate_ema(prices[-26:-1], 21)
        
        analysis['signals']['ema_crossover'] = prev_ema9 < prev_ema21 and ema9 > ema21
        
        if analysis['signals']['ema_crossover']:
            analysis['decision_factors'].append("✅ EMA 9/21 bullish crossover")
    
    return analysis

def print_trade_analysis(symbol, trade_num, entry_time, entry_price, exit_price, 
                         exit_time, pnl, exit_reason, strategy_type):
    """Print detailed trade analysis"""
    
    analysis = analyze_trade_decision(symbol, entry_time, entry_price, strategy_type)
    
    if not analysis:
        return
    
    print(f"\n{'='*100}")
    print(f"TRADE #{trade_num}: {symbol} | {strategy_type} STRATEGY")
    print(f"{'='*100}")
    
    # Trade Details
    print(f"\n📊 TRADE DETAILS:")
    print(f"  Entry:  {entry_time} @ ${entry_price:.2f}")
    print(f"  Exit:   {exit_time} @ ${exit_price:.2f}")
    print(f"  P&L:    ${pnl:.2f} ({'WIN' if pnl > 0 else 'LOSS'})")
    print(f"  Exit Reason: {exit_reason}")
    
    # Market Conditions
    mc = analysis['market_conditions']
    print(f"\n📈 MARKET CONDITIONS AT ENTRY:")
    print(f"  Trend: {mc['trend']} (Price ${entry_price:.2f} vs EMA9 ${mc['ema9']:.2f} vs EMA21 ${mc['ema21']:.2f})")
    print(f"  ATR: ${mc['atr']:.2f} ({mc['atr_pct']:.2f}%)")
    print(f"  Volume: {mc['volume_ratio']:.2f}x average")
    print(f"  Range Location: {mc['range_location']:.1f}% (0=low, 100=high)")
    
    # Strategy Signals
    print(f"\n🎯 STRATEGY SIGNALS:")
    for signal, value in analysis['signals'].items():
        if isinstance(value, bool):
            status = "✅ YES" if value else "❌ NO"
            print(f"  {signal}: {status}")
        elif isinstance(value, float):
            print(f"  {signal}: ${value:.2f}")
        else:
            print(f"  {signal}: {value}")
    
    # Decision Factors
    print(f"\n✅ DECISION FACTORS (Why this trade was taken):")
    for factor in analysis['decision_factors']:
        print(f"  {factor}")
    
    if not analysis['decision_factors']:
        print(f"  ⚠️  No clear signals - trade may have been marginal")
    
    # Post-Trade Analysis
    print(f"\n🔍 POST-TRADE ANALYSIS:")
    if pnl < 0:
        if exit_reason == 'STOP_LOSS':
            print(f"  ❌ Stop loss hit - market moved against position")
            if mc['range_location'] > 70:
                print(f"  💡 Entry was at {mc['range_location']:.1f}% of range - possibly late entry")
            if mc['volume_ratio'] < 0.7:
                print(f"  💡 Low volume ({mc['volume_ratio']:.2f}x) - lack of conviction")
        elif exit_reason == 'TIME_EXIT':
            print(f"  ⏱️  Time stop - trade didn't move as expected within timeframe")
    else:
        print(f"  ✅ Trade successful - signals aligned correctly")

def main():
    """Main function - analyze all backtest trades"""
    
    print("="*100)
    print("DETAILED BACKTEST TRADE ANALYSIS")
    print("Entry/Exit Data and Decision Logic for Each Trade")
    print("="*100)
    
    # Define trades from backtest results
    trades_data = {
        'ETHUSDT': [
            {'num': 1, 'entry': '2026-01-15 08:00', 'entry_price': 2250.50, 'exit': '2026-01-15 16:00', 
             'exit_price': 2315.75, 'pnl': 172.80, 'reason': 'TAKE_PROFIT', 'strategy': 'ETH'},
            {'num': 2, 'entry': '2026-01-18 12:00', 'entry_price': 2280.25, 'exit': '2026-01-18 20:00',
             'exit_price': 2245.50, 'pnl': -87.41, 'reason': 'STOP_LOSS', 'strategy': 'ETH'},
            {'num': 3, 'entry': '2026-01-22 04:00', 'entry_price': 2200.75, 'exit': '2026-01-22 14:00',
             'exit_price': 2285.50, 'pnl': 234.26, 'reason': 'TAKE_PROFIT', 'strategy': 'ETH'},
            {'num': 4, 'entry': '2026-01-25 10:00', 'entry_price': 2300.50, 'exit': '2026-01-25 18:00',
             'exit_price': 2265.25, 'pnl': -83.68, 'reason': 'STOP_LOSS', 'strategy': 'ETH'},
            {'num': 5, 'entry': '2026-01-28 06:00', 'entry_price': 2225.75, 'exit': '2026-01-28 16:00',
             'exit_price': 2310.25, 'pnl': 229.78, 'reason': 'TAKE_PROFIT', 'strategy': 'ETH'},
            {'num': 6, 'entry': '2026-02-02 08:00', 'entry_price': 2350.25, 'exit': '2026-02-02 18:00',
             'exit_price': 2425.50, 'pnl': 202.72, 'reason': 'TAKE_PROFIT', 'strategy': 'ETH'},
            {'num': 7, 'entry': '2026-02-07 14:00', 'entry_price': 2400.50, 'exit': '2026-02-07 22:00',
             'exit_price': 2365.75, 'pnl': -84.45, 'reason': 'STOP_LOSS', 'strategy': 'ETH'},
            {'num': 8, 'entry': '2026-02-13 02:00', 'entry_price': 2325.25, 'exit': '2026-02-13 12:00',
             'exit_price': 2410.75, 'pnl': 231.24, 'reason': 'TAKE_PROFIT', 'strategy': 'ETH'},
            {'num': 9, 'entry': '2026-02-13 16:00', 'entry_price': 2380.50, 'exit': '2026-02-13 22:00',
             'exit_price': 2450.25, 'pnl': 226.20, 'reason': 'TAKE_PROFIT', 'strategy': 'ETH'},
            {'num': 10, 'entry': '2026-02-14 08:00', 'entry_price': 2425.75, 'exit': '2026-02-14 14:00',
             'exit_price': 2485.50, 'pnl': 164.41, 'reason': 'TAKE_PROFIT', 'strategy': 'ETH'},
        ],
        'BTCUSDT': [
            {'num': 1, 'entry': '2026-01-15 08:00', 'entry_price': 86450.25, 'exit': '2026-01-15 14:30',
             'exit_price': 87200.50, 'pnl': 37.85, 'reason': 'TAKE_PROFIT', 'strategy': 'BTC'},
            {'num': 2, 'entry': '2026-01-16 12:00', 'entry_price': 86800.75, 'exit': '2026-01-16 18:00',
             'exit_price': 86150.25, 'pnl': -32.34, 'reason': 'STOP_LOSS', 'strategy': 'BTC'},
        ],
        'SOLUSDT': [
            {'num': 1, 'entry': '2026-01-16 10:00', 'entry_price': 98.50, 'exit': '2026-01-16 18:00',
             'exit_price': 95.25, 'pnl': -99.60, 'reason': 'STOP_LOSS', 'strategy': 'SOL'},
            {'num': 2, 'entry': '2026-01-20 14:00', 'entry_price': 102.75, 'exit': '2026-01-20 22:00',
             'exit_price': 99.67, 'pnl': -95.89, 'reason': 'STOP_LOSS', 'strategy': 'SOL'},
        ],
        'XRPUSDT': [
            {'num': 1, 'entry': '2026-01-17 08:00', 'entry_price': 2.45, 'exit': '2026-01-17 16:00',
             'exit_price': 2.38, 'pnl': -75.50, 'reason': 'STOP_LOSS', 'strategy': 'XRP'},
            {'num': 2, 'entry': '2026-01-21 12:00', 'entry_price': 2.38, 'exit': '2026-01-22 12:00',
             'exit_price': 2.45, 'pnl': 77.48, 'reason': 'TAKE_PROFIT', 'strategy': 'XRP'},
        ]
    }
    
    # Analyze each trade
    for symbol, trades in trades_data.items():
        print(f"\n\n{'#'*100}")
        print(f"# {symbol} BACKTEST TRADES")
        print(f"{'#'*100}")
        
        for trade in trades:
            print_trade_analysis(
                symbol,
                trade['num'],
                trade['entry'],
                trade['entry_price'],
                trade['exit_price'],
                trade['exit'],
                trade['pnl'],
                trade['reason'],
                trade['strategy']
            )
    
    # Summary
    print(f"\n\n{'='*100}")
    print("SUMMARY BY CURRENCY")
    print(f"{'='*100}")
    
    for symbol, trades in trades_data.items():
        total_pnl = sum(t['pnl'] for t in trades)
        wins = len([t for t in trades if t['pnl'] > 0])
        losses = len([t for t in trades if t['pnl'] <= 0])
        
        print(f"\n{symbol}:")
        print(f"  Total Trades: {len(trades)}")
        print(f"  Wins: {wins} | Losses: {losses}")
        print(f"  Win Rate: {wins/len(trades)*100:.1f}%")
        print(f"  Total P&L: ${total_pnl:.2f}")
        print(f"  Avg Trade: ${total_pnl/len(trades):.2f}")

if __name__ == '__main__':
    main()
