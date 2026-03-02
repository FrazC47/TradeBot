#!/usr/bin/env python3
"""
Candlestick Pattern Recognition Module
Option C: Separate signal filter - pattern required for trade entry
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

class PatternType(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"

class PatternStrength(Enum):
    STRONG = 3      # High reliability, clear structure
    MODERATE = 2    # Good reliability, needs confirmation
    WEAK = 1        # Lower reliability, use with caution

@dataclass
class CandlestickPattern:
    name: str
    pattern_type: PatternType
    strength: PatternStrength
    confidence: float  # 0.0 to 1.0 based on pattern quality
    
    def is_bullish(self) -> bool:
        return self.pattern_type == PatternType.BULLISH
    
    def is_bearish(self) -> bool:
        return self.pattern_type == PatternType.BEARISH


class CandlestickPatternRecognizer:
    """
    Recognizes major candlestick patterns for trade entry filtering
    
    Pattern Categories:
    - Single candle: Hammer, Shooting Star, Doji, Marubozu
    - Double candle: Engulfing, Harami, Tweezer
    - Triple candle: Morning/Evening Star, Three Soldiers/Crows
    """
    
    # Minimum pattern strength required for trade entry
    MIN_PATTERN_STRENGTH = PatternStrength.MODERATE
    
    def __init__(self, min_strength: PatternStrength = PatternStrength.MODERATE):
        self.min_strength = min_strength
    
    def analyze(self, data: List[dict], lookback: int = 5) -> Optional[CandlestickPattern]:
        """
        Analyze recent candles for patterns
        Returns strongest pattern found or None
        """
        if len(data) < 3:
            return None
        
        patterns = []
        
        # Single candle patterns (most recent)
        single = self._check_single_candle(data[-1], data[-2] if len(data) > 1 else None)
        if single:
            patterns.append(single)
        
        # Double candle patterns
        if len(data) >= 2:
            double = self._check_double_candle(data[-2], data[-1])
            if double:
                patterns.append(double)
        
        # Triple candle patterns
        if len(data) >= 3:
            triple = self._check_triple_candle(data[-3], data[-2], data[-1])
            if triple:
                patterns.append(triple)
        
        # Return strongest pattern
        if patterns:
            return max(patterns, key=lambda p: (p.strength.value, p.confidence))
        
        return None
    
    def _candle_body(self, candle: dict) -> float:
        """Get candle body size"""
        return abs(candle['close'] - candle['open'])
    
    def _candle_range(self, candle: dict) -> float:
        """Get candle total range"""
        return candle['high'] - candle['low']
    
    def _is_bullish(self, candle: dict) -> bool:
        """Check if candle is bullish"""
        return candle['close'] > candle['open']
    
    def _is_bearish(self, candle: dict) -> bool:
        """Check if candle is bearish"""
        return candle['close'] < candle['open']
    
    def _body_pct(self, candle: dict) -> float:
        """Body as percentage of range"""
        range_size = self._candle_range(candle)
        if range_size == 0:
            return 0
        return self._candle_body(candle) / range_size
    
    def _upper_shadow(self, candle: dict) -> float:
        """Upper shadow size"""
        if self._is_bullish(candle):
            return candle['high'] - candle['close']
        else:
            return candle['high'] - candle['open']
    
    def _lower_shadow(self, candle: dict) -> float:
        """Lower shadow size"""
        if self._is_bullish(candle):
            return candle['open'] - candle['low']
        else:
            return candle['close'] - candle['low']
    
    def _check_single_candle(self, candle: dict, prev: Optional[dict]) -> Optional[CandlestickPattern]:
        """Check for single candle patterns"""
        range_size = self._candle_range(candle)
        body_size = self._candle_body(candle)
        body_pct = self._body_pct(candle)
        
        if range_size == 0:
            return None
        
        upper_shadow = self._upper_shadow(candle)
        lower_shadow = self._lower_shadow(candle)
        
        # Hammer (bullish reversal at bottom)
        if (lower_shadow > body_size * 2 and 
            upper_shadow < body_size * 0.5 and
            body_pct > 0.1 and body_pct < 0.3):
            
            confidence = min(1.0, lower_shadow / (body_size * 3))
            
            # Higher confidence if after downtrend
            if prev and prev['close'] > candle['close']:
                confidence *= 1.2
            
            return CandlestickPattern(
                name="Hammer",
                pattern_type=PatternType.BULLISH,
                strength=PatternStrength.STRONG if confidence > 0.7 else PatternStrength.MODERATE,
                confidence=min(1.0, confidence)
            )
        
        # Shooting Star (bearish reversal at top)
        if (upper_shadow > body_size * 2 and 
            lower_shadow < body_size * 0.5 and
            body_pct > 0.1 and body_pct < 0.3):
            
            confidence = min(1.0, upper_shadow / (body_size * 3))
            
            # Higher confidence if after uptrend
            if prev and prev['close'] < candle['close']:
                confidence *= 1.2
            
            return CandlestickPattern(
                name="Shooting Star",
                pattern_type=PatternType.BEARISH,
                strength=PatternStrength.STRONG if confidence > 0.7 else PatternStrength.MODERATE,
                confidence=min(1.0, confidence)
            )
        
        # Doji (indecision)
        if body_pct < 0.05:
            return CandlestickPattern(
                name="Doji",
                pattern_type=PatternType.NEUTRAL,
                strength=PatternStrength.WEAK,
                confidence=0.5
            )
        
        # Marubozu (strong trend)
        if body_pct > 0.95:
            if self._is_bullish(candle):
                return CandlestickPattern(
                    name="Bullish Marubozu",
                    pattern_type=PatternType.BULLISH,
                    strength=PatternStrength.MODERATE,
                    confidence=0.7
                )
            else:
                return CandlestickPattern(
                    name="Bearish Marubozu",
                    pattern_type=PatternType.BEARISH,
                    strength=PatternStrength.MODERATE,
                    confidence=0.7
                )
        
        return None
    
    def _check_double_candle(self, first: dict, second: dict) -> Optional[CandlestickPattern]:
        """Check for double candle patterns"""
        
        # Bullish Engulfing
        if (self._is_bearish(first) and self._is_bullish(second) and
            second['open'] < first['close'] and
            second['close'] > first['open']):
            
            # Stronger if second candle engulfs more of first
            engulf_pct = (second['close'] - second['open']) / (first['open'] - first['close'])
            confidence = min(1.0, engulf_pct * 0.8)
            
            return CandlestickPattern(
                name="Bullish Engulfing",
                pattern_type=PatternType.BULLISH,
                strength=PatternStrength.STRONG,
                confidence=confidence
            )
        
        # Bearish Engulfing
        if (self._is_bullish(first) and self._is_bearish(second) and
            second['open'] > first['close'] and
            second['close'] < first['open']):
            
            engulf_pct = (second['open'] - second['close']) / (first['close'] - first['open'])
            confidence = min(1.0, engulf_pct * 0.8)
            
            return CandlestickPattern(
                name="Bearish Engulfing",
                pattern_type=PatternType.BEARISH,
                strength=PatternStrength.STRONG,
                confidence=confidence
            )
        
        # Bullish Harami
        if (self._is_bearish(first) and self._is_bullish(second) and
            second['open'] > first['close'] and
            second['close'] < first['open'] and
            self._body_pct(second) < self._body_pct(first) * 0.5):
            
            return CandlestickPattern(
                name="Bullish Harami",
                pattern_type=PatternType.BULLISH,
                strength=PatternStrength.MODERATE,
                confidence=0.6
            )
        
        # Bearish Harami
        if (self._is_bullish(first) and self._is_bearish(second) and
            second['open'] < first['close'] and
            second['close'] > first['open'] and
            self._body_pct(second) < self._body_pct(first) * 0.5):
            
            return CandlestickPattern(
                name="Bearish Harami",
                pattern_type=PatternType.BEARISH,
                strength=PatternStrength.MODERATE,
                confidence=0.6
            )
        
        # Tweezer Bottoms
        if (self._is_bearish(first) and self._is_bullish(second) and
            abs(first['low'] - second['low']) / first['low'] < 0.001):
            
            return CandlestickPattern(
                name="Tweezer Bottoms",
                pattern_type=PatternType.BULLISH,
                strength=PatternStrength.MODERATE,
                confidence=0.65
            )
        
        # Tweezer Tops
        if (self._is_bullish(first) and self._is_bearish(second) and
            abs(first['high'] - second['high']) / first['high'] < 0.001):
            
            return CandlestickPattern(
                name="Tweezer Tops",
                pattern_type=PatternType.BEARISH,
                strength=PatternStrength.MODERATE,
                confidence=0.65
            )
        
        return None
    
    def _check_triple_candle(self, first: dict, second: dict, third: dict) -> Optional[CandlestickPattern]:
        """Check for triple candle patterns"""
        
        # Morning Star (bullish reversal)
        if (self._is_bearish(first) and 
            self._body_pct(second) < 0.3 and  # Small second candle (star)
            self._is_bullish(third) and
            third['close'] > (first['open'] + first['close']) / 2):  # Closes into first body
            
            confidence = 0.7
            if second['open'] < first['close']:  # Gap down
                confidence += 0.1
            
            return CandlestickPattern(
                name="Morning Star",
                pattern_type=PatternType.BULLISH,
                strength=PatternStrength.STRONG,
                confidence=min(1.0, confidence)
            )
        
        # Evening Star (bearish reversal)
        if (self._is_bullish(first) and 
            self._body_pct(second) < 0.3 and  # Small second candle (star)
            self._is_bearish(third) and
            third['close'] < (first['open'] + first['close']) / 2):  # Closes into first body
            
            confidence = 0.7
            if second['open'] > first['close']:  # Gap up
                confidence += 0.1
            
            return CandlestickPattern(
                name="Evening Star",
                pattern_type=PatternType.BEARISH,
                strength=PatternStrength.STRONG,
                confidence=min(1.0, confidence)
            )
        
        # Three White Soldiers (strong bullish)
        if (self._is_bullish(first) and self._is_bullish(second) and self._is_bullish(third) and
            second['open'] > first['open'] and third['open'] > second['open'] and
            second['close'] > first['close'] and third['close'] > second['close'] and
            self._body_pct(first) > 0.5 and self._body_pct(second) > 0.5 and self._body_pct(third) > 0.5):
            
            return CandlestickPattern(
                name="Three White Soldiers",
                pattern_type=PatternType.BULLISH,
                strength=PatternStrength.STRONG,
                confidence=0.85
            )
        
        # Three Black Crows (strong bearish)
        if (self._is_bearish(first) and self._is_bearish(second) and self._is_bearish(third) and
            second['open'] < first['open'] and third['open'] < second['open'] and
            second['close'] < first['close'] and third['close'] < second['close'] and
            self._body_pct(first) > 0.5 and self._body_pct(second) > 0.5 and self._body_pct(third) > 0.5):
            
            return CandlestickPattern(
                name="Three Black Crows",
                pattern_type=PatternType.BEARISH,
                strength=PatternStrength.STRONG,
                confidence=0.85
            )
        
        return None
    
    def validate_for_entry(self, pattern: CandlestickPattern, direction: str) -> Tuple[bool, float]:
        """
        Validate if pattern supports trade entry
        
        Args:
            pattern: Detected candlestick pattern
            direction: 'LONG' or 'SHORT'
        
        Returns:
            (is_valid, confidence_boost)
        """
        if not pattern:
            return False, 0.0
        
        # Check minimum strength
        if pattern.strength.value < self.min_strength.value:
            return False, 0.0
        
        # Check direction alignment
        if direction == "LONG" and not pattern.is_bullish():
            return False, 0.0
        
        if direction == "SHORT" and not pattern.is_bearish():
            return False, 0.0
        
        # Pattern supports entry - calculate confidence boost
        strength_boost = {
            PatternStrength.STRONG: 0.15,
            PatternStrength.MODERATE: 0.10,
            PatternStrength.WEAK: 0.05
        }
        
        boost = strength_boost.get(pattern.strength, 0.05)
        
        return True, boost


# Integration with MTF Engine
class PatternFilteredEntry:
    """
    Integrates candlestick patterns with MTF system
    Option C: Pattern required for trade entry
    """
    
    def __init__(self):
        self.pattern_recognizer = CandlestickPatternRecognizer()
    
    def check_entry_permission(self, data: List[dict], direction: str, 
                                mtf_score: float, mtf_confidence: float) -> dict:
        """
        Check if candlestick pattern permits entry
        
        Returns:
            {
                'permitted': bool,
                'pattern': str or None,
                'pattern_confidence': float,
                'adjusted_confidence': float,
                'reason': str
            }
        """
        # Detect pattern
        pattern = self.pattern_recognizer.analyze(data)
        
        if not pattern:
            return {
                'permitted': False,
                'pattern': None,
                'pattern_confidence': 0.0,
                'adjusted_confidence': mtf_confidence,
                'reason': 'No qualifying candlestick pattern detected'
            }
        
        # Validate pattern for entry
        is_valid, boost = self.pattern_recognizer.validate_for_entry(pattern, direction)
        
        if not is_valid:
            return {
                'permitted': False,
                'pattern': pattern.name,
                'pattern_confidence': pattern.confidence,
                'adjusted_confidence': mtf_confidence,
                'reason': f"Pattern {pattern.name} ({pattern.pattern_type.value}) doesn't align with {direction}"
            }
        
        # Pattern valid - boost confidence
        adjusted_confidence = min(1.0, mtf_confidence + boost)
        
        return {
            'permitted': True,
            'pattern': pattern.name,
            'pattern_confidence': pattern.confidence,
            'adjusted_confidence': adjusted_confidence,
            'reason': f"Valid {pattern.name} pattern detected (+{boost:.0%} confidence)"
        }


if __name__ == "__main__":
    # Test
    import csv
    from pathlib import Path
    
    data_file = Path('/root/.openclaw/workspace/data/binance/BTCUSDT/1h.csv')
    if data_file.exists():
        with open(data_file) as f:
            reader = csv.DictReader(f)
            data = [{'open': float(r['open']), 'high': float(r['high']), 
                    'low': float(r['low']), 'close': float(r['close']),
                    'volume': float(r['volume'])} for r in list(reader)[-10:]]
        
        recognizer = CandlestickPatternRecognizer()
        pattern = recognizer.analyze(data)
        
        if pattern:
            print(f"Pattern: {pattern.name}")
            print(f"Type: {pattern.pattern_type.value}")
            print(f"Strength: {pattern.strength.name}")
            print(f"Confidence: {pattern.confidence:.2f}")
            
            # Test validation
            validator = PatternFilteredEntry()
            result = validator.check_entry_permission(data, "LONG", 0.6, 0.7)
            print(f"\nEntry permission: {result}")
        else:
            print("No pattern detected")
