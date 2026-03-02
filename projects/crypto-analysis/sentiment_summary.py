#!/usr/bin/env python3
"""
Futures Sentiment Summary Generator
Generates 2-hour summary reports with trend analysis.
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/projects/crypto-analysis')

from futures_sentiment_analyzer import FuturesSentimentAnalyzer, SENTIMENT_DIR
from datetime import datetime, timedelta
from pathlib import Path
import json
import re

class SentimentSummaryGenerator:
    """Generates periodic sentiment summaries"""
    
    def __init__(self):
        self.analyzer = FuturesSentimentAnalyzer()
        self.readings_history = []
    
    def load_recent_readings(self, hours: int = 2):
        """Load sentiment readings from the last N hours"""
        readings = {s: [] for s in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']}
        
        # Get all sentiment files from the last N hours
        cutoff = datetime.now() - timedelta(hours=hours)
        
        for filepath in sorted(SENTIMENT_DIR.glob("sentiment_*.md")):
            try:
                # Parse timestamp from filename
                ts_str = filepath.stem.split('_')[1] + '_' + filepath.stem.split('_')[2]
                file_ts = datetime.strptime(ts_str, "%Y%m%d_%H%M")
                
                if file_ts >= cutoff:
                    # Parse the file for each symbol's data
                    with open(filepath, 'r') as f:
                        content = f.read()
                    
                    # Extract data for each symbol (simple parsing)
                    for symbol in readings.keys():
                        if symbol in content:
                            readings[symbol].append({
                                'timestamp': file_ts,
                                'filepath': filepath
                            })
            except:
                continue
        
        return readings
    
    def calculate_trends(self, symbol: str, hours: int = 2):
        """Calculate sentiment trends over time"""
        # Get current reading
        current = self.analyzer.analyze_symbol(symbol)
        if not current:
            return None
        
        # Get readings from 2 hours ago
        old_files = sorted(SENTIMENT_DIR.glob("sentiment_*.md"))
        old_reading = None
        cutoff = datetime.now() - timedelta(hours=hours)
        
        for f in old_files:
            try:
                ts_str = f.stem.split('_')[1] + '_' + f.stem.split('_')[2]
                file_ts = datetime.strptime(ts_str, "%Y%m%d_%H%M")
                if file_ts <= cutoff:
                    # This would need more sophisticated parsing
                    # For now, we'll estimate based on current data
                    pass
            except:
                continue
        
        return {
            'current': current,
            'funding_trend': 'stable',  # Would calculate from history
            'oi_trend': 'stable',
            'ls_trend': 'stable'
        }
    
    def generate_summary(self) -> str:
        """Generate a 2-hour summary report"""
        now = datetime.now()
        period_start = now - timedelta(hours=2)
        
        lines = [
            f"# Futures Sentiment Summary ({period_start.strftime('%H:%M')} - {now.strftime('%H:%M')})",
            f"**Period:** {period_start.strftime('%Y-%m-%d %H:%M')} - {now.strftime('%H:%M')} (Asia/Shanghai)",
            "",
            "---",
            "",
            "## Market Sentiment Overview",
            "",
        ]
        
        # Overall market sentiment
        sentiments = []
        funding_extremes = []
        ls_extremes = []
        
        for symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']:
            reading = self.analyzer.analyze_symbol(symbol)
            if not reading:
                continue
            
            sentiments.append(reading.overall_sentiment)
            
            if abs(reading.funding_rate) > 0.0003:
                funding_extremes.append({
                    'symbol': symbol,
                    'rate': reading.funding_rate,
                    'direction': 'high' if reading.funding_rate > 0 else 'low'
                })
            
            if reading.ls_ratio > 2.5 or reading.ls_ratio < 0.6:
                ls_extremes.append({
                    'symbol': symbol,
                    'ratio': reading.ls_ratio,
                    'bias': 'long' if reading.ls_ratio > 1 else 'short'
                })
        
        # Market summary
        bullish_count = sentiments.count('bullish')
        bearish_count = sentiments.count('bearish')
        neutral_count = sentiments.count('neutral')
        
        if bullish_count > bearish_count and bullish_count > neutral_count:
            market_bias = "🟢 BULLISH BIAS"
        elif bearish_count > bullish_count and bearish_count > neutral_count:
            market_bias = "🔴 BEARISH BIAS"
        else:
            market_bias = "⚪ NEUTRAL"
        
        lines.extend([
            f"**Overall Market Bias:** {market_bias}",
            f"- Bullish: {bullish_count} | Neutral: {neutral_count} | Bearish: {bearish_count}",
            "",
        ])
        
        # Funding summary
        lines.extend([
            "### Funding Rate Summary",
            "",
        ])
        
        if funding_extremes:
            lines.append("⚠️ **Extreme Funding Detected:**")
            for e in funding_extremes:
                emoji = '🔴' if e['direction'] == 'high' else '🟢'
                lines.append(f"- {emoji} {e['symbol']}: {e['rate']*100:+.4f}%")
        else:
            lines.append("✓ Funding rates are within normal ranges")
        
        lines.append("")
        
        # L/S Ratio summary
        lines.extend([
            "### Long/Short Ratio Summary",
            "",
        ])
        
        if ls_extremes:
            lines.append("⚠️ **Extreme Positioning Detected:**")
            for e in ls_extremes:
                emoji = '🔴' if e['bias'] == 'long' else '🟢'
                lines.append(f"- {emoji} {e['symbol']}: {e['ratio']:.2f} ({e['bias'].upper()} bias)")
        else:
            lines.append("✓ L/S ratios are within normal ranges")
        
        lines.extend([
            "",
            "---",
            "",
            "## Individual Asset Summary",
            "",
        ])
        
        # Individual summaries
        for symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']:
            reading = self.analyzer.analyze_symbol(symbol)
            if not reading:
                continue
            
            emoji = {'bullish': '🟢', 'neutral': '⚪', 'bearish': '🔴'}.get(reading.overall_sentiment, '⚪')
            
            lines.extend([
                f"### {symbol}",
                "",
                f"**Sentiment:** {emoji} {reading.overall_sentiment.upper()} ({reading.confidence}% confidence)",
                "",
                "| Metric | Value | Signal |",
                "|--------|-------|--------|",
                f"| Funding Rate | {reading.funding_rate*100:.4f}% | {reading.funding_sentiment.replace('_', ' ').title()} |",
                f"| OI Change (1h) | {reading.oi_change_1h:+.1f}% | {reading.oi_sentiment.replace('_', ' ').title()} |",
                f"| L/S Ratio | {reading.ls_ratio:.2f} | {reading.ls_sentiment.replace('_', ' ').title()} |",
                f"| Liquidation Risk | {reading.liquidation_risk.replace('_', ' ').title()} | - |",
                "",
            ])
        
        # Key observations
        lines.extend([
            "---",
            "",
            "## Key Observations",
            "",
        ])
        
        observations = []
        
        for symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']:
            reading = self.analyzer.analyze_symbol(symbol)
            if not reading:
                continue
            
            # Check for liquidation risks
            if reading.liquidation_risk == 'high_long':
                observations.append(f"🔴 **{symbol}**: High long liquidation risk - overleveraged positioning")
            elif reading.liquidation_risk == 'high_short':
                observations.append(f"🟢 **{symbol}**: High short squeeze potential - shorts overextended")
            
            # Check for divergences
            if reading.oi_sentiment == 'significant_increase' and reading.overall_sentiment == 'bearish':
                observations.append(f"⚠️ **{symbol}**: Bearish price with rising OI - potential accumulation zone")
            elif reading.oi_sentiment == 'significant_decrease' and reading.overall_sentiment == 'bullish':
                observations.append(f"⚠️ **{symbol}**: Bullish price with falling OI - weak rally, short covering")
        
        if observations:
            for obs in observations:
                lines.append(f"- {obs}")
        else:
            lines.append("- No significant divergences or extreme conditions detected")
        
        lines.extend([
            "",
            "---",
            "",
            "## Action Items",
            "",
            "- [ ] Monitor funding rates for extreme moves (>0.05% or <-0.05%)",
            "- [ ] Watch for OI spikes (>10% in 1h) indicating new positions",
            "- [ ] Track L/S ratio extremes (>3.0 or <0.5) for contrarian signals",
            "- [ ] Alert on liquidation cascade conditions",
            "",
            "---",
            "",
            f"*Next summary: {(now + timedelta(hours=2)).strftime('%H:%M')}*",
            "",
            "*This analysis is for informational purposes only. Not financial advice.*",
        ])
        
        return '\n'.join(lines)
    
    def save_summary(self, summary: str):
        """Save the summary report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filepath = SENTIMENT_DIR / f"summary_{timestamp}.md"
        
        with open(filepath, 'w') as f:
            f.write(summary)
        
        # Also save as latest summary
        latest_path = SENTIMENT_DIR / "latest_summary.md"
        with open(latest_path, 'w') as f:
            f.write(summary)
        
        return filepath

def main():
    """Generate and save a 2-hour summary"""
    print("="*70)
    print("Futures Sentiment Summary Generator")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    generator = SentimentSummaryGenerator()
    summary = generator.generate_summary()
    filepath = generator.save_summary(summary)
    
    print(f"\n✓ Summary generated: {filepath}")
    print(f"\n{summary}")
    
    return filepath

if __name__ == '__main__':
    main()
