#!/usr/bin/env python3
"""
COMPASS Trade Tracker & Performance Monitor
Tracks trade performance and generates improvement insights
"""

import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import json

def get_workspace():
    """Get workspace path from environment or script location"""
    env_path = os.environ.get('COMPASS_WORKSPACE')
    if env_path:
        return Path(env_path)
    return Path(__file__).resolve().parent

WORKSPACE = get_workspace()
TRADE_TRACKER = WORKSPACE / 'compass_trade_tracker.csv'
PERFORMANCE_LOG = WORKSPACE / 'compass_performance.json'

def load_trades():
    """Load all tracked trades with consistent schema"""
    columns = ['trade_id', 'timestamp', 'symbol', 'signal', 'score', 'confidence',
               'entry_zone_low', 'entry_zone_high', 'stop_loss', 'take_profit',
               'status', 'actual_entry', 'actual_exit', 'pnl', 'notes']
    
    if not TRADE_TRACKER.exists():
        return pd.DataFrame(columns=columns)
    
    df = pd.read_csv(TRADE_TRACKER)
    
    # Ensure all expected columns exist
    for col in columns:
        if col not in df.columns:
            df[col] = None
    
    return df

def update_trade_status(trade_id, status, actual_entry=None, actual_exit=None, pnl=None, notes=''):
    """Update trade with actual execution details"""
    df = load_trades()
    
    # Handle empty DataFrame or missing trade_id column
    if df.empty or 'trade_id' not in df.columns:
        print(f"Trade {trade_id} not found (no trades tracked)")
        return False
    
    if trade_id not in df['trade_id'].values:
        print(f"Trade {trade_id} not found")
        return False
    
    idx = df[df['trade_id'] == trade_id].index[0]
    df.at[idx, 'status'] = status
    
    if actual_entry:
        df.at[idx, 'actual_entry'] = actual_entry
    if actual_exit:
        df.at[idx, 'actual_exit'] = actual_exit
    if pnl is not None:
        df.at[idx, 'pnl'] = pnl
    if notes:
        df.at[idx, 'notes'] = notes
    
    df.to_csv(TRADE_TRACKER, index=False)
    return True

def calculate_performance():
    """Calculate performance metrics"""
    df = load_trades()
    if df.empty:
        return None
    
    # Filter completed trades
    completed = df[df['status'].isin(['WIN', 'LOSS', 'BREAKEVEN'])]
    
    if completed.empty:
        return None
    
    total_trades = len(completed)
    wins = len(completed[completed['status'] == 'WIN'])
    losses = len(completed[completed['status'] == 'LOSS'])
    breakeven = len(completed[completed['status'] == 'BREAKEVEN'])
    
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    
    # PnL stats
    total_pnl = completed['pnl'].sum() if 'pnl' in completed.columns else 0
    avg_pnl = completed['pnl'].mean() if 'pnl' in completed.columns else 0
    
    # By confidence level
    high_conf = completed[completed['confidence'] == 'High']
    med_conf = completed[completed['confidence'] == 'Medium']
    
    performance = {
        'timestamp': datetime.now().isoformat(),
        'total_trades': total_trades,
        'wins': wins,
        'losses': losses,
        'breakeven': breakeven,
        'win_rate': round(win_rate, 2),
        'total_pnl': round(total_pnl, 2),
        'avg_pnl_per_trade': round(avg_pnl, 2),
        'high_confidence_win_rate': round(len(high_conf[high_conf['status'] == 'WIN']) / len(high_conf) * 100, 2) if len(high_conf) > 0 else 0,
        'medium_confidence_win_rate': round(len(med_conf[med_conf['status'] == 'WIN']) / len(med_conf) * 100, 2) if len(med_conf) > 0 else 0,
        'pending_trades': len(df[df['status'] == 'PENDING'])
    }
    
    # Save performance log
    if PERFORMANCE_LOG.exists():
        with open(PERFORMANCE_LOG, 'r') as f:
            history = json.load(f)
    else:
        history = []
    
    history.append(performance)
    
    with open(PERFORMANCE_LOG, 'w') as f:
        json.dump(history, f, indent=2)
    
    return performance

