#!/usr/bin/env python3
"""
Multi-Timeframe Context Analyzer
Analyzes timeframes from highest to lowest, carrying context down
Never analyzes a timeframe in isolation
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
FUTURES_DATA_DIR = Path('/root/.openclaw/workspace/data/binance_futures')
DIVERGENCE_DIR = Path('/root/.openclaw/workspace/data/divergence_alerts')
OUTPUT_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/mtf')

# Timeframe hierarchy (highest to lowest)
TIMEFRAME_HIERARCHY = ['1M', '1w', '1d', '4h', '1h', '15m', '5m']


@dataclass
class TimeframeContext:
    """Context from a higher timeframe analysis"""
    timeframe: str
    trend: str  # bullish, bearish, neutral
    trend_strength: float  # 0-100
    key_level_high: Optional[float] = None
    key_level_low: Optional[float] = None
    fib_levels: Dict[str, float] = field(default_factory=dict)
    pattern_at_key_level: Optional[str] = None
    rsi_value: Optional[float] = None
    macd_signal: Optional[str] = None  # bullish, bearish, neutral
    divergence_signal: Optional[str] = None
    
    def is_bullish(self) -> bool:
        return self.trend == 'bullish'
    
    def is_bearish(self) -> bool:
        return self.trend == 'bearish'
    
    def get_dominant_direction(self) -> str:
        """Get the dominant direction considering all factors"""
        bullish_count = 0
        bearish_count = 0
        
        if self.trend == 'bullish':
            bullish_count += 2
        elif self.trend == 'bearish':
            bearish_count += 2
            
        if self.macd_signal == 'bullish':
            bullish_count += 1
        elif self.macd_signal == 'bearish':
            bearish_count += 1
            
        if self.rsi_value and self.rsi_value > 50:
            bullish_count += 0.5
        elif self.rsi_value and self.rsi_value < 50:
            bearish_count += 0.5
            
        if self.divergence_signal == 'bullish':
            bullish_count += 1.5
        elif self.divergence_signal == 'bearish':
            bearish_count += 1.5
        
        if bullish_count > bearish_count:
            return 'bullish'
        elif bearish_count > bullish_count:
            return 'bearish'
        return 'neutral'


@dataclass
class MTFAnalysisResult:
    """Complete multi-timeframe analysis for a symbol"""
    symbol: str
    timestamp: str
    overall_bias: str
    confidence: float
    timeframe_analysis: Dict[str, Dict[str, Any]]
    higher_timeframe_context: Dict[str, TimeframeContext]
    trade_setup: Optional[Dict[str, Any]] = None


def load_ohlcv_data(symbol: str, interval: str) -> List[Dict]:
    """Load OHLCV data from CSV"""
    import csv
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


def calculate_basic_indicators(data: List[Dict]) -> Dict[str, Any]:
    """Calculate basic indicators for a timeframe"""
    if not data or len(data) < 20:
        return {}
    
    closes = [d['close'] for d in data]
    highs = [d['high'] for d in data]
    lows = [d['low'] for d in data]
    
    # EMA 20
    ema20 = calculate_ema(closes, 20)
    
    # EMA 50
    ema50 = calculate_ema(closes, 50) if len(closes) >= 50 else [None] * len(closes)
    
    # RSI
    rsi = calculate_rsi(closes, 14)
    
    # Trend determination
    latest_close = closes[-1]
    latest_ema20 = ema20[-1] if ema20[-1] is not None else latest_close
    latest_ema50 = ema50[-1] if ema50 and ema50[-1] is not None else latest_close
    
    if latest_close > latest_ema20 > latest_ema50:
        trend = 'bullish'
        trend_strength = min(100, (latest_close / latest_ema50 - 1) * 1000)
    elif latest_close < latest_ema20 < latest_ema50:
        trend = 'bearish'
        trend_strength = min(100, (latest_ema50 / latest_close - 1) * 1000)
    else:
        trend = 'neutral'
        trend_strength = 50
    
    # Key levels (recent high/low)
    recent_high = max(highs[-20:])
    recent_low = min(lows[-20:])
    
    # Fibonacci levels
    fib_levels = calculate_fibonacci_levels(recent_high, recent_low)
    
    return {
        'trend': trend,
        'trend_strength': trend_strength,
        'ema20': ema20[-1],
        'ema50': ema50[-1] if ema50 else None,
        'rsi': rsi[-1] if rsi else 50,
        'key_level_high': recent_high,
        'key_level_low': recent_low,
        'fib_levels': fib_levels,
        'latest_close': latest_close
    }


def calculate_ema(prices: List[float], period: int) -> List[Optional[float]]:
    """Calculate EMA"""
    if len(prices) < period:
        return [None] * len(prices)
    
    multiplier = 2 / (period + 1)
    ema = [sum(prices[:period]) / period]
    
    for price in prices[period:]:
        ema.append((price * multiplier) + (ema[-1] * (1 - multiplier)))
    
    # Pad with None for initial period
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


def load_divergence_signals(symbol: str, interval: str) -> Optional[str]:
    """Load divergence signals if available"""
    signals_file = DIVERGENCE_DIR / 'latest_signals.json'
    
    if not signals_file.exists():
        return None
    
    try:
        with open(signals_file, 'r') as f:
            signals = json.load(f)
        
        for signal in signals:
            if signal.get('symbol') == symbol and signal.get('interval') == interval:
                if 'FUTURES_PREMIUM' in signal.get('type', ''):
                    return 'bullish'
                elif 'FUTURES_DISCOUNT' in signal.get('type', ''):
                    return 'bearish'
    except:
        pass
    
    return None


def analyze_timeframe_with_context(
    symbol: str,
    interval: str,
    higher_tf_context: Optional[TimeframeContext]
) -> tuple[Dict[str, Any], TimeframeContext]:
    """Analyze a timeframe considering higher timeframe context"""
    
    data = load_ohlcv_data(symbol, interval)
    if not data:
        return {}, TimeframeContext(interval, 'neutral', 0)
    
    indicators = calculate_basic_indicators(data)
    if not indicators:
        return {}, TimeframeContext(interval, 'neutral', 0)
    
    # Get divergence signal
    divergence = load_divergence_signals(symbol, interval)
    
    # Create context for this timeframe
    context = TimeframeContext(
        timeframe=interval,
        trend=indicators['trend'],
        trend_strength=indicators['trend_strength'],
        key_level_high=indicators['key_level_high'],
        key_level_low=indicators['key_level_low'],
        fib_levels=indicators['fib_levels'],
        rsi_value=indicators['rsi'],
        divergence_signal=divergence
    )
    
    # Analysis result with higher timeframe context
    analysis = {
        'interval': interval,
        'trend': indicators['trend'],
        'trend_strength': indicators['trend_strength'],
        'rsi': indicators['rsi'],
        'ema20': indicators['ema20'],
        'ema50': indicators['ema50'],
        'key_levels': {
            'high': indicators['key_level_high'],
            'low': indicators['key_level_low']
        },
        'fib_levels': indicators['fib_levels'],
        'latest_close': indicators['latest_close'],
        'higher_tf_bias': higher_tf_context.get_dominant_direction() if higher_tf_context else 'unknown',
        'alignment_with_higher_tf': 'aligned' if higher_tf_context and indicators['trend'] == higher_tf_context.get_dominant_direction() else 'misaligned'
    }
    
    # If we have higher timeframe context, adjust the analysis
    if higher_tf_context:
        # Check if price is near higher timeframe key levels
        price = indicators['latest_close']
        higher_high = higher_tf_context.key_level_high
        higher_low = higher_tf_context.key_level_low
        
        if higher_high and higher_low:
            # Check if price is within 2% of higher TF levels
            if abs(price - higher_high) / price < 0.02:
                analysis['near_higher_tf_level'] = 'high'
                analysis['higher_tf_level_value'] = higher_high
            elif abs(price - higher_low) / price < 0.02:
                analysis['near_higher_tf_level'] = 'low'
                analysis['higher_tf_level_value'] = higher_low
            else:
                analysis['near_higher_tf_level'] = 'none'
        
        # Check alignment with higher timeframe Fibonacci
        if higher_tf_context.fib_levels:
            for level_name, level_price in higher_tf_context.fib_levels.items():
                if abs(price - level_price) / price < 0.01:
                    analysis['at_higher_tf_fib'] = level_name
                    analysis['higher_tf_fib_price'] = level_price
                    break
        
        # Adjust trend strength based on alignment
        if analysis['alignment_with_higher_tf'] == 'aligned':
            analysis['trend_strength'] *= 1.3  # Boost by 30%
            analysis['confidence'] = 'high'
        else:
            analysis['trend_strength'] *= 0.7  # Reduce by 30%
            analysis['confidence'] = 'low'
    
    return analysis, context


def generate_trade_setup(
    symbol: str,
    timeframe_analysis: Dict[str, Dict[str, Any]],
    context_chain: Dict[str, TimeframeContext]
) -> Optional[Dict[str, Any]]:
    """Generate trade setup based on multi-timeframe analysis"""
    
    # Get overall bias from monthly to 4h
    higher_tf_bias = []
    for tf in ['1M', '1w', '1d', '4h']:
        if tf in context_chain:
            higher_tf_bias.append(context_chain[tf].get_dominant_direction())
    
    if not higher_tf_bias:
        return None
    
    # Count bullish vs bearish
    bullish_count = higher_tf_bias.count('bullish')
    bearish_count = higher_tf_bias.count('bearish')
    
    if bullish_count > bearish_count:
        overall_bias = 'bullish'
    elif bearish_count > bullish_count:
        overall_bias = 'bearish'
    else:
        return None  # No clear bias
    
    # Look for entry on lower timeframes
    entry_tf = None
    entry_price = None
    stop_loss = None
    target = None
    
    for tf in ['1h', '15m', '5m']:  # Include 5m for precise entries
        if tf not in timeframe_analysis:
            continue
        
        tf_data = timeframe_analysis[tf]
        
        # For bullish bias, look for pullback to support
        if overall_bias == 'bullish':
            if tf_data.get('near_higher_tf_level') == 'low' or tf_data.get('at_higher_tf_fib') in ['0.618', '0.5']:
                if tf_data['rsi'] and tf_data['rsi'] < 50:
                    entry_tf = tf
                    entry_price = tf_data['latest_close']
                    stop_loss = tf_data['key_levels']['low'] * 0.995
                    target = context_chain.get('1d', TimeframeContext('1d', 'neutral', 0)).key_level_high
                    break
        
        # For bearish bias, look for rejection at resistance
        elif overall_bias == 'bearish':
            if tf_data.get('near_higher_tf_level') == 'high' or tf_data.get('at_higher_tf_fib') in ['0.382', '0.5']:
                if tf_data['rsi'] and tf_data['rsi'] > 50:
                    entry_tf = tf
                    entry_price = tf_data['latest_close']
                    stop_loss = tf_data['key_levels']['high'] * 1.005
                    target = context_chain.get('1d', TimeframeContext('1d', 'neutral', 0)).key_level_low
                    break
    
    if not entry_tf:
        return None
    
    return {
        'direction': overall_bias,
        'entry_timeframe': entry_tf,
        'entry_price': round(entry_price, 2),
        'stop_loss': round(stop_loss, 2),
        'target': round(target, 2),
        'risk_reward': round(abs(target - entry_price) / abs(entry_price - stop_loss), 2) if entry_price != stop_loss else 0
    }


def run_mtf_analysis(symbol: str) -> MTFAnalysisResult:
    """Run complete multi-timeframe analysis for a symbol"""
    
    print(f"\n{'='*70}")
    print(f"Multi-Timeframe Analysis: {symbol}")
    print('='*70)
    
    timeframe_analysis = {}
    context_chain = {}
    higher_context = None
    
    # Analyze from highest to lowest timeframe
    for interval in TIMEFRAME_HIERARCHY:
        print(f"\nAnalyzing {interval}...")
        
        analysis, context = analyze_timeframe_with_context(
            symbol, interval, higher_context
        )
        
        if analysis:
            timeframe_analysis[interval] = analysis
            context_chain[interval] = context
            higher_context = context
            
            print(f"  Trend: {analysis['trend']} (strength: {analysis['trend_strength']:.1f})")
            print(f"  RSI: {analysis['rsi']:.1f}")
            
            if analysis.get('higher_tf_bias') != 'unknown':
                print(f"  Higher TF bias: {analysis['higher_tf_bias']}")
                print(f"  Alignment: {analysis['alignment_with_higher_tf']}")
            
            if analysis.get('near_higher_tf_level') and analysis['near_higher_tf_level'] != 'none':
                print(f"  Near higher TF {analysis['near_higher_tf_level']}: {analysis.get('higher_tf_level_value', 'N/A')}")
            
            if analysis.get('at_higher_tf_fib'):
                print(f"  At higher TF Fib {analysis['at_higher_tf_fib']}: {analysis['higher_tf_fib_price']}")
    
    # Generate trade setup
    trade_setup = generate_trade_setup(symbol, timeframe_analysis, context_chain)
    
    if trade_setup:
        print(f"\n{'='*70}")
        print("TRADE SETUP DETECTED")
        print('='*70)
        print(f"Direction: {trade_setup['direction'].upper()}")
        print(f"Entry: ${trade_setup['entry_price']} on {trade_setup['entry_timeframe']}")
        print(f"Stop: ${trade_setup['stop_loss']}")
        print(f"Target: ${trade_setup['target']}")
        print(f"R:R = 1:{trade_setup['risk_reward']}")
    
    # Determine overall bias
    bullish_count = sum(1 for ctx in context_chain.values() if ctx.is_bullish())
    bearish_count = sum(1 for ctx in context_chain.values() if ctx.is_bearish())
    
    if bullish_count > bearish_count:
        overall_bias = 'bullish'
        confidence = (bullish_count / len(context_chain)) * 100
    elif bearish_count > bullish_count:
        overall_bias = 'bearish'
        confidence = (bearish_count / len(context_chain)) * 100
    else:
        overall_bias = 'neutral'
        confidence = 50
    
    result = MTFAnalysisResult(
        symbol=symbol,
        timestamp=datetime.now().isoformat(),
        overall_bias=overall_bias,
        confidence=confidence,
        timeframe_analysis=timeframe_analysis,
        higher_timeframe_context=context_chain,
        trade_setup=trade_setup
    )
    
    # Save to file
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{symbol}_mtf_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            'symbol': result.symbol,
            'timestamp': result.timestamp,
            'overall_bias': result.overall_bias,
            'confidence': result.confidence,
            'timeframe_analysis': result.timeframe_analysis,
            'trade_setup': result.trade_setup
        }, f, indent=2)
    
    print(f"\nSaved to: {output_file}")
    
    return result


def main():
    """Run MTF analysis for all symbols"""
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    
    for symbol in symbols:
        run_mtf_analysis(symbol)
    
    print(f"\n{'='*70}")
    print("Multi-Timeframe Analysis Complete")
    print('='*70)


if __name__ == '__main__':
    main()
