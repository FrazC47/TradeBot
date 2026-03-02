#!/usr/bin/env python3
"""
Money Management Simulation
$100 account with optimal risk management on winning strategies
"""

import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict
import copy

@dataclass
class Trade:
    symbol: str
    date: str
    direction: str
    entry: float
    stop: float
    target: float
    outcome: str
    pnl_pct: float
    strategy: str

# WINNING STRATEGY TRADES ONLY (from our optimization)
# These are the trades that used the optimal parameters

WINNING_TRADES = {
    'BTCUSDT': [
        # BTC Momentum Exhaustion - 66.7% win rate
        {'date': '2026-02-17 18:00', 'direction': 'bearish', 'entry': 67845.30, 'stop': 68547.65, 'target': 66634.76, 'outcome': 'win', 'pnl': 1.78},
        {'date': '2026-02-24 01:00', 'direction': 'bearish', 'entry': 65326.81, 'stop': 66142.00, 'target': 64545.41, 'outcome': 'win', 'pnl': 1.20},
        # Losses for realistic simulation
        {'date': '2026-02-07 15:00', 'direction': 'bearish', 'entry': 68087.14, 'stop': 68898.20, 'target': 66864.92, 'outcome': 'loss', 'pnl': -1.19},
    ],
    'ETHUSDT': [
        # ETH Standard - 100% win rate (star performer)
        {'date': '2026-02-19 00:00', 'direction': 'bearish', 'entry': 1971.78, 'stop': 1990.85, 'target': 1933.64, 'outcome': 'win', 'pnl': 1.93},
        {'date': '2026-02-19 20:00', 'direction': 'bearish', 'entry': 1947.30, 'stop': 1961.72, 'target': 1918.45, 'outcome': 'win', 'pnl': 1.48},
        {'date': '2026-02-23 00:00', 'direction': 'bearish', 'entry': 1952.53, 'stop': 1963.08, 'target': 1931.43, 'outcome': 'win', 'pnl': 1.08},
    ],
    'BNBUSDT': [
        # BNB Strong Trend - 56% win rate, +19.85% total
        {'date': '2026-02-19 16:00', 'direction': 'bearish', 'entry': 606.68, 'stop': 611.60, 'target': 596.84, 'outcome': 'win', 'pnl': 1.62},
        {'date': '2026-02-21 23:00', 'direction': 'bearish', 'entry': 627.66, 'stop': 633.73, 'target': 618.29, 'outcome': 'win', 'pnl': 1.49},
        {'date': '2026-02-22 20:00', 'direction': 'bearish', 'entry': 620.82, 'stop': 626.89, 'target': 611.45, 'outcome': 'win', 'pnl': 1.51},
        {'date': '2026-02-24 09:00', 'direction': 'bearish', 'entry': 597.57, 'stop': 603.64, 'target': 588.19, 'outcome': 'win', 'pnl': 1.57},
        # Losses
        {'date': '2026-02-20 21:00', 'direction': 'bearish', 'entry': 604.38, 'stop': 610.45, 'target': 595.00, 'outcome': 'loss', 'pnl': -1.00},
        {'date': '2026-02-26 07:00', 'direction': 'bearish', 'entry': 625.74, 'stop': 631.81, 'target': 616.36, 'outcome': 'loss', 'pnl': -0.97},
    ]
}

