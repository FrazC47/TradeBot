#!/usr/bin/env python3
"""
Missed Opportunity Analysis
Identifying setups that were filtered out but turned out profitable
"""

import csv
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
INDICATORS_DIR = Path('/root/.openclaw/workspace/data/indicators')

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

def check_strategy_filters(symbol, data_1h, data_1d, index):
    """
    Check which filters would have blocked a trade
    Returns dict of filter results
    """
    if index < 50:
        return None
    
    context = data_1h[index-50:index]
    current = data_1h[index]
    prices = [c['close'] for c in context]
    highs = [c['high'] for c in context]
    lows = [c['low'] for c in context]
    volumes = [c['volume'] for c in context]
    
    # Calculate indicators
    ema9 = calculate_ema(prices[-20:], 9)
    ema21 = calculate_ema(prices[-30:], 21)
    atr = calculate_atr(context[-20:])
    atr_pct = (atr / current['close']) * 100
    
    # Volume
    avg_volume = sum(volumes[-20:]) / 20
    volume_ratio = current['volume'] / avg_volume if avg_volume > 0 else 1
    
    # Range location
    recent_high = max(highs[-30:])
    recent_low = min(lows[-30:])
    range_pct = (current['close'] - recent_low) / (recent_high - recent_low) * 100 if recent_high != recent_low else 50
    
    # Check consecutive bullish
    bullish_count = 0
    for i in range(-1, -6, -1):
        if prices[i] > prices[i-1]:
            bullish_count += 1
        else:
            break
    
    # Check breakout
    recent_resistance = max(highs[-10:-1])
    broke_resistance = current['close'] > recent_resistance
    
    # Daily trend (if available)
    daily_trend_bullish = None
    if data_1d and len(data_1d) > 20:
        daily_idx = index // 24
        if daily_idx > 20:
            daily_prices = [d['close'] for d in data_1d[daily_idx-20:daily_idx]]
            daily_ema20 = calculate_ema(daily_prices, 20)
            daily_trend_bullish = daily_prices[-1] > daily_ema20
    
    # Strategy-specific filters
    filters = {
        'symbol': symbol,
        'timestamp': current['timestamp'],
        'datetime': current['datetime'],
        'price': current['close'],
        'ema9': ema9,
        'ema21': ema21,
        'ema_aligned': current['close'] > ema9 > ema21,
        'atr_pct': atr_pct,
        'volume_ratio': volume_ratio,
        'range_pct': range_pct,
        'consecutive_bullish': bullish_count,
        'broke_resistance': broke_resistance,
        'daily_trend_bullish': daily_trend_bullish,
    }
    
    # ETH Strategy Filters
    filters['eth_passed'] = (
        filters['ema_aligned'] and
        bullish_count >= 2 and
        broke_resistance and
        volume_ratio >= 0.8 and
        atr_pct < 4.0
    )
    
    filters['eth_failed_reasons'] = []
    if not filters['ema_aligned']:
        filters['eth_failed_reasons'].append('EMA_NOT_ALIGNED')
    if bullish_count < 2:
        filters['eth_failed_reasons'].append('INSUFFICIENT_BULLISH_CANDLES')
    if not broke_resistance:
        filters['eth_failed_reasons'].append('NO_BREAKOUT')
    if volume_ratio < 0.8:
        filters['eth_failed_reasons'].append('LOW_VOLUME')
    if atr_pct >= 4.0:
        filters['eth_failed_reasons'].append('HIGH_VOLATILITY')
    
    # BTC Strategy Filters
    if data_1d:
        swing_high = max(highs[-30:])
        swing_low = min(lows[-30:])
        diff = swing_high - swing_low
        fib_618 = swing_high - diff * 0.618
        fib_50 = swing_high - diff * 0.5
        in_fib_zone = fib_618 * 0.99 <= current['close'] <= fib_50 * 1.01
    else:
        in_fib_zone = False
    
    filters['btc_passed'] = (
        in_fib_zone and
        daily_trend_bullish and
        atr_pct < 3.0
    )
    
    filters['btc_failed_reasons'] = []
    if not in_fib_zone:
        filters['btc_failed_reasons'].append('NOT_IN_FIB_ZONE')
    if not daily_trend_bullish:
        filters['btc_failed_reasons'].append('DAILY_TREND_BEARISH')
    if atr_pct >= 3.0:
        filters['btc_failed_reasons'].append('HIGH_VOLATILITY')
    
    return filters

