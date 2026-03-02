#!/usr/bin/env python3
"""
COMPASS Signal Generator & Alert System
Generates trading signals based on COMPASS analysis and sends alerts
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

OUTPUT_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/analysis/compass')
ALERT_LOG = Path('/root/.openclaw/workspace/projects/crypto-analysis/analysis/compass/alerts.log')
TRADE_TRACKER = Path('/root/.openclaw/workspace/projects/crypto-analysis/analysis/compass/trade_tracker.csv')

# Alert thresholds
SCORE_THRESHOLD_HIGH = 75
SCORE_THRESHOLD_MEDIUM = 60
SCORE_THRESHOLD_LOW = 40

class CompassSignalGenerator:
    def __init__(self):
        self.signals = []
        self.load_trade_tracker()
    
    def load_trade_tracker(self):
        """Load or create trade tracking database"""
        if TRADE_TRACKER.exists():
            self.trade_df = pd.read_csv(TRADE_TRACKER)
        else:
            self.trade_df = pd.DataFrame(columns=[
                'trade_id', 'timestamp', 'symbol', 'signal', 'entry_zone_low',
                'entry_zone_high', 'stop_loss', 'target_1', 'target_2',
                'confidence', 'score', 'status', 'actual_entry', 'actual_exit',
                'pnl', 'notes'
            ])
    
    def load_latest_analysis(self, symbol):
        """Load most recent COMPASS analysis for symbol"""
        pattern = f"{symbol}_compass_*.json"
        files = sorted(OUTPUT_DIR.glob(pattern))
        if not files:
            return None
        
        with open(files[-1], 'r') as f:
            return json.load(f)
    
    def generate_signal(self, analysis):
        """Generate trading signal from analysis"""
        if not analysis:
            return None
        
        symbol = analysis['symbol']
        compass_score = analysis['compass_score']
        trade_setup = analysis.get('trade_setup')
        
        score = compass_score['total_score']
        signal = compass_score['signal']
        confidence = compass_score['confidence']
        
        # Determine alert level
        if score >= SCORE_THRESHOLD_HIGH and signal != 'Flat':
            alert_level = 'CRITICAL'
        elif score >= SCORE_THRESHOLD_MEDIUM and signal != 'Flat':
            alert_level = 'HIGH'
        elif score >= SCORE_THRESHOLD_LOW and signal != 'Flat':
            alert_level = 'MEDIUM'
        elif signal == 'Flat':
            alert_level = 'WATCH'
        else:
            alert_level = 'LOW'
        
        signal_data = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'alert_level': alert_level,
            'signal': signal,
            'confidence': confidence,
            'score': score,
            'alignment': compass_score['alignment'],
            'timeframe_scores': compass_score['timeframe_scores'],
            'trade_setup': trade_setup,
            'futures_data': analysis.get('futures_data', {})
        }
        
        return signal_data
    
    def format_alert_message(self, signal):
        """Format signal for human-readable alert"""
        symbol = signal['symbol']
        alert_level = signal['alert_level']
        trade_setup = signal.get('trade_setup')
        futures = signal.get('futures_data', {})
        
        # Emoji based on alert level
        emoji = {
            'CRITICAL': '🚨',
            'HIGH': '🎯',
            'MEDIUM': '👀',
            'WATCH': '⏸️',
            'LOW': '⚪'
        }.get(alert_level, '⚪')
        
        msg = f"""
{emoji} COMPASS SIGNAL: {symbol} {signal['signal']}

📊 Analysis Summary:
├─ Signal: {signal['signal']} ({signal['confidence']} confidence)
├─ Score: {signal['score']:.1f}/100
├─ Alignment: {signal['alignment']}
└─ Alert Level: {alert_level}

📈 Timeframe Breakdown:
"""
        
        for tf, score in signal['timeframe_scores'].items():
            emoji_tf = '✅' if score > 20 else '❌' if score < -20 else '➖'
            msg += f"├─ {tf.upper()}: {score:+.0f} {emoji_tf}\n"
        
        if trade_setup and signal['signal'] != 'Flat':
            msg += f"""
🎯 Trade Setup:
├─ Entry Zone: ${trade_setup['entry_zone'][0]:,.2f} - ${trade_setup['entry_zone'][1]:,.2f}
├─ Stop Loss: ${trade_setup['stop_loss']:,.2f}
├─ Target 1: ${trade_setup['target_1']:,.2f} ({trade_setup['rr_ratio_1']})
├─ Target 2: ${trade_setup['target_2']:,.2f} ({trade_setup['rr_ratio_2']})
└─ {trade_setup['position_size_example']}
"""
        
        if futures:
            msg += f"""
