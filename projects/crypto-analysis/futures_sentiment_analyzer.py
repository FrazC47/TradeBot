#!/usr/bin/env python3
"""
Futures Market Sentiment Analyzer
Analyzes Open Interest, Funding Rates, and Long/Short ratios for market sentiment insights.

Key Metrics:
- Funding > 0.05% = overheated, < -0.05% = oversold
- OI increase > 10% in 1h = significant new positions
- L/S ratio > 3 = retail heavy long, < 0.5 = retail heavy short
"""

import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import statistics

# Configuration
COMPASS_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/analysis/compass')
SENTIMENT_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/analysis/sentiment')
FUTURES_DATA_DIR = Path('/root/.openclaw/workspace/data/binance_futures')
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']

@dataclass
class FuturesMetrics:
    """Container for futures metrics"""
    symbol: str
    timestamp: str
    oi: float
    oi_value: float
    funding_rate: float
    mark_price: float
    long_account: float
    short_account: float
    ls_ratio: float

@dataclass
class SentimentReading:
    """Container for sentiment analysis"""
    symbol: str
    timestamp: str
    
    # Funding sentiment
    funding_rate: float
    funding_sentiment: str  # 'overheated', 'neutral', 'oversold'
    
    # OI sentiment
    oi: float
    oi_change_1h: float
    oi_sentiment: str  # 'increasing', 'stable', 'decreasing'
    
    # L/S sentiment
    ls_ratio: float
    ls_sentiment: str  # 'retail_long', 'balanced', 'retail_short'
    
    # Composite
    overall_sentiment: str  # 'bullish', 'neutral', 'bearish'
    liquidation_risk: str  # 'high_long', 'moderate', 'high_short'
    confidence: int  # 0-100