def find_missed_opportunities(symbol, data_1h, data_1d, min_profit_pct=2.0):
    """
    Find setups that were filtered out but would have been profitable
    """
    missed = []
    
    for i in range(50, len(data_1h) - 24):
        filters = check_strategy_filters(symbol, data_1h, data_1d, i)
        if not filters:
            continue
        
        # Check if trade was filtered out
        if filters['eth_passed'] or filters['btc_passed']:
            continue  # Trade would have been taken
        
        # Simulate what would have happened if we took the trade
        entry_price = filters['price']
        
        # Look ahead 24 hours for outcome
        future_data = data_1h[i:i+24]
        if not future_data:
            continue
        
        # Find max profit potential
        max_price = max(c['high'] for c in future_data)
        min_price = min(c['low'] for c in future_data)
        
        # Calculate potential profit/loss with typical stop/target
        atr = filters['atr_pct']
        stop_price = entry_price * (1 - atr * 3 / 100)  # 3x ATR stop
        target_price = entry_price * (1 + atr * 6 / 100)  # 6x ATR target
        
        # Check if stop or target hit first
        stop_hit = min_price <= stop_price
        target_hit = max_price >= target_price
        
        # Calculate outcome
        if target_hit and not stop_hit:
            outcome = 'PROFIT'
            profit_pct = (target_price - entry_price) / entry_price * 100
        elif stop_hit and not target_hit:
            outcome = 'LOSS'
            profit_pct = (stop_price - entry_price) / entry_price * 100
        elif target_hit and stop_hit:
            # Determine which hit first (simplified)
            outcome = 'UNCERTAIN'
            profit_pct = 0
        else:
            # Neither hit - close at end
            close_price = future_data[-1]['close']
            profit_pct = (close_price - entry_price) / entry_price * 100
            outcome = 'PROFIT' if profit_pct >= min_profit_pct else 'SMALL_GAIN' if profit_pct > 0 else 'LOSS'
        
        # Only record if it would have been profitable
        if outcome in ['PROFIT', 'SMALL_GAIN'] and profit_pct >= 1.0:
            missed.append({
                'symbol': symbol,
                'datetime': filters['datetime'],
                'price': entry_price,
                'outcome': outcome,
                'profit_pct': profit_pct,
                'eth_failed': not filters['eth_passed'],
                'eth_reasons': filters['eth_failed_reasons'],
                'btc_failed': not filters['btc_passed'],
                'btc_reasons': filters['btc_failed_reasons'],
                'filters': filters
            })
    
    return missed

