#!/usr/bin/env python3
"""
Timeframe Analyzer - Top-Down Analysis (1M → 5M)
Implements the step-by-step methodology for each timeframe
"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime

from mtf_engine_v34 import MTFEngine, TFAnalysis, Regime, TF_LOOKBACKS

@dataclass
class MacroContext:
    """Context passed down from higher timeframes"""
    macro_direction: int = 0
    macro_strength: float = 0.0
    macro_confidence: float = 0.0
    macro_regime: str = "unknown"
    strategic_bias: str = "neutral"
    hunt_longs: bool = False
    hunt_shorts: bool = False
    key_levels: Dict = None
    
    def __post_init__(self):
        if self.key_levels is None:
            self.key_levels = {}

@dataclass
class MTFResult:
    """Complete MTF analysis result"""
    symbol: str
    timestamp: int
    timeframes: Dict[str, TFAnalysis]
    macro_permission: str
    strategic_bias: str
    hunt_mode: Dict[str, bool]
    overall_score: float
    overall_confidence: float
    tradeable: bool
    direction: int  # -1, 0, +1

class TimeframeAnalyzer:
    """
    Analyzes timeframes from 1M → 5M with context inheritance
    """
    
    INTERVALS = ['1M', '1w', '1d', '4h', '1h', '15m', '5m']
    
    # Cluster definitions
    MACRO_INTERVALS = ['1M', '1w']
    INTERMEDIATE_INTERVALS = ['1d', '4h']
    EXECUTION_INTERVALS = ['1h', '15m', '5m']
    
    # Weights
    CLUSTER_WEIGHTS = {
        'macro': 0.40,
        'intermediate': 0.35,
        'execution': 0.25
    }
    
    TF_WEIGHTS = {
        '1M': 0.20, '1w': 0.20,
        '1d': 0.21, '4h': 0.14,
        '1h': 0.10, '15m': 0.10, '5m': 0.05
    }
    
    def __init__(self, engine: MTFEngine):
        self.engine = engine
    
    # ============================================================
    # 1) MONTHLY (1M) - Macro Climate
    # ============================================================
    
    def analyze_1M(self, symbol: str) -> Tuple[TFAnalysis, MacroContext]:
        """
        1M: Define long-cycle permission + macro regime
        """
        analysis = self.engine.analyze_timeframe(symbol, '1M')
        if not analysis:
            return None, MacroContext()
        
        # Determine macro permission
        if analysis.direction == 1 and analysis.confidence >= 0.50:
            permission = "Prefer LONG"
        elif analysis.direction == -1 and analysis.confidence >= 0.50:
            permission = "Prefer SHORT"
        else:
            permission = "Neutral macro"
        
        context = MacroContext(
            macro_direction=analysis.direction,
            macro_strength=analysis.strength,
            macro_confidence=analysis.confidence,
            macro_regime=analysis.regime.value,
            key_levels=analysis.key_levels
        )
        
        return analysis, context
    
    # ============================================================
    # 2) WEEKLY (1W) - Seasonal Confirmation
    # ============================================================
    
    def analyze_1W(self, symbol: str, context: MacroContext) -> Tuple[TFAnalysis, MacroContext]:
        """
        1W: Confirm or weaken 1M; detect regime transition
        """
        prev_regime = Regime(context.macro_regime) if context.macro_regime else None
        analysis = self.engine.analyze_timeframe(symbol, '1w', prev_regime)
        if not analysis:
            return None, context
        
        # Compare 1W vs 1M
        if analysis.direction == context.macro_direction:
            # Aligned - raise confidence
            context.macro_strength = min(1.0, context.macro_strength * 1.1)
        elif analysis.direction == 0:
            # 1W neutral while 1M directional - reduce slightly
            context.macro_strength = context.macro_strength * 0.9
        elif analysis.confidence >= 0.50:
            # Conflict with high confidence - transitional
            context.macro_regime = "transitional"
            context.macro_strength = context.macro_strength * 0.7
        
        # Update key levels
        context.key_levels.update({
            'weekly_swing_high': analysis.key_levels.get('swing_high'),
            'weekly_swing_low': analysis.key_levels.get('swing_low')
        })
        
        return analysis, context
    
    # ============================================================
    # 3) DAILY (1D) - Strategic Bias
    # ============================================================
    
    def analyze_1D(self, symbol: str, context: MacroContext) -> Tuple[TFAnalysis, MacroContext]:
        """
        1D: Decide trend continuation vs correction; set strategic bias
        """
        prev_regime = Regime(context.macro_regime) if context.macro_regime else None
        analysis = self.engine.analyze_timeframe(symbol, '1d', prev_regime)
        if not analysis:
            return None, context
        
        # Interpret with macro context
        macro_bullish = context.macro_direction == 1
        macro_bearish = context.macro_direction == -1
        
        if macro_bullish and analysis.regime == Regime.PULLBACK_BULL:
            strategic_bias = "LONG_BIAS"
        elif macro_bearish and analysis.regime == Regime.PULLBACK_BEAR:
            strategic_bias = "SHORT_BIAS"
        elif macro_bullish and analysis.regime == Regime.TREND_BEAR:
            # Correction / possible shift
            strategic_bias = "CAUTION_LONG"
        elif macro_bearish and analysis.regime == Regime.TREND_BULL:
            strategic_bias = "CAUTION_SHORT"
        elif context.macro_direction == 0:
            # Macro neutral - daily becomes primary
            strategic_bias = "LONG_BIAS" if analysis.direction == 1 else \
                           "SHORT_BIAS" if analysis.direction == -1 else "NEUTRAL"
        else:
            strategic_bias = "NEUTRAL"
        
        context.strategic_bias = strategic_bias
        context.key_levels.update({
            'daily_vwap': analysis.metrics.close,  # Would use actual VWAP
            'daily_atr_pct': analysis.metrics.atr_pct,
            'daily_swing_high': analysis.key_levels.get('swing_high'),
            'daily_swing_low': analysis.key_levels.get('swing_low')
        })
        
        return analysis, context
    
    # ============================================================
    # 4) 4H - Tactical Alignment
    # ============================================================
    
    def analyze_4H(self, symbol: str, context: MacroContext) -> Tuple[TFAnalysis, MacroContext]:
        """
        4H: Confirm daily intent; decide whether to hunt setups
        """
        prev_regime = Regime(context.macro_regime) if context.macro_regime else None
        analysis = self.engine.analyze_timeframe(symbol, '4h', prev_regime)
        if not analysis:
            return None, context
        
        # Apply permission rule
        strategic_long = "LONG" in context.strategic_bias
        strategic_short = "SHORT" in context.strategic_bias
        
        # Check alignment
        if analysis.direction == context.macro_direction:
            # Aligned - allowed
            pass
        elif analysis.direction != 0:
            # Opposite - countertrend, block or require stronger confirmation
            if analysis.confidence >= 0.60:
                # Strong opposite - might be early reversal
                pass
        
        # Decide hunt mode
        hunt_longs = (strategic_long and 
                     analysis.regime in [Regime.TREND_BULL, Regime.PULLBACK_BULL])
        hunt_shorts = (strategic_short and 
                      analysis.regime in [Regime.TREND_BEAR, Regime.PULLBACK_BEAR])
        
        context.hunt_longs = hunt_longs
        context.hunt_shorts = hunt_shorts
        context.key_levels.update({
            '4h_higher_low': analysis.key_levels.get('higher_low'),
            '4h_lower_high': analysis.key_levels.get('lower_high'),
            '4h_swing_high': analysis.key_levels.get('swing_high'),
            '4h_swing_low': analysis.key_levels.get('swing_low')
        })
        
        return analysis, context
    
    # ============================================================
    # 5) 1H - Setup Formation
    # ============================================================
    
    def analyze_1H(self, symbol: str, context: MacroContext) -> Tuple[TFAnalysis, bool]:
        """
        1H: Detect forming setup (not trigger)
        """
        prev_regime = Regime(context.macro_regime) if context.macro_regime else None
        analysis = self.engine.analyze_timeframe(symbol, '1h', prev_regime)
        if not analysis:
            return None, False
        
        # Check hunt mode
        if not context.hunt_longs and not context.hunt_shorts:
            return analysis, False
        
        # Setup classification
        candidate_setup = False
        candidate_direction = 0
        
        if context.hunt_longs and analysis.regime == Regime.PULLBACK_BULL:
            # Check structure intact
            if analysis.key_levels.get('higher_low') and \
               analysis.metrics.close > analysis.key_levels['higher_low']:
                # Prefer RSI recovering or momentum rising
                if analysis.metrics.momentum > -0.3:  # Recovering
                    candidate_setup = True
                    candidate_direction = 1
        
        elif context.hunt_shorts and analysis.regime == Regime.PULLBACK_BEAR:
            if analysis.key_levels.get('lower_high') and \
               analysis.metrics.close < analysis.key_levels['lower_high']:
                if analysis.metrics.momentum < 0.3:
                    candidate_setup = True
                    candidate_direction = -1
        
        return analysis, candidate_setup
    
    # ============================================================
    # 6) 15M - Entry Refinement
    # ============================================================
    
    def analyze_15M(self, symbol: str, candidate_setup: bool, 
                   context: MacroContext) -> Tuple[TFAnalysis, Optional[Dict]]:
        """
        15M: Define precise entry zone and validate confluence
        """
        if not candidate_setup:
            return None, None
        
        prev_regime = Regime(context.macro_regime) if context.macro_regime else None
        analysis = self.engine.analyze_timeframe(symbol, '15m', prev_regime)
        if not analysis:
            return None, None
        
        # Define entry zone using fib of last swing
        swing_high = analysis.key_levels.get('swing_high')
        swing_low = analysis.key_levels.get('swing_low')
        
        if not swing_high or not swing_low:
            return analysis, None
        
        diff = swing_high - swing_low
        fib_618 = swing_high - diff * 0.618
        
        # Entry zone with ATR buffer
        atr_5m = analysis.metrics.atr_pct * analysis.metrics.close
        entry_zone_low = fib_618 - (0.15 * atr_5m)
        entry_zone_high = fib_618 + (0.15 * atr_5m)
        
        # VWAP alignment check
        vwap_aligned = True  # Would check actual VWAP
        
        # Liquidity filter (simplified)
        liquidity_ok = True
        
        if vwap_aligned and liquidity_ok:
            entry_zone = {
                'low': entry_zone_low,
                'high': entry_zone_high,
                'fib_level': '0.618',
                'swing_high': swing_high,
                'swing_low': swing_low
            }
            return analysis, entry_zone
        
        return analysis, None
    
    # ============================================================
    # 7) 5M - Trigger/Confirmation
    # ============================================================
    
    def analyze_5M(self, symbol: str, entry_zone: Optional[Dict]) -> Tuple[TFAnalysis, bool]:
        """
        5M: Activate trade only on confirmed 5m close
        """
        analysis = self.engine.analyze_timeframe(symbol, '5m')
        if not analysis:
            return None, False
        
        if not entry_zone:
            return analysis, False
        
        close = analysis.metrics.close
        
        # Check confirmation conditions
        confirmed = False
        
        # For LONG
        if close > entry_zone['high']:
            confirmed = True
        elif close > analysis.key_levels.get('ema9', 0) and analysis.metrics.momentum > 0:
            confirmed = True
        # Add more conditions: engulfing, BOS, etc.
        
        # Hard filters
        if confirmed:
            # Volume check (simplified)
            volume_ok = True
            
            # Range trap filter
            if analysis.regime == Regime.RANGE:
                # Would check bars_in_regime, momentum, ATR compression
                pass
            
            if not volume_ok:
                confirmed = False
        
        return analysis, confirmed
    
    # ============================================================
    # Complete Analysis
    # ============================================================
    
    def analyze_symbol(self, symbol: str) -> Optional[MTFResult]:
        """
        Complete top-down analysis for a symbol
        """
        timestamp = int(datetime.now().timestamp() * 1000)
        timeframes = {}
        
        # 1M: Macro permission
        tf_1m, context = self.analyze_1M(symbol)
        if not tf_1m:
            return None
        timeframes['1M'] = tf_1m
        
        # 1W: Seasonal confirmation
        tf_1w, context = self.analyze_1W(symbol, context)
        if tf_1w:
            timeframes['1w'] = tf_1w
        
        # 1D: Strategic bias
        tf_1d, context = self.analyze_1D(symbol, context)
        if tf_1d:
            timeframes['1d'] = tf_1d
        
        # 4H: Tactical alignment
        tf_4h, context = self.analyze_4H(symbol, context)
        if tf_4h:
            timeframes['4h'] = tf_4h
        
        # 1H: Setup formation
        tf_1h, candidate_setup = self.analyze_1H(symbol, context)
        if tf_1h:
            timeframes['1h'] = tf_1h
        
        # 15M: Entry refinement
        tf_15m, entry_zone = self.analyze_15M(symbol, candidate_setup, context)
        if tf_15m:
            timeframes['15m'] = tf_15m
        
        # 5M: Trigger
        tf_5m, confirmed = self.analyze_5M(symbol, entry_zone)
        if tf_5m:
            timeframes['5m'] = tf_5m
        
        # Calculate overall score
        overall, conf = self.calculate_overall_score(timeframes)
        
        # Determine tradeability
        tradeable = self.is_tradeable(overall, conf, timeframes)
        
        return MTFResult(
            symbol=symbol,
            timestamp=timestamp,
            timeframes=timeframes,
            macro_permission="Prefer LONG" if context.macro_direction == 1 else \
                          "Prefer SHORT" if context.macro_direction == -1 else "Neutral",
            strategic_bias=context.strategic_bias,
            hunt_mode={'hunt_longs': context.hunt_longs, 'hunt_shorts': context.hunt_shorts},
            overall_score=overall,
            overall_confidence=conf,
            tradeable=tradeable,
            direction=1 if overall > 0.2 else (-1 if overall < -0.2 else 0)
        )
    
    def calculate_overall_score(self, timeframes: Dict[str, TFAnalysis]) -> Tuple[float, float]:
        """Calculate weighted overall MTF score"""
        
        def calc_cluster(intervals, name):
            total_weight = 0
            weighted_sum = 0
            conf_sum = 0
            
            for interval in intervals:
                if interval in timeframes:
                    tf = timeframes[interval]
                    w = self.TF_WEIGHTS.get(interval, 0.1)
                    weighted_sum += tf.direction * tf.strength * w * tf.confidence
                    total_weight += w * tf.confidence
                    conf_sum += tf.confidence * w
            
            if total_weight == 0:
                return 0.0, 0.0
            
            return weighted_sum / total_weight, conf_sum / sum(self.TF_WEIGHTS.get(i, 0.1) for i in intervals)
        
        macro, macro_conf = calc_cluster(self.MACRO_INTERVALS, 'macro')
        intermediate, inter_conf = calc_cluster(self.INTERMEDIATE_INTERVALS, 'intermediate')
        execution, exec_conf = calc_cluster(self.EXECUTION_INTERVALS, 'execution')
        
        overall = (self.CLUSTER_WEIGHTS['macro'] * macro + 
                  self.CLUSTER_WEIGHTS['intermediate'] * intermediate +
                  self.CLUSTER_WEIGHTS['execution'] * execution)
        
        overall_conf = (self.CLUSTER_WEIGHTS['macro'] * macro_conf +
                       self.CLUSTER_WEIGHTS['intermediate'] * inter_conf +
                       self.CLUSTER_WEIGHTS['execution'] * exec_conf)
        
        return overall, overall_conf
    
    def is_tradeable(self, overall: float, confidence: float, 
                    timeframes: Dict[str, TFAnalysis]) -> bool:
        """Golden Rule v2: Check if tradeable"""
        
        # Check threshold
        threshold = 0.45  # Base threshold
        if abs(overall) < threshold:
            return False
        
        # Check confidence
        if confidence < 0.50:
            return False
        
        # Check minimum TFs with valid regimes
        valid_tfs = sum(1 for tf in timeframes.values() 
                       if tf.confidence >= 0.35 and tf.regime != Regime.UNKNOWN)
        if valid_tfs < 4:
            return False
        
        # Golden Rule v2: macro + intermediate agree, execution aligned or pullback
        macro_dir = timeframes.get('1M', TFAnalysis(Regime.UNKNOWN, 0, 0, 0, None, {})).direction
        daily_dir = timeframes.get('1d', TFAnalysis(Regime.UNKNOWN, 0, 0, 0, None, {})).direction
        exec_regime = timeframes.get('4h', TFAnalysis(Regime.UNKNOWN, 0, 0, 0, None, {})).regime
        exec_dir = timeframes.get('4h', TFAnalysis(Regime.UNKNOWN, 0, 0, 0, None, {})).direction
        
        # Macro + intermediate must agree
        if macro_dir != daily_dir or macro_dir == 0:
            return False
        
        # Execution aligned OR pullback within trend
        if exec_dir == macro_dir:
            return True
        
        if exec_regime == Regime.PULLBACK_BULL and macro_dir == 1:
            return True
        if exec_regime == Regime.PULLBACK_BEAR and macro_dir == -1:
            return True
        
        return False


if __name__ == '__main__':
    from mtf_engine_v34 import MTFEngine
    
    engine = MTFEngine(Path('/root/.openclaw/workspace/data/binance'))
    analyzer = TimeframeAnalyzer(engine)
    
    result = analyzer.analyze_symbol('BTCUSDT')
    if result:
        print(f"Symbol: {result.symbol}")
        print(f"Tradeable: {result.tradeable}")
        print(f"Direction: {result.direction}")
        print(f"Overall Score: {result.overall_score:.3f}")
        print(f"Strategic Bias: {result.strategic_bias}")
        print(f"Hunt Mode: {result.hunt_mode}")