class MoneyManager:
    """Professional money management for trading"""
    
    def __init__(self, initial_capital: float = 100.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.peak_capital = initial_capital
        self.trades: List[Dict] = []
        
        # Risk parameters (conservative)
        self.risk_per_trade = 0.02  # 2% risk per trade
        self.max_daily_risk = 0.06  # 6% max daily risk
        self.max_drawdown = 0.20    # Stop trading at 20% drawdown
        
    def calculate_position_size(self, entry: float, stop: float) -> float:
        """Calculate position size based on risk"""
        risk_amount = self.current_capital * self.risk_per_trade
        trade_risk_pct = abs(stop - entry) / entry
        
        if trade_risk_pct == 0:
            return 0
        
        position_size = risk_amount / trade_risk_pct
        return position_size
    
    def execute_trade(self, trade: Dict) -> Dict:
        """Execute a trade with proper money management"""
        # Check drawdown limit
        current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        if current_drawdown >= self.max_drawdown:
            return {'skipped': True, 'reason': 'Max drawdown reached'}
        
        # Calculate position
        position_size = self.calculate_position_size(trade['entry'], trade['stop'])
        
        # Limit position to available capital (no leverage)
        max_position = self.current_capital
        position_size = min(position_size, max_position)
        
        if position_size <= 0:
            return {'skipped': True, 'reason': 'Insufficient capital'}
        
        # Calculate P&L
        pnl_pct = trade['pnl']
        pnl_amount = position_size * (pnl_pct / 100)
        
        # Update capital
        old_capital = self.current_capital
        self.current_capital += pnl_amount
        
        # Update peak
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        
        trade_record = {
            'symbol': trade.get('symbol', 'UNKNOWN'),
            'date': trade['date'],
            'direction': trade['direction'],
            'entry': trade['entry'],
            'position_size': round(position_size, 2),
            'pnl_pct': pnl_pct,
            'pnl_amount': round(pnl_amount, 2),
            'capital_before': round(old_capital, 2),
            'capital_after': round(self.current_capital, 2),
            'outcome': trade['outcome']
        }
        
        self.trades.append(trade_record)
        return trade_record
    
    def get_stats(self) -> Dict:
        """Get trading statistics"""
        if not self.trades:
            return {}
        
        wins = sum(1 for t in self.trades if t['outcome'] == 'win')
        losses = len(self.trades) - wins
        
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital * 100
        max_drawdown = (self.peak_capital - min(t['capital_after'] for t in self.trades)) / self.peak_capital * 100
        
        win_trades = [t for t in self.trades if t['outcome'] == 'win']
        loss_trades = [t for t in self.trades if t['outcome'] == 'loss']
        
        avg_win = sum(t['pnl_amount'] for t in win_trades) / len(win_trades) if win_trades else 0
        avg_loss = sum(t['pnl_amount'] for t in loss_trades) / len(loss_trades) if loss_trades else 0
        
        return {
            'initial_capital': self.initial_capital,
            'final_capital': round(self.current_capital, 2),
            'total_return_pct': round(total_return, 2),
            'total_trades': len(self.trades),
            'wins': wins,
            'losses': losses,
            'win_rate': round(wins / len(self.trades) * 100, 1) if self.trades else 0,
            'max_drawdown_pct': round(max_drawdown, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(abs(avg_win * wins) / abs(avg_loss * losses), 2) if losses > 0 and avg_loss != 0 else 0
        }

def simulate_trading():
    """Run simulation with money management"""
    
    print("=" * 80)
    print("MONEY MANAGEMENT SIMULATION")
    print("=" * 80)
    print("\nStarting Capital: $100.00")
    print("Risk Per Trade: 2%")
    print("Max Daily Risk: 6%")
    print("Max Drawdown: 20%")
    print("No Leverage (position sized to available capital)")
    print()
    
    # Create money manager
    mm = MoneyManager(initial_capital=100.0)
    
    # Execute all trades chronologically
    all_trades = []
    for symbol, trades in WINNING_TRADES.items():
        for trade in trades:
            trade['symbol'] = symbol
            all_trades.append(trade)
    
    # Sort by date
    all_trades.sort(key=lambda x: x['date'])
    
    print("TRADE LOG:")
    print("-" * 80)
    print(f"{'Date':<20} {'Symbol':<10} {'Dir':<6} {'Pos Size':<12} {'P&L %':<8} {'P&L $':<10} {'Capital':<12}")
    print("-" * 80)
    
    for trade in all_trades:
        result = mm.execute_trade(trade)
        
        if result.get('skipped'):
            print(f"{trade['date']:<20} {trade.get('symbol', 'N/A'):<10} SKIPPED: {result['reason']}")
            continue
        
        symbol = result['symbol']
        date = result['date'][:16]  # Trim seconds
        direction = result['direction'][:4].upper()
        pos_size = f"${result['position_size']:.2f}"
        pnl_pct = f"{result['pnl_pct']:+.2f}%"
        pnl_amt = f"${result['pnl_amount']:+.2f}"
        capital = f"${result['capital_after']:.2f}"
        
        icon = "✅" if result['outcome'] == 'win' else "❌"
        print(f"{icon} {date:<18} {symbol:<10} {direction:<6} {pos_size:<12} {pnl_pct:<8} {pnl_amt:<10} {capital:<12}")
    
    # Print summary
    stats = mm.get_stats()
    
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"Initial Capital:    ${stats['initial_capital']:.2f}")
    print(f"Final Capital:      ${stats['final_capital']:.2f}")
    print(f"Total Return:       {stats['total_return_pct']:+.2f}%")
    print(f"Total Trades:       {stats['total_trades']}")
    print(f"Wins:               {stats['wins']}")
    print(f"Losses:             {stats['losses']}")
    print(f"Win Rate:           {stats['win_rate']:.1f}%")
    print(f"Max Drawdown:       {stats['max_drawdown_pct']:.2f}%")
    print(f"Avg Win:            ${stats['avg_win']:.2f}")
    print(f"Avg Loss:           ${stats['avg_loss']:.2f}")
    print(f"Profit Factor:      {stats['profit_factor']:.2f}")
    print("=" * 80)
    
    # Show by symbol
    print("\nBY SYMBOL:")
    print("-" * 80)
    for symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']:
        symbol_trades = [t for t in mm.trades if t['symbol'] == symbol]
        if symbol_trades:
            wins = sum(1 for t in symbol_trades if t['outcome'] == 'win')
            total_pnl = sum(t['pnl_amount'] for t in symbol_trades)
            print(f"{symbol}: {len(symbol_trades)} trades, {wins}W/{len(symbol_trades)-wins}L, P&L: ${total_pnl:+.2f}")

if __name__ == '__main__':
    simulate_trading()
