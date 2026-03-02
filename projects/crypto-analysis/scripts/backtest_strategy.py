#!/usr/bin/env python3
"""
Historical Trade Setup Backtest
Identify trade setups in historical data using MTF strategy
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
OUTPUT_DIR = Path('/root/.openclaw/workspace/backtest_results')

SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
TIMEFRAMES = ['1M', '1w', '1d', '4h', '1h', '15m', '5m']


@dataclass
class TradeSetup:
    symbol: str
    entry_time: int
    entry_price: float
    stop_loss: float
    target: float
    direction: str
    entry_tf: str
    confidence: float
    result: Optional[str] = None  # win, loss, open
    exit_price: Optional[float] = None
    exit_time: Optional[int] = None
    pnl_pct: Optional[float] = None


def load_ohlcv_data(symbol: str, interval: str) -> List[Dict]:
    """Load OHLCV data from CSV"""
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


def calculate_ema(prices: List[float], period: int) -> List[Optional[float]]:
    """Calculate EMA"""
    if len(prices) < period:
        return [None] * len(prices)
    
    multiplier = 2 / (period + 1)
    ema = [sum(prices[:period]) / period]
    
    for price in prices[period:]:
        ema.append((price * multiplier) + (ema[-1] * (1 - multiplier)))
    
    return [None] * (period - 1) + ema


def calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
    """Calculate RSI"""
    if len(prices) < period + 1:
        return [None] * len(prices)
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    rsi = [None]
    
    for i in range(period, len(gains)):
        avg_gain = sum(gains[i-period:i]) / period
        avg_loss = sum(losses[i-period:i]) / period
        
        if avg_loss == 0:
            rsi.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi.append(100 - (100 / (1 + rs)))
    
    return [None] * period + rsi[period:]


def calculate_fibonacci_levels(high: float, low: float) -> Dict[str, float]:
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


def analyze_timeframe_at_index(data: List[Dict], idx: int, ema_periods: List[int]) -> Dict:
    """Analyze a timeframe at a specific index"""
    if idx < 50:  # Need enough data
        return {}
    
    closes = [d['close'] for d in data[:idx+1]]
    highs = [d['high'] for d in data[:idx+1]]
    lows = [d['low'] for d in data[:idx+1]]
    
    # Calculate EMAs
    emas = {}
    for period in ema_periods:
        ema = calculate_ema(closes, period)
        emas[f'ema{period}'] = ema[-1] if ema[-1] is not None else closes[-1]
    
    # Calculate RSI
    rsi = calculate_rsi(closes, 14)
    rsi_value = rsi[-1] if rsi[-1] is not None else 50
    
    # Trend determination
    latest_close = closes[-1]
    ema20 = emas.get('ema20') or emas.get('ema21') or emas.get('ema25') or closes[-1]
    ema50 = emas.get('ema50') or closes[-1]
    
    if latest_close > ema20 > ema50:
        trend = 'bullish'
    elif latest_close < ema20 < ema50:
        trend = 'bearish'
    else:
        trend = 'neutral'
    
    # Key levels
    recent_high = max(highs[-20:])
    recent_low = min(lows[-20:])
    fib_levels = calculate_fibonacci_levels(recent_high, recent_low)
    
    return {
        'trend': trend,
        'rsi': rsi_value,
        'close': latest_close,
        'high': recent_high,
        'low': recent_low,
        'fib_levels': fib_levels,
        'emas': emas
    }


def check_fib_proximity(price: float, fib_levels: Dict[str, float], tolerance: float = 0.005) -> Optional[str]:
    """Check if price is near a Fibonacci level"""
    for level_name, level_price in fib_levels.items():
        if abs(price - level_price) / price < tolerance:
            return level_name
    return None


def find_trade_setups_in_history(symbol: str) -> List[TradeSetup]:
    """Find all trade setups in historical data"""
    print(f"\nAnalyzing {symbol}...")
    
    setups = []
    
    # Load all timeframe data
    tf_data = {}
    for tf in TIMEFRAMES:
        data = load_ohlcv_data(symbol, tf)
        if data:
            tf_data[tf] = data
    
    if not tf_data:
        return setups
    
    # Get the timeframe with most data (usually 5m or 1h)
    primary_tf = '1h' if '1h' in tf_data else '5m'
    primary_data = tf_data[primary_tf]
    
    print(f"  Primary timeframe: {primary_tf} with {len(primary_data)} candles")
    
    # Analyze every 4 hours (to avoid overlapping signals)
    step = 48  # 4 hours of 5m candles or 4 candles of 1h
    
    for idx in range(100, len(primary_data), step):
        timestamp = primary_data[idx]['timestamp']
        
        # Analyze higher timeframes
        higher_tf_bias = []
        
        for tf in ['1M', '1w', '1d', '4h']:
            if tf not in tf_data:
                continue
            
            # Find corresponding index in this timeframe
            tf_data_list = tf_data[tf]
            tf_idx = None
            for i, d in enumerate(tf_data_list):
                if d['timestamp'] <= timestamp:
                    tf_idx = i
                else:
                    break
            
            if tf_idx is None or tf_idx < 20:
                continue
            
            ema_periods = [20, 50]
            if tf in ['1M', '1w']:
                ema_periods = [50, 200]
            
            analysis = analyze_timeframe_at_index(tf_data_list, tf_idx, ema_periods)
            if analysis:
                higher_tf_bias.append(analysis['trend'])
        
        # Need at least 2 higher timeframes (was 3)
        if len(higher_tf_bias) < 2:
            continue
        
        # Count bullish/bearish
        bullish_count = higher_tf_bias.count('bullish')
        bearish_count = higher_tf_bias.count('bearish')
        
        if bullish_count >= 2 and bullish_count > bearish_count:  # Was >= 3
            overall_bias = 'bullish'
        elif bearish_count >= 2 and bearish_count > bullish_count:  # Was >= 3
            overall_bias = 'bearish'
        else:
            continue  # No clear bias
        
        # Now check entry timeframe (5m or 15m)
        for entry_tf in ['5m', '15m']:
            if entry_tf not in tf_data:
                continue
            
            # Find index in entry timeframe
            entry_data = tf_data[entry_tf]
            entry_idx = None
            for i, d in enumerate(entry_data):
                if d['timestamp'] <= timestamp:
                    entry_idx = i
                else:
                    break
            
            if entry_idx is None or entry_idx < 20:
                continue
            
            ema_periods = [9, 21]
            if entry_tf == '15m':
                ema_periods = [9, 21, 50]
            
            entry_analysis = analyze_timeframe_at_index(entry_data, entry_idx, ema_periods)
            if not entry_analysis:
                continue
            
            # Check alignment
            if entry_analysis['trend'] != overall_bias:
                continue
            
            # Check RSI (relaxed)
            if overall_bias == 'bullish' and entry_analysis['rsi'] > 70:  # Was 60
                continue
            if overall_bias == 'bearish' and entry_analysis['rsi'] < 30:  # Was 40
                continue
            
            # Check if at Fibonacci level (relaxed tolerance)
            fib_level = check_fib_proximity(entry_analysis['close'], entry_analysis['fib_levels'], tolerance=0.01)  # Was 0.005
            if not fib_level:
                continue
            
            # Good Fib levels for entries (expanded)
            if overall_bias == 'bullish' and fib_level not in ['0.618', '0.5', '0.382', '0.786']:  # Added 0.786
                continue
            if overall_bias == 'bearish' and fib_level not in ['0.382', '0.5', '0.618', '0.236']:  # Added 0.236
                continue
            
            # Calculate stop and target
            entry_price = entry_analysis['close']
            atr = (entry_analysis['high'] - entry_analysis['low']) * 0.1  # Simplified ATR
            
            if overall_bias == 'bullish':
                stop_loss = entry_price - (atr * 2)
                target = entry_price + (atr * 3)
            else:
                stop_loss = entry_price + (atr * 2)
                target = entry_price - (atr * 3)
            
            # Calculate confidence
            aligned_count = sum(1 for t in higher_tf_bias if t == overall_bias)
            confidence = (aligned_count / len(higher_tf_bias)) * 100
            
            setup = TradeSetup(
                symbol=symbol,
                entry_time=timestamp,
                entry_price=round(entry_price, 2),
                stop_loss=round(stop_loss, 2),
                target=round(target, 2),
                direction=overall_bias,
                entry_tf=entry_tf,
                confidence=round(confidence, 1)
            )
            
            setups.append(setup)
            break  # Only one setup per time window
    
    return setups


def calculate_setup_result(setup: TradeSetup, data: List[Dict]) -> TradeSetup:
    """Calculate what happened to a setup"""
    # Find entry index
    entry_idx = None
    for i, d in enumerate(data):
        if d['timestamp'] >= setup.entry_time:
            entry_idx = i
            break
    
    if entry_idx is None:
        setup.result = 'open'
        return setup
    
    # Check next 100 candles (about 8 hours for 5m, 4 days for 1h)
    for i in range(entry_idx, min(entry_idx + 100, len(data))):
        candle = data[i]
        
        if setup.direction == 'bullish':
            # Check if stop hit
            if candle['low'] <= setup.stop_loss:
                setup.result = 'loss'
                setup.exit_price = setup.stop_loss
                setup.exit_time = candle['timestamp']
                setup.pnl_pct = round((setup.stop_loss - setup.entry_price) / setup.entry_price * 100, 2)
                return setup
            
            # Check if target hit
            if candle['high'] >= setup.target:
                setup.result = 'win'
                setup.exit_price = setup.target
                setup.exit_time = candle['timestamp']
                setup.pnl_pct = round((setup.target - setup.entry_price) / setup.entry_price * 100, 2)
                return setup
        
        else:  # bearish
            # Check if stop hit
            if candle['high'] >= setup.stop_loss:
                setup.result = 'loss'
                setup.exit_price = setup.stop_loss
                setup.exit_time = candle['timestamp']
                setup.pnl_pct = round((setup.entry_price - setup.stop_loss) / setup.entry_price * 100, 2)
                return setup
            
            # Check if target hit
            if candle['low'] <= setup.target:
                setup.result = 'win'
                setup.exit_price = setup.target
                setup.exit_time = candle['timestamp']
                setup.pnl_pct = round((setup.entry_price - setup.target) / setup.entry_price * 100, 2)
                return setup
    
    # Still open
    setup.result = 'open'
    return setup


def main():
    """Run backtest on all symbols"""
    print("=" * 70)
    print("HISTORICAL TRADE SETUP BACKTEST")
    print("=" * 70)
    
    all_setups = []
    
    for symbol in SYMBOLS:
        setups = find_trade_setups_in_history(symbol)
        
        # Calculate results
        data = load_ohlcv_data(symbol, '5m')
        if not data:
            data = load_ohlcv_data(symbol, '1h')
        
        for setup in setups:
            calculate_setup_result(setup, data)
        
        all_setups.extend(setups)
        
        print(f"  Found {len(setups)} setups")
    
    # Statistics
    print("\n" + "=" * 70)
    print("BACKTEST RESULTS")
    print("=" * 70)
    
    print(f"\nTotal setups found: {len(all_setups)}")
    
    if not all_setups:
        print("No setups found with current strategy parameters.")
        return
    
    wins = sum(1 for s in all_setups if s.result == 'win')
    losses = sum(1 for s in all_setups if s.result == 'loss')
    open_trades = sum(1 for s in all_setups if s.result == 'open')
    
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")
    print(f"Open: {open_trades}")
    
    if wins + losses > 0:
        win_rate = (wins / (wins + losses)) * 100
        print(f"Win rate: {win_rate:.1f}%")
        
        avg_win = sum(s.pnl_pct for s in all_setups if s.result == 'win') / wins if wins > 0 else 0
        avg_loss = sum(s.pnl_pct for s in all_setups if s.result == 'loss') / losses if losses > 0 else 0
        
        print(f"Average win: {avg_win:.2f}%")
        print(f"Average loss: {avg_loss:.2f}%")
        
        total_pnl = sum(s.pnl_pct for s in all_setups if s.pnl_pct is not None)
        print(f"Total P&L: {total_pnl:.2f}%")
    
    # Show recent setups
    print("\n" + "=" * 70)
    print("RECENT SETUPS (Last 10)")
    print("=" * 70)
    
    for setup in sorted(all_setups, key=lambda x: x.entry_time, reverse=True)[:10]:
        date = datetime.fromtimestamp(setup.entry_time / 1000).strftime('%Y-%m-%d %H:%M')
        result_icon = "✅" if setup.result == 'win' else "❌" if setup.result == 'loss' else "⏳"
        print(f"\n{result_icon} {setup.symbol} {setup.direction.upper()}")
        print(f"   Date: {date}")
        print(f"   Entry: ${setup.entry_price} on {setup.entry_tf}")
        print(f"   Stop: ${setup.stop_loss} | Target: ${setup.target}")
        print(f"   Confidence: {setup.confidence}%")
        if setup.pnl_pct:
            print(f"   P&L: {setup.pnl_pct:+.2f}%")
    
    # Save results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f'backtest_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
    
    with open(output_file, 'w') as f:
        json.dump([{
            'symbol': s.symbol,
            'entry_time': s.entry_time,
            'entry_price': s.entry_price,
            'stop_loss': s.stop_loss,
            'target': s.target,
            'direction': s.direction,
            'entry_tf': s.entry_tf,
            'confidence': s.confidence,
            'result': s.result,
            'pnl_pct': s.pnl_pct
        } for s in all_setups], f, indent=2)
    
    print(f"\nSaved to: {output_file}")


if __name__ == '__main__':
    main()
