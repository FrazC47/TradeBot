#!/usr/bin/env python3
"""
Futures Sentiment Monitor
Runs every 15 minutes to check futures data and alert on extreme conditions.
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/projects/crypto-analysis')

from futures_sentiment_analyzer import FuturesSentimentAnalyzer
from datetime import datetime
import json

def main():
    """Run the sentiment monitor"""
    analyzer = FuturesSentimentAnalyzer()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Running futures sentiment check...")
    
    # Generate report
    report = analyzer.generate_sentiment_report()
    filepath = analyzer.save_report(report)
    print(f"  ✓ Report saved: {filepath.name}")
    
    # Check for extreme conditions
    alerts = analyzer.check_extreme_conditions()
    
    if alerts:
        print(f"\n  ⚠️  {len(alerts)} ALERT(S) DETECTED:")
        for alert in alerts:
            emoji = '🔴' if alert['severity'] == 'high' else '🟠'
            print(f"     {emoji} {alert['symbol']}: {alert['message']}")
    else:
        print("  ✓ No extreme conditions")
    
    # Print quick summary
    print("\n  Current Sentiment:")
    for symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']:
        reading = analyzer.analyze_symbol(symbol)
        if reading:
            emoji = {'bullish': '🟢', 'neutral': '⚪', 'bearish': '🔴'}.get(reading.overall_sentiment, '⚪')
            print(f"    {symbol}: {emoji} {reading.overall_sentiment.upper()} (funding: {reading.funding_rate*100:+.4f}%, L/S: {reading.ls_ratio:.2f})")
    
    return len(alerts)

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