def generate_improvement_insights():
    """Generate insights for improving the system"""
    df = load_trades()
    if df.empty or len(df[df['status'] != 'PENDING']) < 5:
        return "Need more completed trades for insights"
    
    completed = df[df['status'].isin(['WIN', 'LOSS', 'BREAKEVEN'])]
    
    insights = []
    
    # Check score correlation with win rate
    high_score = completed[completed['score'] >= 70]
    low_score = completed[completed['score'] < 60]
    
    if len(high_score) > 0 and len(low_score) > 0:
        high_win_rate = len(high_score[high_score['status'] == 'WIN']) / len(high_score)
        low_win_rate = len(low_score[low_score['status'] == 'WIN']) / len(low_score)
        
        if high_win_rate > low_win_rate * 1.2:
            insights.append(f"✅ High score trades (>70) win {high_win_rate*100:.0f}% vs {low_win_rate*100:.0f}% for low scores")
        else:
            insights.append("⚠️ Score threshold may need adjustment - high scores not outperforming significantly")
    
    # Check confidence level performance
    for conf in ['High', 'Medium']:
        conf_trades = completed[completed['confidence'] == conf]
        if len(conf_trades) >= 5:
            win_rate = len(conf_trades[conf_trades['status'] == 'WIN']) / len(conf_trades)
            insights.append(f"📊 {conf} confidence trades: {win_rate*100:.0f}% win rate ({len(conf_trades)} trades)")
    
    # Check symbol performance
    for symbol in completed['symbol'].unique():
        sym_trades = completed[completed['symbol'] == symbol]
        if len(sym_trades) >= 3:
            win_rate = len(sym_trades[sym_trades['status'] == 'WIN']) / len(sym_trades)
            insights.append(f"📈 {symbol}: {win_rate*100:.0f}% win rate ({len(sym_trades)} trades)")
    
    return "\n".join(insights)

def display_dashboard():
    """Display performance dashboard"""
    df = load_trades()
    perf = calculate_performance()
    
    print("="*70)
    print("COMPASS Trade Tracker Dashboard")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    if df.empty:
        print("\nNo trades tracked yet")
        return
    
    # Pending trades
    pending = df[df['status'] == 'PENDING']
    print(f"\n⏳ PENDING TRADES: {len(pending)}")
    if len(pending) > 0:
        for _, trade in pending.iterrows():
            print(f"  • {trade['trade_id']}: {trade['signal']} {trade['symbol']} @ {trade['entry_zone_low']:.0f}-{trade['entry_zone_high']:.0f}")
    
    # Performance summary
    if perf:
        print("\n📊 PERFORMANCE SUMMARY")
        print(f"  Total Trades: {perf['total_trades']}")
        print(f"  Win Rate: {perf['win_rate']}%")
        print(f"  Wins: {perf['wins']} | Losses: {perf['losses']} | Breakeven: {perf['breakeven']}")
        print(f"  Total PnL: ${perf['total_pnl']:,.2f}")
        print(f"  Avg per Trade: ${perf['avg_pnl_per_trade']:,.2f}")
    
    # Recent completed trades
    completed = df[df['status'].isin(['WIN', 'LOSS', 'BREAKEVEN'])].tail(5)
    if not completed.empty:
        print("\n📝 RECENT COMPLETED TRADES")
        for _, trade in completed.iterrows():
            emoji = '✅' if trade['status'] == 'WIN' else '❌' if trade['status'] == 'LOSS' else '➖'
            pnl_str = f"${trade['pnl']:,.2f}" if pd.notna(trade['pnl']) else 'N/A'
            print(f"  {emoji} {trade['trade_id']}: {trade['status']} | PnL: {pnl_str}")
    
    # Insights
    print("\n💡 IMPROVEMENT INSIGHTS")
    insights = generate_improvement_insights()
    print(f"  {insights}")
    
    print("\n" + "="*70)

def main():
    """Main tracker function"""
    display_dashboard()

if __name__ == '__main__':
    main()
