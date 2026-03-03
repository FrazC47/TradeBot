#!/usr/bin/env python3
"""
Trade Forensics - Analyzing Losing Trades by Currency
Identifies patterns and root causes of trade failures
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
INDICATORS_DIR = Path('/root/.openclaw/workspace/data/indicators')
RESULTS_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/backtest_data')

def load_trade_history(symbol):
    """Load trade history from CSV"""
    filepath = RESULTS_DIR / f"{symbol}_trade_history.csv"
    if not filepath.exists():
        return []
    
    trades = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if float(row['net_pnl_usd']) <= 0:  # Only losing trades
                trades.append({
                    'trade_id': row['trade_id'],
                    'symbol': row['symbol'],
                    'entry_time': row['entry_time'],
                    'entry_price': float(row['entry_price']),
                    'exit_time': row['exit_time'],
                    'exit_price': float(row['exit_price']),
                    'stop_loss': float(row['stop_loss']),
                    'take_profit': float(row['take_profit']),
                    'net_pnl': float(row['net_pnl_usd']),
                    'exit_reason': row['exit_reason'],
                    'duration': float(row['trade_duration_hours'])
                })
    return trades

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

def analyze_market_conditions_at_entry(trade, ohlcv_data, indicators):
    """Analyze market conditions when trade was entered"""
    entry_time = datetime.strptime(trade['entry_time'], '%Y-%m-%d %H:%M:%S')
    entry_ts = int(entry_time.timestamp() * 1000)
    
    # Find entry candle
    entry_candle = None
    for i, candle in enumerate(ohlcv_data):
        if candle['timestamp'] == entry_ts:
            entry_candle = candle
            entry_index = i
            break
    
    if not entry_candle or entry_index < 20:
        return None
    
    # Get context (20 candles before entry)
    context = ohlcv_data[entry_index-20:entry_index]
    
    # Calculate metrics
    prices = [c['close'] for c in context]
    highs = [c['high'] for c in context]
    lows = [c['low'] for c in context]
    volumes = [c['volume'] for c in context]
    
    # Trend analysis
    sma10 = sum(prices[-10:]) / 10
    sma20 = sum(prices[-20:]) / 20
    trend_direction = 'UP' if prices[-1] > sma10 > sma20 else 'DOWN' if prices[-1] < sma10 < sma20 else 'CHOPPY'
    
    # Volatility
    atr = sum(h - l for h, l in zip(highs[-14:], lows[-14:])) / 14
    atr_pct = (atr / prices[-1]) * 100
    
    # Volume analysis
    avg_volume = sum(volumes[-10:]) / 10
    volume_ratio = entry_candle['volume'] / avg_volume if avg_volume > 0 else 1
    
    # Price location in recent range
    recent_high = max(highs)
    recent_low = min(lows)
    range_pct = (prices[-1] - recent_low) / (recent_high - recent_low) * 100 if recent_high != recent_low else 50
    
    return {
        'trend_direction': trend_direction,
        'atr_pct': atr_pct,
        'volume_ratio': volume_ratio,
        'range_location': range_pct,
        'recent_high': recent_high,
        'recent_low': recent_low,
        'sma10': sma10,
        'sma20': sma20
    }

def categorize_loss_reason(trade, market_conditions):
    """Categorize the reason for loss"""
    reasons = []
    
    if not market_conditions:
        return ['DATA_UNAVAILABLE']
    
    # Check if stopped out quickly
    if trade['duration'] < 4:
        reasons.append('IMMEDIATE_STOP')
    
    # Check trend alignment
    if market_conditions['trend_direction'] == 'DOWN':
        reasons.append('COUNTER_TREND_ENTRY')
    elif market_conditions['trend_direction'] == 'CHOPPY':
        reasons.append('CHOPPY_MARKET')
    
    # Check volatility
    if market_conditions['atr_pct'] > 2.0:
        reasons.append('HIGH_VOLATILITY')
    elif market_conditions['atr_pct'] < 0.5:
        reasons.append('LOW_VOLATILITY')
    
    # Check volume
    if market_conditions['volume_ratio'] < 0.7:
        reasons.append('LOW_VOLUME')
    
    # Check entry location
    if market_conditions['range_location'] > 70:
        reasons.append('LATE_ENTRY_HIGH')
    elif market_conditions['range_location'] < 30:
        reasons.append('EARLY_ENTRY_LOW')
    
    # Check if stop was too tight
    stop_distance = abs(trade['entry_price'] - trade['stop_loss']) / trade['entry_price'] * 100
    if stop_distance < 0.5:
        reasons.append('STOP_TOO_TIGHT')
    elif stop_distance > 3.0:
        reasons.append('STOP_TOO_WIDE')
    
    # Duration analysis
    if trade['duration'] > 20:
        reasons.append('TIME_DECAY')
    
    return reasons if reasons else ['UNKNOWN']

def analyze_symbol(symbol):
    """Analyze all losing trades for a symbol"""
    print(f"\n{'='*90}")
    print(f"🔍 FORENSICS: {symbol} Losing Trades Analysis")
    print(f"{'='*90}")
    
    trades = load_trade_history(symbol)
    if not trades:
        print(f"No losing trades found for {symbol}")
        return None
    
    ohlcv_1h = load_ohlcv(symbol, '1h')
    ohlcv_1d = load_ohlcv(symbol, '1d')
    indicators = load_indicators(symbol)
    
    # Analyze each trade
    analyzed_trades = []
    for trade in trades:
        market_conditions = analyze_market_conditions_at_entry(trade, ohlcv_1h, indicators)
        loss_reasons = categorize_loss_reason(trade, market_conditions)
        
        analyzed_trades.append({
            **trade,
            'market_conditions': market_conditions,
            'loss_reasons': loss_reasons
        })
    
    # Summary statistics
    total_loss = sum(t['net_pnl'] for t in analyzed_trades)
    avg_loss = total_loss / len(analyzed_trades)
    
    # Reason frequency
    reason_counts = defaultdict(int)
    for t in analyzed_trades:
        for reason in t['loss_reasons']:
            reason_counts[reason] += 1
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total Losing Trades: {len(analyzed_trades)}")
    print(f"  Total Loss: ${total_loss:.2f}")
    print(f"  Average Loss per Trade: ${avg_loss:.2f}")
    print(f"  Largest Single Loss: ${min(t['net_pnl'] for t in analyzed_trades):.2f}")
    
    print(f"\n🔴 PRIMARY LOSS REASONS:")
    for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(analyzed_trades) * 100
        print(f"  {reason}: {count} trades ({pct:.1f}%)")
    
    print(f"\n📋 DETAILED TRADE ANALYSIS:")
    print(f"{'Trade':<6} {'Date':<12} {'Entry':<10} {'Exit':<10} {'Loss':<10} {'Duration':<10} {'Primary Reason':<25}")
    print(f"-"*90)
    
    for t in analyzed_trades[:10]:  # Show first 10
        date = t['entry_time'][:10]
        primary_reason = t['loss_reasons'][0] if t['loss_reasons'] else 'UNKNOWN'
        print(f"{t['trade_id']:<6} {date:<12} ${t['entry_price']:<9.0f} ${t['exit_price']:<9.0f} "
              f"${t['net_pnl']:<9.2f} {t['duration']:<9.1f}h {primary_reason:<25}")
    
    if len(analyzed_trades) > 10:
        print(f"... and {len(analyzed_trades) - 10} more trades")
    
    # Root cause analysis
    print(f"\n🔬 ROOT CAUSE ANALYSIS:")
    
    # Find dominant patterns
    dominant_reasons = [r for r, c in reason_counts.items() if c >= len(analyzed_trades) * 0.2]
    
    if dominant_reasons:
        print(f"  Dominant failure patterns (>20% of losses):")
        for reason in dominant_reasons:
            print(f"    • {reason}")
    
    # Specific recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if 'COUNTER_TREND_ENTRY' in reason_counts and reason_counts['COUNTER_TREND_ENTRY'] > 3:
        print(f"  1. ADD TREND FILTER: Too many counter-trend entries")
        print(f"     → Only enter when price > EMA 20 on daily timeframe")
    
    if 'CHOPPY_MARKET' in reason_counts and reason_counts['CHOPPY_MARKET'] > 3:
        print(f"  2. ADD CHOP FILTER: Trading in sideways markets")
        print(f"     → Only trade when ADX > 25 (trending market)")
    
    if 'IMMEDIATE_STOP' in reason_counts and reason_counts['IMMEDIATE_STOP'] > 3:
        print(f"  3. WIDEN STOPS: Too many immediate stop-outs")
        print(f"     → Increase ATR multiplier from current to next level")
    
    if 'HIGH_VOLATILITY' in reason_counts and reason_counts['HIGH_VOLATILITY'] > 3:
        print(f"  4. VOLATILITY FILTER: Trading during high volatility")
        print(f"     → Skip trades when ATR% > 2.5%")
    
    if 'LATE_ENTRY_HIGH' in reason_counts and reason_counts['LATE_ENTRY_HIGH'] > 3:
        print(f"  5. ENTRY TIMING: Entering too late in move")
        print(f"     → Wait for pullback to 0.618 fib instead of 0.382")
    
    if 'LOW_VOLUME' in reason_counts and reason_counts['LOW_VOLUME'] > 3:
        print(f"  6. VOLUME FILTER: Trading on low volume")
        print(f"     → Require volume > 1.2x average")
    
    if 'TIME_DECAY' in reason_counts and reason_counts['TIME_DECAY'] > 3:
        print(f"  7. TIME STOPS: Trades held too long")
        print(f"     → Reduce max hold time from 24h to 12h")
    
    return {
        'symbol': symbol,
        'total_losing_trades': len(analyzed_trades),
        'total_loss': total_loss,
        'avg_loss': avg_loss,
        'reason_counts': dict(reason_counts),
        'trades': analyzed_trades
    }


def generate_comprehensive_report():
    """Generate comprehensive forensics report for all symbols"""
    print("="*90)
    print("🔬 COMPREHENSIVE TRADE FORENSICS REPORT")
    print("Analysis of All Losing Trades by Currency Pair")
    print("="*90)
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT']
    all_results = {}
    
    for symbol in symbols:
        result = analyze_symbol(symbol)
        if result:
            all_results[symbol] = result
    
    # Cross-currency analysis
    print(f"\n\n{'='*90}")
    print("📊 CROSS-CURRENCY PATTERN ANALYSIS")
    print(f"{'='*90}")
    
    # Aggregate all loss reasons
    all_reasons = defaultdict(lambda: {'count': 0, 'symbols': []})
    for symbol, result in all_results.items():
        for reason, count in result['reason_counts'].items():
            all_reasons[reason]['count'] += count
            all_reasons[reason]['symbols'].append(symbol)
    
    print(f"\n🔴 GLOBAL LOSS PATTERNS (All Currencies Combined):")
    for reason, data in sorted(all_reasons.items(), key=lambda x: x[1]['count'], reverse=True):
        print(f"  {reason}: {data['count']} trades across {', '.join(data['symbols'])}")
    
    # Currency-specific insights
    print(f"\n📈 CURRENCY-SPECIFIC INSIGHTS:")
    
    for symbol, result in all_results.items():
        print(f"\n  {symbol}:")
        print(f"    • Total Loss: ${result['total_loss']:.2f}")
        print(f"    • Avg Loss: ${result['avg_loss']:.2f}")
        
        # Top 2 reasons
        top_reasons = sorted(result['reason_counts'].items(), key=lambda x: x[1], reverse=True)[:2]
        print(f"    • Top Issues: {', '.join([r[0] for r in top_reasons])}")
    
    # Save to file
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIR / 'trade_forensics_report.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n💾 Full report saved to: {RESULTS_DIR / 'trade_forensics_report.json'}")


if __name__ == '__main__':
    generate_comprehensive_report()