class FuturesSentimentAnalyzer:
    """Analyzes futures market sentiment"""
    
    def __init__(self):
        self.sentiment_history: Dict[str, List[SentimentReading]] = {s: [] for s in SYMBOLS}
        SENTIMENT_DIR.mkdir(parents=True, exist_ok=True)
    
    def load_latest_compass_data(self, symbol: str) -> Optional[FuturesMetrics]:
        """Load the most recent COMPASS analysis file for a symbol"""
        # Find the most recent file for this symbol
        files = sorted(COMPASS_DIR.glob(f"{symbol}_compass_*.json"), reverse=True)
        if not files:
            return None
        
        try:
            with open(files[0], 'r') as f:
                data = json.load(f)
            
            futures = data.get('futures_data', {})
            return FuturesMetrics(
                symbol=symbol,
                timestamp=data.get('timestamp', datetime.now().isoformat()),
                oi=futures.get('oi', 0),
                oi_value=futures.get('oi_value', 0),
                funding_rate=futures.get('funding_rate', 0),
                mark_price=futures.get('mark_price', 0),
                long_account=futures.get('long_account', 0.5),
                short_account=futures.get('short_account', 0.5),
                ls_ratio=futures.get('ls_ratio', 1.0)
            )
        except Exception as e:
            print(f"Error loading {symbol} data: {e}")
            return None
    
    def get_oi_change(self, symbol: str, current_oi: float, hours: int = 1) -> float:
        """Calculate OI change over specified hours"""
        # Look back at historical files
        cutoff = datetime.now() - timedelta(hours=hours)
        files = sorted(COMPASS_DIR.glob(f"{symbol}_compass_*.json"))
        
        for f in reversed(files[:-1]):  # Skip the most recent
            try:
                # Parse timestamp from filename
                ts_str = f.stem.split('_')[2]  # YYYYMMDD_HHMM
                file_ts = datetime.strptime(ts_str, "%Y%m%d_%H%M")
                
                if file_ts <= cutoff:
                    with open(f, 'r') as file:
                        data = json.load(file)
                    old_oi = data.get('futures_data', {}).get('oi', 0)
                    if old_oi > 0:
                        return ((current_oi - old_oi) / old_oi) * 100
            except:
                continue
        
        return 0.0
    
    def analyze_funding(self, rate: float) -> Tuple[str, int]:
        """
        Analyze funding rate sentiment
        Returns: (sentiment_label, confidence_impact)
        """
        rate_pct = rate * 100  # Convert to percentage
        
        if rate_pct > 0.05:
            return ('overheated', -20)  # Overleveraged longs
        elif rate_pct > 0.01:
            return ('elevated_longs', -10)
        elif rate_pct < -0.05:
            return ('oversold', 20)  # Shorts paying, potential bounce
        elif rate_pct < -0.01:
            return ('elevated_shorts', 10)
        else:
            return ('neutral', 0)
    
    def analyze_oi(self, oi: float, change_pct: float) -> Tuple[str, int]:
        """
        Analyze Open Interest sentiment
        Returns: (sentiment_label, confidence_impact)
        """
        if abs(change_pct) > 10:
            if change_pct > 0:
                return ('significant_increase', 15)  # New positions opening
            else:
                return ('significant_decrease', -10)  # Positions closing
        elif abs(change_pct) > 5:
            if change_pct > 0:
                return ('increasing', 5)
            else:
                return ('decreasing', -5)
        else:
            return ('stable', 0)
    
    def analyze_ls_ratio(self, ratio: float) -> Tuple[str, int]:
        """
        Analyze Long/Short ratio sentiment
        Returns: (sentiment_label, confidence_impact)
        """
        if ratio > 3.0:
            return ('retail_heavy_long', -25)  # Contrarian bearish signal
        elif ratio > 2.0:
            return ('long_bias', -10)
        elif ratio < 0.5:
            return ('retail_heavy_short', 25)  # Contrarian bullish signal
        elif ratio < 0.8:
            return ('short_bias', 10)
        else:
            return ('balanced', 0)
    
    def calculate_liquidation_risk(self, funding_sent: str, ls_sent: str, oi_sent: str) -> str:
        """Calculate liquidation risk based on positioning"""
        risk_score = 0
        
        # Funding contribution
        if funding_sent == 'overheated':
            risk_score += 3
        elif funding_sent == 'elevated_longs':
            risk_score += 1
        elif funding_sent == 'oversold':
            risk_score -= 3
        elif funding_sent == 'elevated_shorts':
            risk_score -= 1
        
        # L/S ratio contribution
        if ls_sent == 'retail_heavy_long':
            risk_score += 3
        elif ls_sent == 'long_bias':
            risk_score += 1
        elif ls_sent == 'retail_heavy_short':
            risk_score -= 3
        elif ls_sent == 'short_bias':
            risk_score -= 1
        
        # OI contribution (high OI + extreme positioning = danger)
        if oi_sent in ['significant_increase', 'increasing']:
            risk_score = risk_score * 1.5  # Amplify risk with new positions
        
        if risk_score >= 4:
            return 'high_long'
        elif risk_score >= 2:
            return 'moderate_long'
        elif risk_score <= -4:
            return 'high_short'
        elif risk_score <= -2:
            return 'moderate_short'
        else:
            return 'low'
    
    def calculate_overall_sentiment(self, funding_sent: str, ls_sent: str, oi_sent: str, 
                                   base_confidence: int) -> Tuple[str, int]:
        """Calculate overall market sentiment"""
        sentiment_score = base_confidence
        
        # Funding rate signals (contrarian)
        if funding_sent == 'overheated':
            sentiment_score -= 30  # Bearish - overleveraged longs
        elif funding_sent == 'oversold':
            sentiment_score += 30  # Bullish - oversold conditions
        
        # L/S ratio signals (contrarian)
        if ls_sent == 'retail_heavy_long':
            sentiment_score -= 25  # Bearish - retail is wrong at extremes
        elif ls_sent == 'retail_heavy_short':
            sentiment_score += 25  # Bullish - retail is wrong at extremes
        
        # OI signals (momentum)
        if oi_sent == 'significant_increase':
            sentiment_score += 10  # New money entering
        elif oi_sent == 'significant_decrease':
            sentiment_score -= 10  # Capitulation or profit taking
        
        # Determine sentiment label
        if sentiment_score > 20:
            overall = 'bullish'
        elif sentiment_score < -20:
            overall = 'bearish'
        else:
            overall = 'neutral'
        
        # Clamp confidence
        confidence = max(0, min(100, 50 + abs(sentiment_score)))
        
        return overall, confidence
    
    def analyze_symbol(self, symbol: str) -> Optional[SentimentReading]:
        """Perform full sentiment analysis for a symbol"""
        metrics = self.load_latest_compass_data(symbol)
        if not metrics:
            return None
        
        # Calculate OI change
        oi_change = self.get_oi_change(symbol, metrics.oi, hours=1)
        
        # Analyze components
        funding_sent, funding_conf = self.analyze_funding(metrics.funding_rate)
        oi_sent, oi_conf = self.analyze_oi(metrics.oi, oi_change)
        ls_sent, ls_conf = self.analyze_ls_ratio(metrics.ls_ratio)
        
        # Calculate base confidence
        base_confidence = funding_conf + oi_conf + ls_conf
        
        # Calculate overall sentiment
        overall, confidence = self.calculate_overall_sentiment(
            funding_sent, ls_sent, oi_sent, base_confidence
        )
        
        # Calculate liquidation risk
        liq_risk = self.calculate_liquidation_risk(funding_sent, ls_sent, oi_sent)
        
        return SentimentReading(
            symbol=symbol,
            timestamp=metrics.timestamp,
            funding_rate=metrics.funding_rate,
            funding_sentiment=funding_sent,
            oi=metrics.oi,
            oi_change_1h=oi_change,
            oi_sentiment=oi_sent,
            ls_ratio=metrics.ls_ratio,
            ls_sentiment=ls_sent,
            overall_sentiment=overall,
            liquidation_risk=liq_risk,
            confidence=confidence
        )
    
    def detect_divergences(self, readings: List[SentimentReading]) -> List[Dict]:
        """Detect price-OI divergences and other anomalies"""
        divergences = []
        
        for r in readings:
            # Price up + OI down = weak move (shorts closing, not new buying)
            # Price down + OI up = accumulation (new shorts opening or longs adding)
            
            if r.oi_sentiment == 'significant_decrease' and r.overall_sentiment == 'bullish':
                divergences.append({
                    'symbol': r.symbol,
                    'type': 'weak_rally',
                    'description': f"Price strength with OI decreasing - likely short covering, not new buying",
                    'severity': 'medium'
                })
            
            if r.oi_sentiment == 'significant_increase' and r.overall_sentiment == 'bearish':
                divergences.append({
                    'symbol': r.symbol,
                    'type': 'accumulation',
                    'description': f"Price weakness with OI increasing - new positions opening",
                    'severity': 'high' if r.ls_sentiment == 'retail_heavy_short' else 'medium'
                })
            
            # Funding extreme with price flat = impending move
            if r.funding_sentiment == 'overheated' and r.overall_sentiment == 'neutral':
                divergences.append({
                    'symbol': r.symbol,
                    'type': 'funding_extreme',
                    'description': f"Overheated funding ({r.funding_rate*100:.4f}%) with neutral price - liquidation risk",
                    'severity': 'high'
                })
        
        return divergences
    
    def generate_sentiment_report(self) -> str:
        """Generate a comprehensive sentiment report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        readings = []
        
        for symbol in SYMBOLS:
            reading = self.analyze_symbol(symbol)
            if reading:
                readings.append(reading)
                self.sentiment_history[symbol].append(reading)
        
        divergences = self.detect_divergences(readings)
        
        # Build report
        report_lines = [
            "# Futures Market Sentiment Analysis",
            f"**Report Time:** {timestamp} (Asia/Shanghai)",
            f"**Analyst:** Futures Market Sentiment Agent",
            "",
            "---",
            "",
            "## Market Overview",
            "",
        ]
        
        # Summary table
        report_lines.extend([
            "| Symbol | Sentiment | Confidence | Funding | OI Change | L/S Ratio | Liquidation Risk |",
            "|--------|-----------|------------|---------|-----------|-----------|------------------|",
        ])
        
        for r in readings:
            funding_emoji = {
                'overheated': '🔴', 'elevated_longs': '🟠',
                'neutral': '⚪', 'elevated_shorts': '🔵', 'oversold': '🟢'
            }.get(r.funding_sentiment, '⚪')
            
            sentiment_emoji = {
                'bullish': '🟢', 'neutral': '⚪', 'bearish': '🔴'
            }.get(r.overall_sentiment, '⚪')
            
            liq_emoji = {
                'high_long': '🔴🚀', 'moderate_long': '🟠',
                'low': '🟢', 'moderate_short': '🔵', 'high_short': '🟢💥'
            }.get(r.liquidation_risk, '⚪')
            
            report_lines.append(
                f"| {r.symbol} | {sentiment_emoji} {r.overall_sentiment.upper()} | {r.confidence}% | "
                f"{funding_emoji} {r.funding_rate*100:.4f}% | {r.oi_change_1h:+.1f}% | "
                f"{r.ls_ratio:.2f} | {liq_emoji} |"
            )
        
        report_lines.extend([
            "",
            "---",
            "",
            "## Detailed Analysis",
            "",
        ])
        
        # Individual symbol analysis
        for r in readings:
            report_lines.extend([
                f"### {r.symbol}",
                "",
                f"**Overall Sentiment:** {r.overall_sentiment.upper()} (Confidence: {r.confidence}%)",
                "",
                "#### Funding Rate Analysis",
                f"- **Current Rate:** {r.funding_rate*100:.4f}%",
                f"- **Status:** {r.funding_sentiment.replace('_', ' ').title()}",
                f"- **Interpretation:** {self._funding_interpretation(r.funding_sentiment)}",
                "",
                "#### Open Interest Analysis",
                f"- **Current OI:** {r.oi:,.0f} contracts (${r.oi/1000000:.1f}M notional)",
                f"- **1h Change:** {r.oi_change_1h:+.1f}%",
                f"- **Status:** {r.oi_sentiment.replace('_', ' ').title()}",
                f"- **Interpretation:** {self._oi_interpretation(r.oi_sentiment)}",
                "",
                "#### Long/Short Ratio Analysis",
                f"- **Current Ratio:** {r.ls_ratio:.2f} (Longs: {r.ls_ratio/(1+r.ls_ratio)*100:.1f}%)",
                f"- **Status:** {r.ls_sentiment.replace('_', ' ').title()}",
                f"- **Interpretation:** {self._ls_interpretation(r.ls_sentiment)}",
                "",
                "#### Liquidation Risk",
                f"- **Risk Level:** {r.liquidation_risk.replace('_', ' ').title()}",
                f"- **Warning:** {self._liq_warning(r.liquidation_risk)}",
                "",
                "---",
                "",
            ])
        
        # Divergences section
        if divergences:
            report_lines.extend([
                "## 🚨 Divergence Alerts",
                "",
            ])
            for d in divergences:
                emoji = '🔴' if d['severity'] == 'high' else '🟠'
                report_lines.append(f"{emoji} **{d['symbol']}** - {d['type'].replace('_', ' ').title()}")
                report_lines.append(f"   {d['description']}")
                report_lines.append("")
        
        # Key metrics reference
        report_lines.extend([
            "## Key Metrics Reference",
            "",
            "| Metric | Bullish Signal | Bearish Signal |",
            "|--------|---------------|----------------|",
            "| Funding Rate | < -0.05% (oversold) | > 0.05% (overheated) |",
            "| OI Change | +10% in 1h (new positions) | -10% in 1h (capitulation) |",
            "| L/S Ratio | < 0.5 (retail short) | > 3.0 (retail long) |",
            "",
            "---",
            "",
            "*This analysis is for informational purposes only. Not financial advice.*",
            "",
            f"*Next update: ~15 minutes*",
        ])
        
        return '\n'.join(report_lines)
    
    def _funding_interpretation(self, sentiment: str) -> str:
        interpretations = {
            'overheated': 'Longs are paying high funding - overleveraged, prone to liquidation cascades',
            'elevated_longs': 'Moderate long bias in funding - slight caution warranted',
            'neutral': 'Funding is balanced - no extreme positioning detected',
            'elevated_shorts': 'Shorts paying funding - slight bullish contrarian signal',
            'oversold': 'Shorts paying high funding - potential for short squeeze'
        }
        return interpretations.get(sentiment, 'Unknown')
    
    def _oi_interpretation(self, sentiment: str) -> str:
        interpretations = {
            'significant_increase': 'Large new positions opening - watch for momentum continuation',
            'increasing': 'New money entering the market',
            'stable': 'Open interest unchanged - consolidation phase',
            'decreasing': 'Positions closing - possible profit taking or capitulation',
            'significant_decrease': 'Large position unwind - potential reversal or consolidation'
        }
        return interpretations.get(sentiment, 'Unknown')
    
    def _ls_interpretation(self, sentiment: str) -> str:
        interpretations = {
            'retail_heavy_long': 'Retail heavily long - contrarian bearish signal',
            'long_bias': 'More longs than shorts - slight caution',
            'balanced': 'Long/Short ratio neutral',
            'short_bias': 'More shorts than longs - slight bullish contrarian',
            'retail_heavy_short': 'Retail heavily short - contrarian bullish signal'
        }
        return interpretations.get(sentiment, 'Unknown')
    
    def _liq_warning(self, risk: str) -> str:
        warnings = {
            'high_long': '⚠️ HIGH RISK: Overleveraged longs vulnerable to cascade liquidation',
            'moderate_long': 'Caution: Long bias with moderate liquidation risk',
            'low': 'Low liquidation risk - positioning is balanced',
            'moderate_short': 'Caution: Short bias with moderate squeeze risk',
            'high_short': '⚠️ HIGH RISK: Overleveraged shorts vulnerable to short squeeze'
        }
        return warnings.get(risk, 'Unknown')
    
    def save_report(self, report: str):
        """Save the sentiment report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filepath = SENTIMENT_DIR / f"sentiment_{timestamp}.md"
        
        with open(filepath, 'w') as f:
            f.write(report)
        
        # Also save as latest
        latest_path = SENTIMENT_DIR / "latest_sentiment.md"
        with open(latest_path, 'w') as f:
            f.write(report)
        
        return filepath
    
    def check_extreme_conditions(self) -> List[Dict]:
        """Check for extreme market conditions that need immediate alerts"""
        alerts = []
        
        for symbol in SYMBOLS:
            reading = self.analyze_symbol(symbol)
            if not reading:
                continue
            
            # Extreme funding
            if abs(reading.funding_rate) > 0.0005:  # 0.05%
                alerts.append({
                    'symbol': symbol,
                    'type': 'extreme_funding',
                    'message': f"{symbol}: Extreme funding rate {reading.funding_rate*100:.4f}%",
                    'severity': 'high' if abs(reading.funding_rate) > 0.001 else 'medium'
                })
            
            # Extreme L/S ratio
            if reading.ls_ratio > 3.0 or reading.ls_ratio < 0.5:
                alerts.append({
                    'symbol': symbol,
                    'type': 'extreme_positioning',
                    'message': f"{symbol}: Extreme L/S ratio {reading.ls_ratio:.2f}",
                    'severity': 'high' if reading.ls_ratio > 4.0 or reading.ls_ratio < 0.33 else 'medium'
                })
            
            # High liquidation risk
            if reading.liquidation_risk in ['high_long', 'high_short']:
                alerts.append({
                    'symbol': symbol,
                    'type': 'liquidation_risk',
                    'message': f"{symbol}: High liquidation risk - {reading.liquidation_risk}",
                    'severity': 'high'
                })
        
        return alerts

def main():
    """Main entry point"""
    analyzer = FuturesSentimentAnalyzer()
    
    print("="*70)
    print("Futures Market Sentiment Analyzer")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Generate report
    report = analyzer.generate_sentiment_report()
    
    # Save report
    filepath = analyzer.save_report(report)
    print(f"\n✓ Sentiment report saved: {filepath}")
    
    # Check for extreme conditions
    alerts = analyzer.check_extreme_conditions()
    if alerts:
        print("\n" + "="*70)
        print("⚠️  EXTREME CONDITIONS DETECTED")
        print("="*70)
        for alert in alerts:
            emoji = '🔴' if alert['severity'] == 'high' else '🟠'
            print(f"{emoji} [{alert['type'].upper()}] {alert['message']}")
    else:
        print("\n✓ No extreme conditions detected")
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    for symbol in SYMBOLS:
        reading = analyzer.analyze_symbol(symbol)
        if reading:
            emoji = {'bullish': '🟢', 'neutral': '⚪', 'bearish': '🔴'}.get(reading.overall_sentiment, '⚪')
            print(f"{symbol}: {emoji} {reading.overall_sentiment.upper()} (conf: {reading.confidence}%)")
    
    return report

if __name__ == '__main__':
    main()
