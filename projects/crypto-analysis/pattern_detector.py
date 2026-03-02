#!/usr/bin/env python3
"""
Candlestick Pattern Detector Module
Detects Japanese candlestick patterns in OHLCV data with strict textbook criteria.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class PatternType(Enum):
    """Classification of pattern sentiment"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class Candle:
    """Represents a single candlestick"""
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    timestamp: int = 0
    
    @property
    def body(self) -> float:
        """Body size (absolute value)"""
        return abs(self.close - self.open)
    
    @property
    def body_pct(self) -> float:
        """Body as percentage of range"""
        range_size = self.range
        if range_size == 0:
            return 0
        return self.body / range_size
    
    @property
    def range(self) -> float:
        """Total range (high - low)"""
        return self.high - self.low
    
    @property
    def upper_wick(self) -> float:
        """Upper wick size"""
        return self.high - max(self.open, self.close)
    
    @property
    def lower_wick(self) -> float:
        """Lower wick size"""
        return min(self.open, self.close) - self.low
    
    @property
    def is_bullish(self) -> bool:
        """True if close > open"""
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        """True if close < open"""
        return self.close < self.open
    
    @property
    def is_doji(self, tolerance: float = 0.001) -> bool:
        """True if open ≈ close within tolerance"""
        if self.range == 0:
            return True
        return self.body / self.range < tolerance


@dataclass
class Pattern:
    """Detected pattern information"""
    name: str
    type: PatternType
    start_idx: int
    end_idx: int
    candles: List[Candle]
    confidence: float = 1.0
    
    @property
    def candle_count(self) -> int:
        return len(self.candles)