def analyze_missed_opportunities():
    """Main analysis function"""
    print("="*100)
    print("MISSED OPPORTUNITY ANALYSIS")
    print("Setups Filtered Out That Would Have Been Profitable")
    print("="*100)
    
    symbols = ['ETHUSDT', 'BTCUSDT', 'SOLUSDT']
    all_missed = []
    
    for symbol in symbols:
        print(f"\n🔍 Analyzing {symbol}...")
        
        data_1h = load_ohlcv(symbol, '1h')
        data_1d = load_ohlcv(symbol, '1d') if symbol in ['BTCUSDT', 'BNBUSDT'] else []
        
        if not data_1h:
            print(f"  No data available")
            continue
        
        missed = find_missed_opportunities(symbol, data_1h, data_1d)
        all_missed.extend(missed)
        
        print(f"  Found {len(missed)} missed opportunities")
        
        if missed:
            # Analyze why they were missed
            eth_reasons = defaultdict(int)
            btc_reasons = defaultdict(int)
            
            for m in missed:
                for reason in m['eth_reasons']:
                    eth_reasons[reason] += 1
                for reason in m['btc_reasons']:
                    btc_reasons[reason] += 1
            
            print(f"\n  Top reasons ETH strategy filtered out profitable setups:")
            for reason, count in sorted(eth_reasons.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"    • {reason}: {count} times")
            
            if btc_reasons:
                print(f"\n  Top reasons BTC strategy filtered out profitable setups:")
                for reason, count in sorted(btc_reasons.items(), key=lambda x: x[1], reverse=True)[:3]:
                    print(f"    • {reason}: {count} times")
    
    # Overall summary
    print(f"\n\n{'='*100}")
    print("SUMMARY: ALL MISSED OPPORTUNITIES")
    print(f"{'='*100}")
    
    if not all_missed:
        print("\nNo significant missed opportunities found.")
        print("Current filters are well-calibrated.")
        return
    
    total_missed_profit = sum(m['profit_pct'] for m in all_missed)
    avg_missed_profit = total_missed_profit / len(all_missed)
    
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"  Total Missed Opportunities: {len(all_missed)}")
    print(f"  Total Missed Profit: {total_missed_profit:.2f}%")
    print(f"  Average Missed Profit: {avg_missed_profit:.2f}% per trade")
    print(f"  Largest Missed Profit: {max(m['profit_pct'] for m in all_missed):.2f}%")
    
    # Group by symbol
    by_symbol = defaultdict(list)
    for m in all_missed:
        by_symbol[m['symbol']].append(m)
    
    print(f"\n📈 BY SYMBOL:")
    for symbol, trades in by_symbol.items():
        total = sum(t['profit_pct'] for t in trades)
        print(f"  {symbol}: {len(trades)} trades, {total:.2f}% total missed profit")
    
    # Show examples
    print(f"\n💡 EXAMPLES OF MISSED OPPORTUNITIES:")
    
    # Sort by profit and show top 5
    top_missed = sorted(all_missed, key=lambda x: x['profit_pct'], reverse=True)[:5]
    
    for i, m in enumerate(top_missed, 1):
        print(f"\n  #{i}: {m['symbol']} @ {m['datetime'].strftime('%Y-%m-%d %H:%M')}")
        print(f"      Price: ${m['price']:.2f}")
        print(f"      Potential Profit: {m['profit_pct']:.2f}%")
        print(f"      Why Filtered Out:")
        
        if m['eth_failed']:
            for reason in m['eth_reasons']:
                print(f"        • ETH: {reason}")
        if m['btc_failed']:
            for reason in m['btc_reasons']:
                print(f"        • BTC: {reason}")
    
    # Recommendations
    print(f"\n🔧 RECOMMENDATIONS TO CAPTURE MISSED OPPORTUNITIES:")
    
    # Analyze common filter blocks
    all_eth_reasons = defaultdict(int)
    all_btc_reasons = defaultdict(int)
    
    for m in all_missed:
        for reason in m['eth_reasons']:
            all_eth_reasons[reason] += 1
        for reason in m['btc_reasons']:
            all_btc_reasons[reason] += 1
    
    if all_eth_reasons:
        top_eth = max(all_eth_reasons.items(), key=lambda x: x[1])
        if top_eth[0] == 'LOW_VOLUME':
            print(f"  1. RELAX VOLUME FILTER:")
            print(f"     Current: >0.8x average")
            print(f"     Recommended: >0.6x average")
            print(f"     Impact: Would capture {top_eth[1]} missed trades")
        elif top_eth[0] == 'INSUFFICIENT_BULLISH_CANDLES':
            print(f"  1. RELAX MOMENTUM FILTER:")
            print(f"     Current: 2+ consecutive bullish candles")
            print(f"     Recommended: 1+ bullish candle with volume")
            print(f"     Impact: Would capture {top_eth[1]} missed trades")
        elif top_eth[0] == 'NO_BREAKOUT':
            print(f"  1. ADD PULLBACK ENTRY:")
            print(f"     Current: Only enter on breakout")
            print(f"     Recommended: Also enter on pullback to support")
            print(f"     Impact: Would capture {top_eth[1]} missed trades")
    
    if all_btc_reasons:
        top_btc = max(all_btc_reasons.items(), key=lambda x: x[1])
        if top_btc[0] == 'NOT_IN_FIB_ZONE':
            print(f"  2. EXPAND FIB ZONE:")
            print(f"     Current: 0.5-0.618 fib only")
            print(f"     Recommended: Add 0.382 fib level")
            print(f"     Impact: Would capture {top_btc[1]} missed trades")
        elif top_btc[0] == 'DAILY_TREND_BEARISH':
            print(f"  2. RELAX TREND FILTER:")
            print(f"     Current: Daily must be bullish")
            print(f"     Recommended: Allow 4h trend if strong")
            print(f"     Impact: Would capture {top_btc[1]} missed trades")
    
    print(f"\n⚠️  IMPORTANT: Relaxing filters will also capture more LOSING trades.")
    print(f"   Test any changes in backtest before deploying to production.")
    
    # Save to file
    output = []
    for m in all_missed:
        output.append({
            'symbol': m['symbol'],
            'datetime': m['datetime'].strftime('%Y-%m-%d %H:%M'),
            'price': m['price'],
            'profit_pct': m['profit_pct'],
            'eth_failed_reasons': ','.join(m['eth_reasons']),
            'btc_failed_reasons': ','.join(m['btc_reasons'])
        })
    
    import json
    RESULTS_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/backtest_data')
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(RESULTS_DIR / 'MISSED_OPPORTUNITIES.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Full data saved to: {RESULTS_DIR / 'MISSED_OPPORTUNITIES.json'}")

if __name__ == '__main__':
    analyze_missed_opportunities()
