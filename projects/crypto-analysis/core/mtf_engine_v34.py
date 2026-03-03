#!/usr/bin/env python3
"""
MTF Engine v3.4 - Core Metrics and Regime Classification
Production implementation of deterministic trading logic
"""

import json
import csv
import math
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum

class Regime(Enum):
    TREND_BULL = "trend_bull"
    TREND_BEAR = "trend_bear"
    PULLBACK_BULL = "pullback_bull"
    PULLBACK_BEAR = "pullback_bear"
    RANGE = "range"
    RANGE_BULL_DRIFT = "range_bull_drift"
    RANGE_BEAR_DRIFT = "range_bear_drift"
    TRANSITIONAL = "transitional"
    BREAKOUT = "breakout"
    BREAKDOWN = "breakdown"
    UNKNOWN = "unknown"

@dataclass
class TFMetrics:
    """Metrics for a single timeframe"""
    structure_score: float
    ema_alignment: float
    momentum: float
    range_pct: float
    atr_pct: float
    close: float
    
    # Structure levels
    last_swing_high: Optional[float] = None
    last_swing_low: Optional[float] = None
    last_higher_low: Optional[float] = None
    last_lower_high: Optional[float] = None

@dataclass
class TFAnalysis:
    """Complete analysis for a timeframe"""
    regime: Regime
    direction: int  # -1, 0, +1
    strength: float  # 0-1
    confidence: float  # 0-1
    metrics: TFMetrics
    key_levels: Dict

# TF Configurations
TF_LOOKBACKS = {
    '1M': 24, '1w': 52, '1d': 50, '4h': 72,
    '1h': 72, '15m': 96, '5m': 72
}

TF_WEIGHTS = {
    '1M': 0.20, '1w': 0.20, '1d': 0.21, '4h': 0.14,
    '1h': 0.10, '15m': 0.10, '5m': 0.05
}