class PatternDetector:
    """Detects candlestick patterns in OHLCV data"""
    
    # Detection thresholds (strict mode)
    DOJI_TOLERANCE = 0.001          # 0.1% of range
    WICK_RATIO = 2.0                # Wick must be 2x body
    BODY_PERCENTAGE = 0.5           # 50% for long body
    SMALL_BODY_RATIO = 0.3          # 30% for small body
    ENGULFING_THRESHOLD = 1.0       # Complete engulfing
    GAP_THRESHOLD = 0.001           # 0.1% for gap
    EQUAL_PRICE_TOLERANCE = 0.001   # 0.1% for equal prices
    
    def __init__(self, data: List[Dict]):
        """
        Initialize with OHLCV data
        
        Args:
            data: List of dicts with 'open', 'high', 'low', 'close', 'volume', 'timestamp'
        """
        self.candles = self._convert_to_candles(data)
        self.patterns: List[Pattern] = []
    
    def _convert_to_candles(self, data: List[Dict]) -> List[Candle]:
        """Convert raw data to Candle objects"""
        candles = []
        for d in data:
            try:
                candle = Candle(
                    open=float(d['open']),
                    high=float(d['high']),
                    low=float(d['low']),
                    close=float(d['close']),
                    volume=float(d.get('volume', 0)),
                    timestamp=int(d.get('timestamp', 0))
                )
                candles.append(candle)
            except (ValueError, KeyError):
                continue
        return candles
    
    def _is_doji(self, candle: Candle) -> bool:
        """Check if candle is a doji"""
        if candle.range == 0:
            return True
        return candle.body / candle.range < self.DOJI_TOLERANCE
    
    def _is_long_body(self, candle: Candle) -> bool:
        """Check if candle has a long body"""
        if candle.range == 0:
            return False
        return candle.body / candle.range >= self.BODY_PERCENTAGE
    
    def _is_small_body(self, candle: Candle, reference: Candle) -> bool:
        """Check if candle body is small relative to reference"""
        if reference.body == 0:
            return candle.body < 0.001
        return candle.body / reference.body < self.SMALL_BODY_RATIO
    
    def _has_gap_up(self, prev: Candle, curr: Candle) -> bool:
        """Check for gap up between candles"""
        return curr.low > prev.high * (1 + self.GAP_THRESHOLD)
    
    def _has_gap_down(self, prev: Candle, curr: Candle) -> bool:
        """Check for gap down between candles"""
        return curr.high < prev.low * (1 - self.GAP_THRESHOLD)
    
    def _is_uptrend(self, idx: int, lookback: int = 3) -> bool:
        """Check if we're in an uptrend"""
        if idx < lookback:
            return False
        highs = [self.candles[idx-i].high for i in range(lookback)]
        lows = [self.candles[idx-i].low for i in range(lookback)]
        return all(highs[i] >= highs[i+1] for i in range(len(highs)-1)) and \
               all(lows[i] >= lows[i+1] for i in range(len(lows)-1))
    
    def _is_downtrend(self, idx: int, lookback: int = 3) -> bool:
        """Check if we're in a downtrend"""
        if idx < lookback:
            return False
        highs = [self.candles[idx-i].high for i in range(lookback)]
        lows = [self.candles[idx-i].low for i in range(lookback)]
        return all(highs[i] <= highs[i+1] for i in range(len(highs)-1)) and \
               all(lows[i] <= lows[i+1] for i in range(len(lows)-1))
    
    def detect_all_patterns(self) -> List[Pattern]:
        """Detect HIGH VALUE patterns only"""
        self.patterns = []
        
        for i in range(len(self.candles)):
            # Single candle patterns - HIGH VALUE ONLY
            self._detect_hammer(i)
            self._detect_shooting_star(i)
            
            # Two candle patterns - HIGH VALUE ONLY
            if i >= 1:
                self._detect_engulfing(i)
            
            # Three candle patterns - HIGH VALUE ONLY
            if i >= 2:
                self._detect_morning_star(i)
                self._detect_evening_star(i)
        
        return self.patterns
    
    def detect_all_patterns_with_fibonacci(self, fib_levels: dict = None) -> List[Pattern]:
        """Detect patterns and mark those near Fibonacci levels"""
        patterns = self.detect_all_patterns()
        
        if not fib_levels:
            return patterns
        
        # Mark patterns near Fibonacci levels
        for pattern in patterns:
            pattern.near_fibonacci = False
            pattern.fibonacci_level = None
            
            # Get pattern price (use close of last candle)
            pattern_price = pattern.candles[-1].close
            
            # Check if pattern is within 1% of any Fibonacci level
            for level_name, level_price in fib_levels.items():
                if abs(pattern_price - level_price) / level_price < 0.01:
                    pattern.near_fibonacci = True
                    pattern.fibonacci_level = level_name
                    pattern.confidence *= 1.5  # Boost confidence
                    break
        
        return patterns
    
    # ==================== SINGLE CANDLE PATTERNS ====================
    
    def _detect_doji_patterns(self, idx: int):
        """Detect all doji variants"""
        if idx >= len(self.candles):
            return
        
        candle = self.candles[idx]
        
        if not self._is_doji(candle):
            return
        
        body = candle.body
        upper = candle.upper_wick
        lower = candle.lower_wick
        
        # Check for long-legged doji
        if body > 0:
            if upper / body >= self.WICK_RATIO and lower / body >= self.WICK_RATIO:
                self._add_pattern("Long-Legged Doji", PatternType.NEUTRAL, idx, idx, [candle])
                return
            
            # Dragonfly doji
            if lower / body >= self.WICK_RATIO and upper / candle.range < 0.1:
                self._add_pattern("Dragonfly Doji", PatternType.BULLISH, idx, idx, [candle])
                return
            
            # Gravestone doji
            if upper / body >= self.WICK_RATIO and lower / candle.range < 0.1:
                self._add_pattern("Gravestone Doji", PatternType.BEARISH, idx, idx, [candle])
                return
        
        # Standard doji
        self._add_pattern("Doji", PatternType.NEUTRAL, idx, idx, [candle])
    
    def _detect_hammer(self, idx: int):
        """Detect hammer pattern (bullish reversal at bottom)"""
        if idx >= len(self.candles) or idx < 2:
            return
        
        candle = self.candles[idx]
        
        # Must be at bottom of downtrend
        if not self._is_downtrend(idx):
            return
        
        # Small body at upper end
        if not self._is_long_body(candle):
            return
        
        # Lower wick at least 2x body
        if candle.lower_wick < candle.body * self.WICK_RATIO:
            return
        
        # Little to no upper wick
        if candle.upper_wick > candle.body * 0.1:
            return
        
        # Body in upper third
        upper_third = candle.low + (candle.range * 0.67)
        if min(candle.open, candle.close) < upper_third:
            return
        
        self._add_pattern("Hammer", PatternType.BULLISH, idx, idx, [candle])
    
    def _detect_inverted_hammer(self, idx: int):
        """Detect inverted hammer pattern (bullish reversal at bottom)"""
        if idx >= len(self.candles) or idx < 2:
            return
        
        candle = self.candles[idx]
        
        # Must be at bottom of downtrend
        if not self._is_downtrend(idx):
            return
        
        # Upper wick at least 2x body
        if candle.upper_wick < candle.body * self.WICK_RATIO:
            return
        
        # Little to no lower wick
        if candle.lower_wick > candle.body * 0.1:
            return
        
        # Body in lower third
        lower_third = candle.low + (candle.range * 0.33)
        if max(candle.open, candle.close) > lower_third + candle.body:
            return
        
        self._add_pattern("Inverted Hammer", PatternType.BULLISH, idx, idx, [candle])
    
    def _detect_shooting_star(self, idx: int):
        """Detect shooting star pattern (bearish reversal at top)"""
        if idx >= len(self.candles) or idx < 2:
            return
        
        candle = self.candles[idx]
        
        # Must be at top of uptrend
        if not self._is_uptrend(idx):
            return
        
        # Upper wick at least 2x body
        if candle.upper_wick < candle.body * self.WICK_RATIO:
            return
        
        # Little to no lower wick
        if candle.lower_wick > candle.body * 0.1:
            return
        
        # Body in lower third
        lower_third = candle.low + (candle.range * 0.33)
        if max(candle.open, candle.close) > lower_third + candle.body:
            return
        
        self._add_pattern("Shooting Star", PatternType.BEARISH, idx, idx, [candle])
    
    # ==================== TWO CANDLE PATTERNS ====================
    
    def _detect_engulfing(self, idx: int):
        """Detect bullish and bearish engulfing patterns"""
        prev = self.candles[idx - 1]
        curr = self.candles[idx]
        
        # Bullish engulfing
        if prev.is_bearish and curr.is_bullish:
            if curr.open <= prev.close and curr.close >= prev.open:
                if not self._is_doji(prev):  # First candle shouldn't be doji
                    self._add_pattern("Bullish Engulfing", PatternType.BULLISH, idx-1, idx, [prev, curr])
        
        # Bearish engulfing
        elif prev.is_bullish and curr.is_bearish:
            if curr.open >= prev.close and curr.close <= prev.open:
                if not self._is_doji(prev):
                    self._add_pattern("Bearish Engulfing", PatternType.BEARISH, idx-1, idx, [prev, curr])
    
    def _detect_harami(self, idx: int):
        """Detect bullish and bearish harami patterns"""
        prev = self.candles[idx - 1]
        curr = self.candles[idx]
        
        # Current candle must be inside previous candle's body
        prev_body_top = max(prev.open, prev.close)
        prev_body_bottom = min(prev.open, prev.close)
        
        curr_body_top = max(curr.open, curr.close)
        curr_body_bottom = min(curr.open, curr.close)
        
        if curr_body_top > prev_body_top or curr_body_bottom < prev_body_bottom:
            return
        
        # Current body must be small relative to previous
        if not self._is_small_body(curr, prev):
            return
        
        # Bullish harami
        if prev.is_bearish and curr.is_bullish:
            self._add_pattern("Bullish Harami", PatternType.BULLISH, idx-1, idx, [prev, curr])
        
        # Bearish harami
        elif prev.is_bullish and curr.is_bearish:
            self._add_pattern("Bearish Harami", PatternType.BEARISH, idx-1, idx, [prev, curr])
    
    def _detect_piercing_pattern(self, idx: int):
        """Detect piercing pattern (bullish reversal)"""
        prev = self.candles[idx - 1]
        curr = self.candles[idx]
        
        # First candle must be long bearish
        if not prev.is_bearish or not self._is_long_body(prev):
            return
        
        # Second candle must be bullish
        if not curr.is_bullish:
            return
        
        # Must open below previous low
        if curr.open >= prev.low:
            return
        
        # Must close above 50% of previous body
        prev_mid = prev.close + (prev.body * 0.5)
        if curr.close <= prev_mid:
            return
        
        # Must close below previous open
        if curr.close >= prev.open:
            return
        
        self._add_pattern("Piercing Pattern", PatternType.BULLISH, idx-1, idx, [prev, curr])
    
    def _detect_dark_cloud_cover(self, idx: int):
        """Detect dark cloud cover (bearish reversal)"""
        prev = self.candles[idx - 1]
        curr = self.candles[idx]
        
        # First candle must be long bullish
        if not prev.is_bullish or not self._is_long_body(prev):
            return
        
        # Second candle must be bearish
        if not curr.is_bearish:
            return
        
        # Must open above previous high
        if curr.open <= prev.high:
            return
        
        # Must close below 50% of previous body
        prev_mid = prev.close - (prev.body * 0.5)
        if curr.close >= prev_mid:
            return
        
        # Must close above previous open
        if curr.close <= prev.open:
            return
        
        self._add_pattern("Dark Cloud Cover", PatternType.BEARISH, idx-1, idx, [prev, curr])
    
    def _detect_tweezers(self, idx: int):
        """Detect tweezer tops and bottoms"""
        prev = self.candles[idx - 1]
        curr = self.candles[idx]
        
        # Tweezer tops (bearish)
        if prev.is_bullish and curr.is_bearish:
            high_diff = abs(prev.high - curr.high) / prev.high
            if high_diff < self.EQUAL_PRICE_TOLERANCE:
                self._add_pattern("Tweezer Tops", PatternType.BEARISH, idx-1, idx, [prev, curr])
        
        # Tweezer bottoms (bullish)
        elif prev.is_bearish and curr.is_bullish:
            low_diff = abs(prev.low - curr.low) / prev.low
            if low_diff < self.EQUAL_PRICE_TOLERANCE:
                self._add_pattern("Tweezer Bottoms", PatternType.BULLISH, idx-1, idx, [prev, curr])
    
    # ==================== THREE CANDLE PATTERNS ====================
    
    def _detect_morning_star(self, idx: int):
        """Detect morning star pattern (bullish reversal)"""
        c1 = self.candles[idx - 2]
        c2 = self.candles[idx - 1]
        c3 = self.candles[idx]
        
        # First candle: long bearish
        if not c1.is_bearish or not self._is_long_body(c1):
            return
        
        # Second candle: small body (star)
        if not self._is_small_body(c2, c1):
            return
        
        # Third candle: long bullish
        if not c3.is_bullish or not self._is_long_body(c3):
            return
        
        # Third candle should close well into first candle's body
        c1_mid = c1.open - (c1.body * 0.5)
        if c3.close < c1_mid:
            return
        
        self._add_pattern("Morning Star", PatternType.BULLISH, idx-2, idx, [c1, c2, c3])
    
    def _detect_evening_star(self, idx: int):
        """Detect evening star pattern (bearish reversal)"""
        c1 = self.candles[idx - 2]
        c2 = self.candles[idx - 1]
        c3 = self.candles[idx]
        
        # First candle: long bullish
        if not c1.is_bullish or not self._is_long_body(c1):
            return
        
        # Second candle: small body (star)
        if not self._is_small_body(c2, c1):
            return
        
        # Third candle: long bearish
        if not c3.is_bearish or not self._is_long_body(c3):
            return
        
        # Third candle should close well into first candle's body
        c1_mid = c1.open + (c1.body * 0.5)
        if c3.close > c1_mid:
            return
        
        self._add_pattern("Evening Star", PatternType.BEARISH, idx-2, idx, [c1, c2, c3])
    
    def _detect_three_white_soldiers(self, idx: int):
        """Detect three white soldiers (bullish continuation)"""
        c1 = self.candles[idx - 2]
        c2 = self.candles[idx - 1]
        c3 = self.candles[idx]
        
        # All three must be bullish
        if not (c1.is_bullish and c2.is_bullish and c3.is_bullish):
            return
        
        # Each should open within previous body
        c1_body_top = max(c1.open, c1.close)
        c1_body_bottom = min(c1.open, c1.close)
        c2_body_top = max(c2.open, c2.close)
        c2_body_bottom = min(c2.open, c2.close)
        
        if not (c1_body_bottom <= c2.open <= c1_body_top):
            return
        if not (c2_body_bottom <= c3.open <= c2_body_top):
            return
        
        # Each should close near high (small upper wick)
        for c in [c1, c2, c3]:
            if c.upper_wick > c.body * 0.2:
                return
        
        # Progressive higher closes
        if not (c3.close > c2.close > c1.close):
            return
        
        self._add_pattern("Three White Soldiers", PatternType.BULLISH, idx-2, idx, [c1, c2, c3])
    
    def _detect_three_black_crows(self, idx: int):
        """Detect three black crows (bearish continuation)"""
        c1 = self.candles[idx - 2]
        c2 = self.candles[idx - 1]
        c3 = self.candles[idx]
        
        # All three must be bearish
        if not (c1.is_bearish and c2.is_bearish and c3.is_bearish):
            return
        
        # Each should open within previous body
        c1_body_top = max(c1.open, c1.close)
        c1_body_bottom = min(c1.open, c1.close)
        c2_body_top = max(c2.open, c2.close)
        c2_body_bottom = min(c2.open, c2.close)
        
        if not (c1_body_bottom <= c2.open <= c1_body_top):
            return
        if not (c2_body_bottom <= c3.open <= c2_body_top):
            return
        
        # Each should close near low (small lower wick)
        for c in [c1, c2, c3]:
            if c.lower_wick > c.body * 0.2:
                return
        
        # Progressive lower closes
        if not (c3.close < c2.close < c1.close):
            return
        
        self._add_pattern("Three Black Crows", PatternType.BEARISH, idx-2, idx, [c1, c2, c3])
    
    def _detect_abandoned_baby(self, idx: int):
        """Detect abandoned baby pattern (strong reversal)"""
        c1 = self.candles[idx - 2]
        c2 = self.candles[idx - 1]
        c3 = self.candles[idx]
        
        # Middle candle must be doji
        if not self._is_doji(c2):
            return
        
        # Check for gaps on both sides of doji
        gap_after_c1 = c2.low > c1.high * (1 + self.GAP_THRESHOLD)
        gap_before_c3 = c3.high < c2.low * (1 - self.GAP_THRESHOLD)
        
        if not (gap_after_c1 and gap_before_c3):
            return
        
        # Determine direction
        if c1.is_bearish and c3.is_bullish and self._is_long_body(c3):
            self._add_pattern("Abandoned Baby", PatternType.BULLISH, idx-2, idx, [c1, c2, c3])
        elif c1.is_bullish and c3.is_bearish and self._is_long_body(c3):
            self._add_pattern("Abandoned Baby", PatternType.BEARISH, idx-2, idx, [c1, c2, c3])
    
    def _detect_morning_doji_star(self, idx: int):
        """Detect morning doji star pattern"""
        c1 = self.candles[idx - 2]
        c2 = self.candles[idx - 1]
        c3 = self.candles[idx]
        
        # First candle: long bearish
        if not c1.is_bearish or not self._is_long_body(c1):
            return
        
        # Second candle: doji with gap down
        if not self._is_doji(c2):
            return
        if c2.high >= c1.low:
            return
        
        # Third candle: long bullish closing into first body
        if not c3.is_bullish or not self._is_long_body(c3):
            return
        
        c1_mid = c1.open - (c1.body * 0.5)
        if c3.close < c1_mid:
            return
        
        self._add_pattern("Morning Doji Star", PatternType.BULLISH, idx-2, idx, [c1, c2, c3])
    
    def _detect_evening_doji_star(self, idx: int):
        """Detect evening doji star pattern"""
        c1 = self.candles[idx - 2]
        c2 = self.candles[idx - 1]
        c3 = self.candles[idx]
        
        # First candle: long bullish
        if not c1.is_bullish or not self._is_long_body(c1):
            return
        
        # Second candle: doji with gap up
        if not self._is_doji(c2):
            return
        if c2.low <= c1.high:
            return
        
        # Third candle: long bearish closing into first body
        if not c3.is_bearish or not self._is_long_body(c3):
            return
        
        c1_mid = c1.open + (c1.body * 0.5)
        if c3.close > c1_mid:
            return
        
        self._add_pattern("Evening Doji Star", PatternType.BEARISH, idx-2, idx, [c1, c2, c3])
    
    def _add_pattern(self, name: str, ptype: PatternType, start_idx: int, end_idx: int, 
                     candles: List[Candle], confidence: float = 1.0):
        """Add a detected pattern to the list"""
        pattern = Pattern(
            name=name,
            type=ptype,
            start_idx=start_idx,
            end_idx=end_idx,
            candles=candles,
            confidence=confidence
        )
        self.patterns.append(pattern)
    
    def get_patterns_by_type(self, ptype: PatternType) -> List[Pattern]:
        """Get all patterns of a specific type"""
        return [p for p in self.patterns if p.type == ptype]
    
    def get_patterns_by_name(self, name: str) -> List[Pattern]:
        """Get all patterns with a specific name"""
        return [p for p in self.patterns if p.name == name]
    
    def get_pattern_summary(self) -> Dict[str, int]:
        """Get summary of detected patterns"""
        summary = {}
        for p in self.patterns:
            summary[p.name] = summary.get(p.name, 0) + 1
        return summary


def detect_patterns(data: List[Dict]) -> List[Pattern]:
    """
    Convenience function to detect all patterns in OHLCV data
    
    Args:
        data: List of OHLCV dictionaries
        
    Returns:
        List of detected Pattern objects
    """
    detector = PatternDetector(data)
    return detector.detect_all_patterns()


if __name__ == '__main__':
    # Test with sample data
    sample_data = [
        {'open': 100, 'high': 105, 'low': 95, 'close': 98, 'volume': 1000, 'timestamp': 1},
        {'open': 98, 'high': 99, 'low': 97, 'close': 98, 'volume': 800, 'timestamp': 2},
        {'open': 98, 'high': 106, 'low': 97, 'close': 105, 'volume': 1500, 'timestamp': 3},
    ]
    
    detector = PatternDetector(sample_data)
    patterns = detector.detect_all_patterns()
    
    print("Detected patterns:")
    for p in patterns:
        print(f"  {p.name} ({p.type.value}) at indices {p.start_idx}-{p.end_idx}")
