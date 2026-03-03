#!/usr/bin/env python3
"""
Comprehensive Backtest Engine - Binance Futures Simulation
Account: $1000 with leverage, includes fees and realistic conditions
"""

import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
RESULTS_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/backtests')

# Binance Futures fees (taker)
BINANCE_MAKER_FEE = 0.0002  # 0.02%
BINANCE_TAKER_FEE = 0.0005  # 0.05%
BINANCE_FUNDING_FEE = 0.0001  # 0.01% (approx 3x daily)

@dataclass
class Trade:
    entry_time: datetime
    exit_time: Optional[datetime]
    direction: str  # LONG or SHORT
    entry_price: float
    exit_price: Optional[float]
    stop_loss: float
    take_profit: float
    position_size: float  # in USD
    leverage: float
    pnl: float
    pnl_pct: float
    fees: float
    exit_reason: str
    status: str  # OPEN, CLOSED

@dataclass
class BacktestResult:
    symbol: str
    strategy: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_pnl_pct: float
    avg_trade_pnl: float
    max_drawdown: float
    max_drawdown_pct: float
    profit_factor: float
    sharpe_ratio: float
    trades: List[Trade]
    equity_curve: List[float]

class FuturesBacktester:
    """Backtester with realistic Binance Futures conditions"""
    
    def __init__(self, initial_balance=1000, leverage=5):
        self.initial_balance = initial_balance
        self.leverage = leverage
        self.balance = initial_balance
        self.equity_curve = [initial_balance]
        self.peak_balance = initial_balance
        self.max_drawdown = 0
        
    def calculate_position_size(self, risk_pct, entry, stop, leverage):
        """Calculate position size based on risk"""
        risk_amount = self.balance * risk_pct
        price_risk = abs(entry - stop) / entry
        position_size = risk_amount / price_risk
        # Cap at available leverage
        max_position = self.balance * leverage
        return min(position_size, max_position)
    
    def calculate_fees(self, position_size, is_taker=True):
        """Calculate opening + closing fees"""
        fee_rate = BINANCE_TAKER_FEE if is_taker else BINANCE_MAKER_FEE
        # Open + Close = 2x fees
        return position_size * fee_rate * 2
    
    def simulate_trade(self, direction, entry, stop, target, 
                      entry_time, exit_time, 
                      price_data, strategy_params) -> Trade:
        """Simulate a single trade with realistic execution"""
        
        # Position sizing (3% risk per trade)
        risk_pct = 0.03
        position_size = self.calculate_position_size(risk_pct, entry, stop, self.leverage)
        
        # Calculate fees
        fees = self.calculate_fees(position_size)
        
        # Find actual exit based on price action
        exit_price = None
        exit_reason = None
        
        # Look through price data to find what hit first (stop or target)
        for candle in price_data:
            if candle['timestamp'] < entry_time.timestamp() * 1000:
                continue
            if candle['timestamp'] > exit_time.timestamp() * 1000:
                break
                
            if direction == 'LONG':
                # Check if stop hit
                if candle['low'] <= stop:
                    exit_price = stop
                    exit_reason = 'STOP_LOSS'
                    break
                # Check if target hit
                if candle['high'] >= target:
                    exit_price = target
                    exit_reason = 'TAKE_PROFIT'
                    break
            else:  # SHORT
                if candle['high'] >= stop:
                    exit_price = stop
                    exit_reason = 'STOP_LOSS'
                    break
                if candle['low'] <= target:
                    exit_price = target
                    exit_reason = 'TAKE_PROFIT'
                    break
        
        # If no exit found, close at last price
        if exit_price is None:
            exit_price = price_data[-1]['close']
            exit_reason = 'TIME_EXIT'
        
        # Calculate P&L
        if direction == 'LONG':
            pnl = (exit_price - entry) / entry * position_size * self.leverage
        else:
            pnl = (entry - exit_price) / entry * position_size * self.leverage
        
        # Subtract fees
        pnl -= fees
        
        # Update balance
        self.balance += pnl
        self.equity_curve.append(self.balance)
        
        # Track drawdown
        if self.balance > self.peak_balance:
            self.peak_balance = self.balance
        drawdown = self.peak_balance - self.balance
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
        
        return Trade(
            entry_time=entry_time,
            exit_time=exit_time,
            direction=direction,
            entry_price=entry,
            exit_price=exit_price,
            stop_loss=stop,
            take_profit=target,
            position_size=position_size,
            leverage=self.leverage,
            pnl=pnl,
            pnl_pct=(pnl / self.initial_balance) * 100,
            fees=fees,
            exit_reason=exit_reason,
            status='CLOSED'
        )
    
    def run_backtest(self, symbol, strategy_func, data_1h, data_1d=None) -> BacktestResult:
        """Run complete backtest for a symbol"""
        trades = []
        
        # Reset balance
        self.balance = self.initial_balance
        self.equity_curve = [self.initial_balance]
        self.peak_balance = self.initial_balance
        self.max_drawdown = 0
        
        # Look for trade setups in historical data
        lookback = 500  # Look at last 500 hours
        if len(data_1h) < lookback:
            lookback = len(data_1h)
        
        for i in range(100, lookback - 24):  # Need buffer for exits
            window = data_1h[:i]
            
            # Check for setup
            if data_1d:
                setup = strategy_func(window, data_1d[:i//24])
            else:
                setup = strategy_func(window)
            
            if not setup:
                continue
            
            # Simulate trade
            entry_time = datetime.fromtimestamp(window[-1]['timestamp'] / 1000)
            exit_time = entry_time + timedelta(hours=24)  # Max hold 24h
            
            # Get price data for exit simulation
            future_data = data_1h[i:i+24]
            if len(future_data) < 2:
                continue
            
            trade = self.simulate_trade(
                setup['direction'],
                setup['entry'],
                setup['stop'],
                setup['target'],
                entry_time,
                exit_time,
                future_data,
                setup
            )
            
            trades.append(trade)
        
        # Calculate metrics
        if not trades:
            return None
        
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl <= 0]
        
        total_pnl = sum(t.pnl for t in trades)
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Sharpe ratio (simplified)
        returns = [t.pnl_pct for t in trades]
        avg_return = np.mean(returns) if returns else 0
        std_return = np.std(returns) if returns else 1
        sharpe = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
        
        return BacktestResult(
            symbol=symbol,
            strategy=trades[0].direction if trades else 'UNKNOWN',
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=len(winning_trades) / len(trades) * 100 if trades else 0,
            total_pnl=total_pnl,
            total_pnl_pct=(total_pnl / self.initial_balance) * 100,
            avg_trade_pnl=total_pnl / len(trades) if trades else 0,
            max_drawdown=self.max_drawdown,
            max_drawdown_pct=(self.max_drawdown / self.initial_balance) * 100,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe,
            trades=trades,
            equity_curve=self.equity_curve
        )


def load_data(symbol, interval):
    """Load OHLCV data"""
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    if not filepath.exists():
        return []
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
    return data


def btc_fib_strategy(data_1h, data_1d=None):
    """BTC Fibonacci Pullback Strategy"""
    if len(data_1h) < 50:
        return None
    
    prices = [c['close'] for c in data_1h]
    highs = [c['high'] for c in data_1h]
    lows = [c['low'] for c in data_1h]
    
    # Find swing high/low
    recent_high = max(highs[-20:])
    recent_low = min(lows[-20:])
    current = prices[-1]
    
    # Calculate fib levels
    diff = recent_high - recent_low
    fib_50 = recent_high - diff * 0.5
    fib_618 = recent_high - diff * 0.618
    
    # Check if price near fib 0.5-0.618 zone
    if not (fib_618 <= current <= fib_50):
        return None
    
    # ATR for stop
    atr = sum(highs[-14:]) / 14 - sum(lows[-14:]) / 14
    
    return {
        'direction': 'LONG',
        'entry': current,
        'stop': current - atr * 3,
        'target': recent_high,
        'strategy': 'BTC_Fib_Pullback'
    }


def eth_momentum_strategy(data_1h):
    """ETH Momentum Breakout Strategy"""
    if len(data_1h) < 30:
        return None
    
    prices = [c['close'] for c in data_1h]
    
    # EMA 9/21
    ema9 = sum(prices[-9:]) / 9
    ema21 = sum(prices[-21:]) / 21
    
    # Check for bullish momentum
    if prices[-1] < ema9 or ema9 < ema21:
        return None
    
    # Check recent breakout
    if prices[-1] < max(prices[-10:-1]) * 1.01:
        return None
    
    current = prices[-1]
    
    return {
        'direction': 'LONG',
        'entry': current,
        'stop': current * 0.985,
        'target': current * 1.03,
        'strategy': 'ETH_Momentum'
    }


def sol_ema_strategy(data_1h):
    """SOL EMA Crossover Strategy"""
    if len(data_1h) < 30:
        return None
    
    prices = [c['close'] for c in data_1h]
    
    # EMA 12/26
    ema12 = sum(prices[-12:]) / 12
    ema26 = sum(prices[-26:]) / 26
    prev_ema12 = sum(prices[-13:-1]) / 12
    prev_ema26 = sum(prices[-27:-1]) / 26
    
    # Check for bullish crossover
    if not (prev_ema12 < prev_ema26 and ema12 > ema26):
        return None
    
    current = prices[-1]
    
    return {
        'direction': 'LONG',
        'entry': current,
        'stop': current * 0.97,
        'target': current * 1.04,
        'strategy': 'SOL_EMA_Cross',
        'position_factor': 0.5
    }


def xrp_ema_strategy(data_1h):
    """XRP EMA Crossover Strategy"""
    if len(data_1h) < 25:
        return None
    
    prices = [c['close'] for c in data_1h]
    
    # EMA 9/21
    ema9 = sum(prices[-9:]) / 9
    ema21 = sum(prices[-21:]) / 21
    prev_ema9 = sum(prices[-10:-1]) / 9
    prev_ema21 = sum(prices[-22:-1]) / 21
    
    # Check for bullish crossover
    if not (prev_ema9 < prev_ema21 and ema9 > ema21):
        return None
    
    current = prices[-1]
    
    return {
        'direction': 'LONG',
        'entry': current,
        'stop': current * 0.97,
        'target': current * 1.04,
        'strategy': 'XRP_EMA_Cross',
        'position_factor': 0.5
    }


def bnb_extreme_strategy(data_1h, data_1d):
    """BNB Extreme Selectivity Strategy"""
    if len(data_1h) < 50 or not data_1d or len(data_1d) < 10:
        return None
    
    prices = [c['close'] for c in data_1h]
    daily_prices = [c['close'] for c in data_1d]
    
    # Check 10-day trend > 5%
    trend_10d = (daily_prices[-1] - daily_prices[-10]) / daily_prices[-10]
    if trend_10d < 0.05:
        return None
    
    # Check volume spike
    recent_vol = sum(c['volume'] for c in data_1h[-24:])
    avg_vol = sum(c['volume'] for c in data_1h[-120:]) / 5
    if recent_vol < avg_vol * 1.5:
        return None
    
    current = prices[-1]
    
    return {
        'direction': 'LONG',
        'entry': current,
        'stop': current * 0.97,
        'target': current * 1.06,
        'strategy': 'BNB_Extreme'
    }


def print_results(results: List[BacktestResult]):
    """Print formatted backtest results"""
    print("\n" + "="*100)
    print("COMPREHENSIVE BACKTEST RESULTS - $1000 Binance Futures Account (5x Leverage)")
    print("="*100)
    print(f"{'Symbol':<10} {'Strategy':<18} {'Trades':<8} {'Win%':<8} {'P&L $':<12} {'P&L %':<10} {'Max DD':<10} {'PF':<8} {'Sharpe':<8}")
    print("-"*100)
    
    total_pnl = 0
    total_trades = 0
    
    for r in results:
        if not r:
            continue
        total_pnl += r.total_pnl
        total_trades += r.total_trades
        print(f"{r.symbol:<10} {r.strategy:<18} {r.total_trades:<8} {r.win_rate:>6.1f}%  "
              f"${r.total_pnl:>8.2f}  {r.total_pnl_pct:>6.2f}%   "
              f"{r.max_drawdown_pct:>5.1f}%    {r.profit_factor:>4.2f}   {r.sharpe_ratio:>4.2f}")
    
    print("-"*100)
    print(f"{'TOTAL':<10} {'':<18} {total_trades:<8} {'':<8} "
          f"${total_pnl:>8.2f}  {(total_pnl/1000)*100:>6.2f}%")
    print("="*100)
    
    # Detailed breakdown
    print("\n📊 DETAILED PERFORMANCE BREAKDOWN")
    print("="*100)
    
    for r in results:
        if not r:
            continue
        print(f"\n{r.symbol} - {r.strategy}")
        print(f"  Total Trades: {r.total_trades} | Wins: {r.winning_trades} | Losses: {r.losing_trades}")
        print(f"  Win Rate: {r.win_rate:.1f}%")
        print(f"  Total P&L: ${r.total_pnl:.2f} ({r.total_pnl_pct:.2f}%)")
        print(f"  Avg Trade P&L: ${r.avg_trade_pnl:.2f}")
        print(f"  Max Drawdown: ${r.max_drawdown:.2f} ({r.max_drawdown_pct:.2f}%)")
        print(f"  Profit Factor: {r.profit_factor:.2f}")
        print(f"  Sharpe Ratio: {r.sharpe_ratio:.2f}")
        
        # Recent trades
        print(f"  Last 5 Trades:")
        for t in r.trades[-5:]:
            status = "✅" if t.pnl > 0 else "❌"
            print(f"    {status} {t.entry_time.strftime('%Y-%m-%d')}: {t.direction} "
                  f"Entry=${t.entry_price:.0f} Exit=${t.exit_price:.0f} "
                  f"P&L=${t.pnl:.2f} ({t.exit_reason})")


if __name__ == '__main__':
    print("🔄 Running Backtests...")
    
    backtester = FuturesBacktester(initial_balance=1000, leverage=5)
    results = []
    
    # BTC
    print("  Testing BTC...")
    btc_1h = load_data('BTCUSDT', '1h')
    btc_1d = load_data('BTCUSDT', '1d')
    result = backtester.run_backtest('BTCUSDT', btc_fib_strategy, btc_1h, btc_1d)
    if result:
        results.append(result)
    
    # ETH
    print("  Testing ETH...")
    eth_1h = load_data('ETHUSDT', '1h')
    result = backtester.run_backtest('ETHUSDT', eth_momentum_strategy, eth_1h)
    if result:
        results.append(result)
    
    # SOL
    print("  Testing SOL...")
    sol_1h = load_data('SOLUSDT', '1h')
    result = backtester.run_backtest('SOLUSDT', sol_ema_strategy, sol_1h)
    if result:
        results.append(result)
    
    # XRP
    print("  Testing XRP...")
    xrp_1h = load_data('XRPUSDT', '1h')
    result = backtester.run_backtest('XRPUSDT', xrp_ema_strategy, xrp_1h)
    if result:
        results.append(result)
    
    # BNB
    print("  Testing BNB...")
    bnb_1h = load_data('BNBUSDT', '1h')
    bnb_1d = load_data('BNBUSDT', '1d')
    result = backtester.run_backtest('BNBUSDT', bnb_extreme_strategy, bnb_1h, bnb_1d)
    if result:
        results.append(result)
    
    # Print results
    print_results(results)
    
    # Save to file
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIR / 'backtest_results.json', 'w') as f:
        json.dump([{
            'symbol': r.symbol,
            'strategy': r.strategy,
            'total_trades': r.total_trades,
            'win_rate': r.win_rate,
            'total_pnl': r.total_pnl,
            'total_pnl_pct': r.total_pnl_pct,
            'max_drawdown_pct': r.max_drawdown_pct,
            'profit_factor': r.profit_factor,
            'sharpe_ratio': r.sharpe_ratio
        } for r in results], f, indent=2)
    
    print(f"\n💾 Results saved to: {RESULTS_DIR / 'backtest_results.json'}")
