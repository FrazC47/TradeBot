#!/usr/bin/env python3
"""
COMPASS Alert System - Standalone Alert Generator
Generates alerts when COMPASS scores exceed thresholds
"""

import json
from pathlib import Path
from datetime import datetime
import subprocess

OUTPUT_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/analysis/compass')
ALERT_THRESHOLD = 60  # Minimum score to generate alert

def load_latest_summary():
    """Load the most recent COMPASS summary"""
    files = sorted(OUTPUT_DIR.glob('compass_summary_*.json'))
    if not files:
        return None
    
    with open(files[-1], 'r') as f:
        return json.load(f)

def generate_alert(symbol, data):
    """Generate human-readable alert"""
    score = data['compass_score']['total_score']
    signal = data['compass_score']['signal']
    confidence = data['compass_score']['confidence']
    alignment = data['compass_score']['alignment']
    
    trade_setup = data.get('trade_setup')
    futures = data.get('futures_data', {})
    
    emoji = '🚨' if score >= 75 else '🎯' if score >= 60 else '👀'
    
    msg = f"""
{emoji} COMPASS SIGNAL: {symbol} {signal}

📊 Analysis Summary:
├─ Signal: {signal} ({confidence} confidence)
├─ Score: {score:.1f}/100
└─ Alignment: {alignment}

📈 Timeframe Scores:
"""
    
    for tf, score_val in data['compass_score']['timeframe_scores'].items():
        status = '✅' if score_val > 20 else '❌' if score_val < -20 else '➖'
        msg += f"├─ {tf.upper()}: {score_val:+.0f} {status}\n"
    
    if trade_setup and signal != 'Flat':
        msg += f"""
🎯 Trade Setup:
├─ Entry: ${trade_setup['entry_zone'][0]:,.2f} - ${trade_setup['entry_zone'][1]:,.2f}
├─ Stop: ${trade_setup['stop_loss']:,.2f}
├─ Target 1: ${trade_setup['target_1']:,.2f} ({trade_setup['rr_ratio_1']})
└─ Target 2: ${trade_setup['target_2']:,.2f} ({trade_setup['rr_ratio_2']})
"""
    
    if futures:
        msg += f"""
📊 Futures Data:
├─ OI: {futures.get('oi', 'N/A'):,.0f}
├─ Funding: {futures.get('funding_rate', 0)*100:.4f}%
└─ L/S Ratio: {futures.get('ls_ratio', 'N/A')}
"""
    
    msg += """
⚠️ Required Confirmation:
   • Volume >1.5x baseline
   • Price action aligns with signal
   • No major news/events

✅ PRE-TRADE CHECKLIST:
□ Reviewed all timeframes
□ Volume confirmation visible
□ Stop loss set before entry
□ Position size matches 1% risk
□ Emotionally calm
"""
    
    return msg

def main():
    """Check for signals and generate alerts"""
    print("="*70)
    print("COMPASS Alert System")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    summary = load_latest_summary()
    if not summary:
        print("No analysis data found")
        return
    
    alerts_generated = 0
    
    for symbol, data in summary.items():
        score = data['compass_score']['total_score']
        signal = data['compass_score']['signal']
        
        print(f"\n{symbol}: Score={score:.1f}, Signal={signal}")
        
        if score >= ALERT_THRESHOLD and signal != 'Flat':
            alert_msg = generate_alert(symbol, data)
            print(f"  🎯 ALERT GENERATED (Score: {score:.1f})")
            
            # Save alert to file for pickup
            alert_file = Path('/root/.openclaw/workspace/compass_pending_alert.txt')
            with open(alert_file, 'w') as f:
                f.write(alert_msg)
            
            alerts_generated += 1
        else:
            print(f"  ⏸️  No alert (Score below threshold)")
    
    print(f"\n{'='*70}")
    print(f"Alerts generated: {alerts_generated}")
    print('='*70)

if __name__ == '__main__':
    main()
