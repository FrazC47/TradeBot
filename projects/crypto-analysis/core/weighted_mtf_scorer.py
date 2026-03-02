#!/usr/bin/env python3
"""
Weighted MTF Scoring System
Replaces simple alignment counting with weighted cluster scoring
"""

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum

class TrendDirection(Enum):
    BULLISH = 1
    BEARISH = -1
    NEUTRAL = 0

@dataclass
class TimeframeScore:
    timeframe: str
    direction: TrendDirection
    strength: float
    weight: float
    regime: str
    confidence: float

@dataclass
class MTFScoreResult:
    macro_score: float
    intermediate_score: float
    execution_score: float
    overall_score: float
    overall_direction: TrendDirection
    confidence: float
    dominant_regime: str
    
    def is_tradeable(self, threshold: float = 0.6) -> bool:
        return abs(self.overall_score) >= threshold and self.confidence >= 0.5


class WeightedMTFScorer:
    """
    Weighted MTF scoring with cluster-based importance
    
    Weights:
    - Macro (1M, 1W): 40% - Long-term structure
    - Intermediate (1D, 4H): 35% - Trading direction  
    - Execution (1H, 15M, 5M): 25% - Timing precision
    """
    
    TIMEFRAME_WEIGHTS = {
        '1M': 0.20,
        '1w': 0.20,
        '1d': 0.20,
        '4h': 0.15,
        '1h': 0.10,
        '15m': 0.10,
        '5m': 0.05
    }
    
    CLUSTER_WEIGHTS = {
        'macro': 0.40,
        'intermediate': 0.35,
        'execution': 0.25
    }
    
    def __init__(self):
        self.timeframe_scores: Dict[str, TimeframeScore] = {}
    
    def add_timeframe(self, timeframe: str, direction: TrendDirection, 
                      strength: float, regime: str, confidence: float):
        weight = self.TIMEFRAME_WEIGHTS.get(timeframe, 0.1)
        
        self.timeframe_scores[timeframe] = TimeframeScore(
            timeframe=timeframe,
            direction=direction,
            strength=strength,
            weight=weight,
            regime=regime,
            confidence=confidence
        )
    
    def calculate(self) -> MTFScoreResult:
        macro_score = self._calculate_cluster(['1M', '1w'])
        intermediate_score = self._calculate_cluster(['1d', '4h'])
        execution_score = self._calculate_cluster(['1h', '15m', '5m'])
        
        overall = (
            macro_score * self.CLUSTER_WEIGHTS['macro'] +
            intermediate_score * self.CLUSTER_WEIGHTS['intermediate'] +
            execution_score * self.CLUSTER_WEIGHTS['execution']
        )
        
        if overall > 0.2:
            direction = TrendDirection.BULLISH
        elif overall < -0.2:
            direction = TrendDirection.BEARISH
        else:
            direction = TrendDirection.NEUTRAL
        
        confidence = self._calculate_confidence()
        dominant_regime = self._find_dominant_regime()
        
        return MTFScoreResult(
            macro_score=macro_score,
            intermediate_score=intermediate_score,
            execution_score=execution_score,
            overall_score=overall,
            overall_direction=direction,
            confidence=confidence,
            dominant_regime=dominant_regime
        )
    
    def _calculate_cluster(self, timeframes: List[str]) -> float:
        total_weight = 0
        weighted_sum = 0
        
        for tf in timeframes:
            if tf in self.timeframe_scores:
                score = self.timeframe_scores[tf]
                direction_value = score.direction.value
                weighted_sum += direction_value * score.strength * score.weight * score.confidence
                total_weight += score.weight * score.confidence
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    def _calculate_confidence(self) -> float:
        total_weight = sum(s.weight * s.confidence for s in self.timeframe_scores.values())
        max_possible = sum(self.TIMEFRAME_WEIGHTS.values())
        
        if max_possible == 0:
            return 0.0
        
        coverage = total_weight / max_possible
        
        bullish_count = sum(1 for s in self.timeframe_scores.values() if s.direction == TrendDirection.BULLISH)
        bearish_count = sum(1 for s in self.timeframe_scores.values() if s.direction == TrendDirection.BEARISH)
        
        conflict_factor = 1.0 - (min(bullish_count, bearish_count) / max(bullish_count + bearish_count, 1))
        
        return coverage * conflict_factor
    
    def _find_dominant_regime(self) -> str:
        regime_counts = {}
        for score in self.timeframe_scores.values():
            regime = score.regime
            regime_counts[regime] = regime_counts.get(regime, 0) + score.weight
        
        if not regime_counts:
            return "unknown"
        
        return max(regime_counts.items(), key=lambda x: x[1])[0]
    
    def get_alignment_report(self) -> Dict:
        result = self.calculate()
        
        return {
            'macro_score': round(result.macro_score, 3),
            'intermediate_score': round(result.intermediate_score, 3),
            'execution_score': round(result.execution_score, 3),
            'overall_score': round(result.overall_score, 3),
            'direction': result.overall_direction.name,
            'confidence': round(result.confidence, 2),
            'dominant_regime': result.dominant_regime,
            'tradeable': result.is_tradeable(),
            'timeframe_breakdown': {
                tf: {
                    'direction': s.direction.name,
                    'strength': round(s.strength, 2),
                    'regime': s.regime
                }
                for tf, s in self.timeframe_scores.items()
            }
        }
