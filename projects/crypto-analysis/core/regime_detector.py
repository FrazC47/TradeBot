#!/usr/bin/env python3
"""
Market Regime Detector
Classifies market state: Trend / Pullback / Distribution / Accumulation / Range
"""

import numpy as np
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

class MarketRegime(Enum):
    TREND_BULL = "trend_bull"
    TREND_BEAR = "trend_bear"
    PULLBACK_BULL = "pullback_bull"
    PULLBACK_BEAR = "pullback_bear"
    DISTRIBUTION = "distribution"
    ACCUMULATION = "accumulation"
    RANGE = "range"
    UNKNOWN = "unknown"

@dataclass
class RegimeContext:
    regime: MarketRegime
    strength: float
    confidence: float
    key_level: Optional[float] = None
    structure_broken: bool = False

class RegimeDetector:
    def __init__(self, lookback: int = 20):
        self.lookback = lookback
    
    def detect(self, data: list) -> RegimeContext:
        if len(data) < self.lookback:
            return RegimeContext(MarketRegime.UNKNOWN, 0.0, 0.0)
        
        closes = [d['close'] for d in data[-self.lookback:]]
        highs = [d['high'] for d in data[-self.lookback:]]
        lows = [d['low'] for d in data[-self.lookback:]]
        
        structure = self._calculate_structure(highs, lows)
        ema_align = self._calculate_ema_alignment(closes)
        momentum = self._calculate_momentum(closes)
        
        regime, strength = self._classify(structure, ema_align, momentum)
        confidence = abs(structure) * 0.4 + abs(ema_align) * 0.4 + abs(momentum) * 0.2
        key_level = self._find_key_level(highs, lows, closes)
        
        return RegimeContext(regime, strength, confidence, key_level)
    
    def _calculate_structure(self, highs, lows) -> float:
        hh = sum(1 for i in range(2, len(highs)) if highs[i] > highs[i-1] > highs[i-2])
        ll = sum(1 for i in range(2, len(lows)) if lows[i] < lows[i-1] < lows[i-2])
        total = hh + ll
        return (hh - ll) / total if total > 0 else 0.0
    
    def _calculate_ema_alignment(self, closes) -> float:
        if len(closes) < 50:
            return 0.0
        ema9 = self._ema(closes, 9)[-1]
        ema21 = self._ema(closes, 21)[-1]
        ema50 = self._ema(closes, 50)[-1]
        curr = closes[-1]
        
        bullish = (curr > ema9) + (ema9 > ema21) + (ema21 > ema50)
        bearish = (curr < ema9) + (ema9 < ema21) + (ema21 < ema50)
        return (bullish - bearish) / 3.0
    
    def _calculate_momentum(self, closes) -> float:
        if len(closes) < 14:
            return 0.0
        gains = sum(max(0, closes[-i] - closes[-i-1]) for i in range(1, 15))
        losses = sum(max(0, closes[-i-1] - closes[-i]) for i in range(1, 15))
        if losses == 0:
            return 1.0
        rs = gains / losses
        rsi = 100 - (100 / (1 + rs))
        return (rsi - 50) / 50
    
    def _classify(self, structure, ema, momentum) -> Tuple[MarketRegime, float]:
        # Trend
        if structure > 0.5 and ema > 0.4:
            if momentum < -0.2:
                return MarketRegime.PULLBACK_BULL, 0.7
            return MarketRegime.TREND_BULL, min(1.0, (structure + ema) / 2)
        
        if structure < -0.5 and ema < -0.4:
            if momentum > 0.2:
                return MarketRegime.PULLBACK_BEAR, 0.7
            return MarketRegime.TREND_BEAR, min(1.0, abs((structure + ema) / 2))
        
        # Distribution / Accumulation
        if abs(structure) < 0.2 and abs(ema) < 0.3:
            if momentum > 0.3:
                return MarketRegime.ACCUMULATION, 0.6
            if momentum < -0.3:
                return MarketRegime.DISTRIBUTION, 0.6
            return MarketRegime.RANGE, 0.5
        
        return MarketRegime.UNKNOWN, 0.3
    
    def _find_key_level(self, highs, lows, closes) -> float:
        return (max(highs[-10:]) + min(lows[-10:])) / 2
    
    def _ema(self, data, period):
        multiplier = 2 / (period + 1)
        ema = [sum(data[:period]) / period]
        for price in data[period:]:
            ema.append((price - ema[-1]) * multiplier + ema[-1])
        return [ema[0]] * (period - 1) + ema


if __name__ == "__main__":
    # Test
    import json
    from pathlib import Path
    
    # Load sample data
    data_file = Path('/root/.openclaw/workspace/data/binance/BTCUSDT/1d.csv')
    if data_file.exists():
        import csv
        with open(data_file) as f:
            reader = csv.DictReader(f)
            data = [{'open': float(r['open']), 'high': float(r['high']), 
                    'low': float(r['low']), 'close': float(r['close']),
                    'volume': float(r['volume'])} for r in list(reader)[-50:]]
        
        detector = RegimeDetector(lookback=20)
        regime = detector.detect(data)
        
        print(f"Regime: {regime.regime.value}")
        print(f"Strength: {regime.strength:.2f}")
        print(f"Confidence: {regime.confidence:.2f}")
        print(f"Key Level: ${regime.key_level:,.2f}" if regime.key_level else "Key Level: None")
