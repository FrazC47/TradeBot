#!/usr/bin/env python3
"""
Professional MTF Analysis Engine
Sequential analysis with regime detection and state management
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/projects/crypto-analysis/core')

from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import json

from regime_detector import RegimeDetector, MarketRegime
from weighted_mtf_scorer import WeightedMTFScorer, TrendDirection
from signal_state_machine import SignalStateMachine, SignalType

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
OUTPUT_DIR = Path('/root/.openclaw/workspace/mtf_analysis')

ANALYSIS_SEQUENCE = ['1M', '1w', '1d', '4h', '1h', '15m', '5m']

MIN_CANDLES = {
    '1M': 24, '1w': 52, '1d': 50, '4h': 100,
    '1h': 100, '15m': 100, '5m': 100
}


class ProfessionalMTFEngine:
    def __init__(self):
        self.regime_detector = RegimeDetector(lookback=20)
        self.mtf_scorer = WeightedMTFScorer()
        self.signal_machine = SignalStateMachine(cooldown_minutes=120)
        self.results = {}
    
    def load_timeframe_data(self, symbol: str, timeframe: str) -> Optional[list]:
        filepath = DATA_DIR / symbol / f"{timeframe}.csv"
        if not filepath.exists():
            return None
        try:
            import csv
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                data = []
                for row in reader:
                    data.append({
                        'open': float(row['open']), 'high': float(row['high']),
                        'low': float(row['low']), 'close': float(row['close']),
                        'volume': float(row['volume'])
                    })
                if len(data) < MIN_CANDLES.get(timeframe, 50):
                    return None
                return data
        except:
            return None
    
    def analyze_timeframe(self, symbol: str, timeframe: str, data: list) -> Dict:
        regime_ctx = self.regime_detector.detect(data)
        
        if regime_ctx.regime in [MarketRegime.TREND_BULL, MarketRegime.PULLBACK_BULL]:
            direction = TrendDirection.BULLISH
        elif regime_ctx.regime in [MarketRegime.TREND_BEAR, MarketRegime.PULLBACK_BEAR]:
            direction = TrendDirection.BEARISH
        else:
            direction = TrendDirection.NEUTRAL
        
        return {
            'timeframe': timeframe, 'regime': regime_ctx.regime.value,
            'direction': direction.name, 'strength': regime_ctx.strength,
            'confidence': regime_ctx.confidence, 'key_level': regime_ctx.key_level,
            'current_price': data[-1]['close'], 'structure_broken': regime_ctx.structure_broken
        }
    
    def run_analysis(self, symbol: str) -> Dict:
        print(f"\n{'='*70}")
        print(f"PROFESSIONAL MTF ANALYSIS: {symbol}")
        print('='*70)
        
        # Step 1: Load data
        print("\n[Step 1] Loading timeframe data...")
        timeframe_data = {}
        for tf in ANALYSIS_SEQUENCE:
            data = self.load_timeframe_data(symbol, tf)
            if data:
                timeframe_data[tf] = data
                print(f"  {tf}: {len(data)} candles")
        
        if len(timeframe_data) < 4:
            return {'error': 'Insufficient data'}
        
        # Step 2: Analyze timeframes
        print("\n[Step 2] Analyzing timeframes (top-down)...")
        timeframe_analysis = {}
        for tf in ANALYSIS_SEQUENCE:
            if tf not in timeframe_data:
                continue
            analysis = self.analyze_timeframe(symbol, tf, timeframe_data[tf])
            timeframe_analysis[tf] = analysis
            emoji = "📈" if analysis['direction'] == 'BULLISH' else "📉" if analysis['direction'] == 'BEARISH' else "➖"
            print(f"  {tf:3s}: {emoji} {analysis['direction']:8s} | Regime: {analysis['regime']:15s} | Str: {analysis['strength']:.2f}")
        
        # Step 3: Weighted MTF score
        print("\n[Step 3] Calculating weighted MTF score...")
        for tf, analysis in timeframe_analysis.items():
            self.mtf_scorer.add_timeframe(tf, TrendDirection[analysis['direction']], 
                                          analysis['strength'], analysis['regime'], analysis['confidence'])
        
        mtf = self.mtf_scorer.calculate()
        print(f"  Macro: {mtf.macro_score:+.3f} | Intermediate: {mtf.intermediate_score:+.3f} | Execution: {mtf.execution_score:+.3f}")
        print(f"  Overall: {mtf.overall_score:+.3f} | Direction: {mtf.overall_direction.name} | Confidence: {mtf.confidence:.1%}")
        print(f"  Tradeable: {'YES' if mtf.is_tradeable() else 'NO'}")
        
        return {
            'symbol': symbol, 'timestamp': datetime.now().isoformat(),
            'timeframe_analysis': timeframe_analysis,
            'mtf_score': {
                'macro': mtf.macro_score, 'intermediate': mtf.intermediate_score,
                'execution': mtf.execution_score, 'overall': mtf.overall_score,
                'direction': mtf.overall_direction.name, 'confidence': mtf.confidence,
                'tradeable': mtf.is_tradeable()
            }
        }


if __name__ == "__main__":
    engine = ProfessionalMTFEngine()
    result = engine.run_analysis('BTCUSDT')
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / 'professional_mtf_result.json', 'w') as f:
        json.dump(result, f, indent=2)