📊 Futures Context:
├─ OI: {futures.get('oi', 'N/A'):,.0f} contracts
├─ Funding: {futures.get('funding_rate', 0)*100:.4f}%
└─ L/S Ratio: {futures.get('ls_ratio', 'N/A')}
"""
        
        msg += f"""
⚠️ Required Confirmation:
   • Volume >1.5x baseline on entry
   • Price action aligns with {signal['signal']} bias
   • No major news/events

⏱️ Valid for: Next 4 hours

✅ PRE-TRADE CHECKLIST:
□ I have reviewed all timeframes
□ I agree with the COMPASS bias
□ Volume confirmation visible
□ Stop loss set before entry
□ Position size matches 1% risk rule
□ Emotionally calm (not FOMO)

📝 Journal: What could invalidate this? _________
"""
        return msg
    
    def log_alert(self, signal):
        """Log alert to file"""
        with open(ALERT_LOG, 'a') as f:
            f.write(f"{datetime.now().isoformat()} | {signal['symbol']} | {signal['alert_level']} | {signal['signal']} | Score: {signal['score']:.1f}\n")
    
    def add_to_tracker(self, signal):
        """Add signal to trade tracker for performance monitoring"""
        if signal['signal'] == 'Flat':
            return
        
        trade_setup = signal.get('trade_setup', {})
        if not trade_setup:
            return
        
        trade_id = f"{signal['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        new_trade = {
            'trade_id': trade_id,
            'timestamp': signal['timestamp'],
            'symbol': signal['symbol'],
            'signal': signal['signal'],
            'entry_zone_low': trade_setup['entry_zone'][0],
            'entry_zone_high': trade_setup['entry_zone'][1],
            'stop_loss': trade_setup['stop_loss'],
            'target_1': trade_setup['target_1'],
            'target_2': trade_setup['target_2'],
            'confidence': signal['confidence'],
            'score': signal['score'],
            'status': 'PENDING',
            'actual_entry': None,
            'actual_exit': None,
            'pnl': None,
            'notes': ''
        }
        
        self.trade_df = pd.concat([self.trade_df, pd.DataFrame([new_trade])], ignore_index=True)
        self.trade_df.to_csv(TRADE_TRACKER, index=False)
        
        return trade_id
    
    def send_telegram_alert(self, message):
        """Send alert via Telegram"""
        try:
            # Use OpenClaw's message tool via subprocess or direct call
            # For now, we'll write to a file that can be picked up
            alert_file = Path('/root/.openclaw/workspace/compass_pending_alert.txt')
            with open(alert_file, 'w') as f:
                f.write(message)
            return True
        except Exception as e:
            print(f"Error sending alert: {e}")
            return False
    
    def check_existing_position(self, symbol):
        """Check if we already have a pending position for this symbol"""
        pending = self.trade_df[
            (self.trade_df['symbol'] == symbol) & 
            (self.trade_df['status'] == 'PENDING')
        ]
        return len(pending) > 0
    
    def generate_all_signals(self):
        """Generate signals for all symbols"""
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        signals = []
        
        print("="*70)
        print("COMPASS Signal Generator")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        for symbol in symbols:
            print(f"\nProcessing {symbol}...")
            
            # Check if already have pending position
            if self.check_existing_position(symbol):
                print(f"  ⏸️  Pending position exists, skipping")
                continue
            
            # Load analysis
            analysis = self.load_latest_analysis(symbol)
            if not analysis:
                print(f"  ✗ No analysis found")
                continue
            
            # Generate signal
            signal = self.generate_signal(analysis)
            if not signal:
                print(f"  ✗ Could not generate signal")
                continue
            
            signals.append(signal)
            
            # Log alert
            self.log_alert(signal)
            
            # Add to tracker if actionable
            if signal['alert_level'] in ['CRITICAL', 'HIGH']:
                trade_id = self.add_to_tracker(signal)
                print(f"  🎯 {signal['alert_level']} signal generated (ID: {trade_id})")
                
                # Format and send alert
                alert_msg = self.format_alert_message(signal)
                self.send_telegram_alert(alert_msg)
                print(f"  📤 Alert sent")
            else:
                print(f"  ⏸️  {signal['alert_level']} signal (no alert)")
        
        print(f"\n{'='*70}")
        print(f"Generated {len(signals)} signals")
        print('='*70)
        
        return signals

def main():
    """Main signal generation"""
    generator = CompassSignalGenerator()
    signals = generator.generate_all_signals()
    return signals

if __name__ == '__main__':
    main()