class MTFEngine:
    """Multi-timeframe analysis engine"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
    
    # ============================================================
    # STEP TF.1: Core Metrics
    # ============================================================
    
    def calculate_structure(self, data: List[dict], lookback: int = 50, 
                           swing_bars: int = 2) -> Tuple[float, Dict]:
        """
        Calculate structure score with swing points
        Returns: (score, levels_dict)
        """
        if len(data) < 10:
            return 0.0, {}
        
        highs = [c['high'] for c in data[-lookback:]]
        lows = [c['low'] for c in data[-lookback:]]
        closes = [c['close'] for c in data[-lookback:]]
        
        # Find swing points with plateau protection
        swing_highs = []
        swing_lows = []
        
        for i in range(swing_bars, len(highs) - swing_bars):
            window_h = highs[i-swing_bars:i+swing_bars+1]
            window_l = lows[i-swing_bars:i+swing_bars+1]
            
            # Plateau protection: must be unique max/min
            if highs[i] == max(window_h) and window_h.count(highs[i]) == 1:
                swing_highs.append((i, highs[i]))
            if lows[i] == min(window_l) and window_l.count(lows[i]) == 1:
                swing_lows.append((i, lows[i]))
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return 0.0, {}
        
        # Count HH/HL vs LH/LL
        hh = sum(1 for i in range(1, len(swing_highs)) 
                 if swing_highs[i][1] > swing_highs[i-1][1])
        lh = sum(1 for i in range(1, len(swing_highs)) 
                 if swing_highs[i][1] < swing_highs[i-1][1])
        hl = sum(1 for i in range(1, len(swing_lows)) 
                 if swing_lows[i][1] > swing_lows[i-1][1])
        ll = sum(1 for i in range(1, len(swing_lows)) 
                 if swing_lows[i][1] < swing_lows[i-1][1])
        
        up = hh + hl
        down = lh + ll
        total = up + down
        
        score = (up - down) / total if total > 0 else 0.0
        
        # Extract key levels
        levels = {
            'last_swing_high': swing_highs[-1][1] if swing_highs else None,
            'last_swing_low': swing_lows[-1][1] if swing_lows else None,
        }
        
        # Find last higher low (bullish structure)
        if score > 0.3 and len(swing_lows) >= 2:
            for i in range(len(swing_lows)-1, 0, -1):
                if swing_lows[i][1] > swing_lows[i-1][1]:
                    levels['last_higher_low'] = swing_lows[i][1]
                    break
        
        # Find last lower high (bearish structure)
        if score < -0.3 and len(swing_highs) >= 2:
            for i in range(len(swing_highs)-1, 0, -1):
                if swing_highs[i][1] < swing_highs[i-1][1]:
                    levels['last_lower_high'] = swing_highs[i][1]
                    break
        
        return score, levels
    
    def calculate_ema_alignment(self, data: List[dict]) -> float:
        """
        Calculate EMA alignment score
        Bullish: close > EMA9 > EMA21 > EMA50
        """
        if len(data) < 50:
            return 0.0
        
        closes = [c['close'] for c in data]
        
        def ema(prices, period):
            if len(prices) < period:
                return None
            multiplier = 2 / (period + 1)
            ema_val = sum(prices[:period]) / period
            for p in prices[period:]:
                ema_val = (p * multiplier) + (ema_val * (1 - multiplier))
            return ema_val
        
        ema9 = ema(closes, 9)
        ema21 = ema(closes, 21)
        ema50 = ema(closes, 50)
        current = closes[-1]
        
        if None in [ema9, ema21, ema50]:
            return 0.0
        
        # Bullish alignment
        bullish = (current > ema9) + (ema9 > ema21) + (ema21 > ema50)
        # Bearish alignment
        bearish = (current < ema9) + (ema9 < ema21) + (ema21 < ema50)
        
        return (bullish - bearish) / 3.0
    
    def calculate_momentum(self, data: List[dict], period: int = 14) -> float:
        """
        Calculate normalized momentum (RSI + ROC)
        Returns: -1 to +1
        """
        if len(data) < period + 1:
            return 0.0
        
        closes = [c['close'] for c in data]
        
        # RSI component (60%)
        gains = [0.0] * len(closes)
        losses = [0.0] * len(closes)
        
        for i in range(1, len(closes)):
            d = closes[i] - closes[i-1]
            gains[i] = max(d, 0.0)
            losses[i] = max(-d, 0.0)
        
        avg_gain = sum(gains[1:period+1]) / period
        avg_loss = sum(losses[1:period+1]) / period
        
        if avg_loss == 0:
            rsi_norm = 1.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_norm = (rsi - 50) / 50
        
        # ROC component (40%) - 5-bar return normalized by ATR
        roc = (closes[-1] - closes[-6]) / closes[-6] if len(closes) >= 6 else 0
        
        # Approximate ATR for normalization
        atr = sum(c['high'] - c['low'] for c in data[-period:]) / period
        atr = max(atr, closes[-1] * 0.001)  # Minimum ATR
        roc_norm = roc / (atr / closes[-1] * 5)
        roc_norm = max(-1, min(1, roc_norm))
        
        # Combined
        momentum = 0.6 * rsi_norm + 0.4 * roc_norm
        return max(-1, min(1, momentum))
    
    def calculate_range_pct(self, data: List[dict], lookback: int) -> float:
        """Calculate range as percentage of price"""
        if len(data) < lookback:
            return 0.0
        
        recent = data[-lookback:]
        range_high = max(c['high'] for c in recent)
        range_low = min(c['low'] for c in recent)
        current = data[-1]['close']
        
        return (range_high - range_low) / current if current > 0 else 0.0
    
    def calculate_atr(self, data: List[dict], period: int = 14) -> float:
        """Calculate ATR"""
        if len(data) < 2:
            return 0.0
        
        n = len(data)
        tr_list = [0.0]
        
        for i in range(1, n):
            high = data[i]['high']
            low = data[i]['low']
            prev_close = data[i-1]['close']
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_list.append(tr)
        
        if n <= period:
            return sum(tr_list) / len(tr_list) if tr_list else 0.0
        
        # SMA seed
        seed = sum(tr_list[1:period+1]) / period
        atr = [0.0] * period + [seed]
        
        # Wilder smoothing
        for i in range(period + 1, n):
            atr.append((atr[-1] * (period - 1) + tr_list[i]) / period)
        
        return atr[-1] if atr else 0.0
    
    # ============================================================
    # STEP TF.2: Regime Classification
    # ============================================================
    
    def classify_regime(self, metrics: TFMetrics, prev_regime: Optional[Regime] = None) -> Regime:
        """
        Classify market regime based on exact rules
        """
        s = metrics.structure_score
        e = metrics.ema_alignment
        m = metrics.momentum
        r = metrics.range_pct
        close = metrics.close
        
        # Check for BREAKOUT/BREAKDOWN first (requires previous RANGE)
        if prev_regime == Regime.RANGE:
            # Would need displacement candle check here
            # Simplified: check if outside range
            pass  # Implement with actual range data
        
        # TREND_BULL
        if r <= 0.10 and s > 0.50 and e > 0.40 and m > 0.20:
            return Regime.TREND_BULL
        
        # TREND_BEAR
        if r <= 0.10 and s < -0.50 and e < -0.40 and m < -0.20:
            return Regime.TREND_BEAR
        
        # PULLBACK_BULL
        if s > 0.30 and e > 0.20 and m < -0.20:
            if metrics.last_higher_low and close > metrics.last_higher_low:
                return Regime.PULLBACK_BULL
        
        # PULLBACK_BEAR
        if s < -0.30 and e < -0.20 and m > 0.20:
            if metrics.last_lower_high and close < metrics.last_lower_high:
                return Regime.PULLBACK_BEAR
        
        # RANGE
        if r >= 0.15 and abs(s) < 0.30 and abs(e) < 0.30:
            # Check for drift
            if s > 0.10 and m > 0.10:
                return Regime.RANGE_BULL_DRIFT
            if s < -0.10 and m < -0.10:
                return Regime.RANGE_BEAR_DRIFT
            return Regime.RANGE
        
        # TRANSITIONAL
        if 0.10 <= r < 0.15:
            return Regime.TRANSITIONAL
        
        return Regime.UNKNOWN
    
    # ============================================================
    # STEP TF.3: Direction Assignment
    # ============================================================
    
    def assign_direction(self, regime: Regime) -> int:
        """Assign direction based on regime"""
        if regime in [Regime.TREND_BULL, Regime.BREAKOUT, Regime.PULLBACK_BULL]:
            return 1
        if regime in [Regime.TREND_BEAR, Regime.BREAKDOWN, Regime.PULLBACK_BEAR]:
            return -1
        return 0
    
    # ============================================================
    # STEP TF.4: Strength and Confidence
    # ============================================================
    
    def calculate_strength(self, metrics: TFMetrics, regime: Regime) -> float:
        """Calculate strength with regime penalty"""
        base = (
            0.45 * abs(metrics.structure_score) +
            0.35 * abs(metrics.ema_alignment) +
            0.20 * abs(metrics.momentum)
        )
        base = min(1.0, base)
        
        # Regime penalties
        penalties = {
            Regime.PULLBACK_BULL: 0.75,
            Regime.PULLBACK_BEAR: 0.75,
            Regime.RANGE: 0.50,
            Regime.RANGE_BULL_DRIFT: 0.50,
            Regime.RANGE_BEAR_DRIFT: 0.50,
            Regime.TRANSITIONAL: 0.60,
            Regime.UNKNOWN: 0.0
        }
        
        return base * penalties.get(regime, 1.0)
    
    def calculate_confidence(self, metrics: TFMetrics) -> float:
        """Calculate confidence"""
        conf = (
            0.40 * abs(metrics.structure_score) +
            0.30 * abs(metrics.ema_alignment) +
            0.30 * abs(metrics.momentum)
        )
        return min(1.0, conf)
    
    # ============================================================
    # Main Analysis Function
    # ============================================================
    
    def analyze_timeframe(self, symbol: str, interval: str, 
                         prev_regime: Optional[Regime] = None) -> Optional[TFAnalysis]:
        """
        Complete timeframe analysis (Steps TF.0 - TF.4)
        """
        # Load data
        filepath = self.data_dir / symbol / f"{interval}.csv"
        if not filepath.exists():
            return None
        
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
        
        # Validate minimum candles
        lookback = TF_LOOKBACKS.get(interval, 50)
        if len(data) < lookback:
            return None
        
        # Calculate metrics
        structure_score, levels = self.calculate_structure(data, lookback)
        ema_alignment = self.calculate_ema_alignment(data)
        momentum = self.calculate_momentum(data)
        range_pct = self.calculate_range_pct(data, lookback)
        atr = self.calculate_atr(data)
        
        metrics = TFMetrics(
            structure_score=structure_score,
            ema_alignment=ema_alignment,
            momentum=momentum,
            range_pct=range_pct,
            atr_pct=atr / data[-1]['close'] if data[-1]['close'] > 0 else 0,
            close=data[-1]['close'],
            **levels
        )
        
        # Classify regime
        regime = self.classify_regime(metrics, prev_regime)
        
        # Assign direction
        direction = self.assign_direction(regime)
        
        # Calculate strength and confidence
        strength = self.calculate_strength(metrics, regime)
        confidence = self.calculate_confidence(metrics)
        
        # Extract key levels
        key_levels = {
            'swing_high': metrics.last_swing_high,
            'swing_low': metrics.last_swing_low,
            'higher_low': metrics.last_higher_low,
            'lower_high': metrics.last_lower_high,
            'close': metrics.close
        }
        
        return TFAnalysis(
            regime=regime,
            direction=direction,
            strength=strength,
            confidence=confidence,
            metrics=metrics,
            key_levels=key_levels
        )


if __name__ == '__main__':
    # Test
    engine = MTFEngine(Path('/root/.openclaw/workspace/data/binance'))
    result = engine.analyze_timeframe('BTCUSDT', '1d')
    if result:
        print(f"Regime: {result.regime.value}")
        print(f"Direction: {result.direction}")
        print(f"Strength: {result.strength:.2f}")
        print(f"Confidence: {result.confidence:.2f}")
