#!/usr/bin/env python3
"""
Accurate Backtest - Using Optimized Strategy Parameters
$1000 Binance Futures Account with 5x Leverage
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import numpy as np

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
RESULTS_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/backtests')

# Load optimized strategies
with open(RESULTS_DIR / 'FINAL_STRATEGIES.json') as f:
    OPTIMAL_STRATEGIES = json.load(f)

# Fees
TAKER_FEE = 0.0005  # 0.05% per side
MAKER_FEE = 0.0002  # 0.02% per side
FUNDING_FEE = 0.0001  # ~0.01% per 8h


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


def calculate_atr(data, period=14):
    """Calculate ATR"""
    if len(data) < period + 1:
        return 0
    tr_list = []
    for i in range(1, len(data)):
        high = data[i]['high']
        low = data[i]['low']
        prev_close = data[i-1]['close']
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_list.append(tr)
    return sum(tr_list[-period:]) / period


def simulate_trade_futures(entry, stop, target, direction, data_slice, 
                           balance, leverage=5, risk_pct=0.03):
    """
    Simulate a futures trade with realistic fees
    Returns: (pnl, exit_price, exit_reason, fees)
    """
    # Position sizing based on risk
    risk_amount = balance * risk_pct
    price_risk = abs(entry - stop) / entry
    position_size = risk_amount / price_risk
    
    # Apply leverage
    margin = position_size / leverage
    
    # Opening fee
    open_fee = position_size * TAKER_FEE
    
    # Simulate price movement
    exit_price = None
    exit_reason = None
    
    for candle in data_slice:
        if direction == 'LONG':
            # Check stop loss
            if candle['low'] <= stop:
                exit_price = stop
                exit_reason = 'STOP'
                break
            # Check take profit
            if candle['high'] >= target:
                exit_price = target
                exit_reason = 'TARGET'
                break
        else:  # SHORT
            if candle['high'] >= stop:
                exit_price = stop
                exit_reason = 'STOP'
                break
            if candle['low'] <= target:
                exit_price = target
                exit_reason = 'TARGET'
                break
    
    # If no exit, use last close
    if exit_price is None:
        exit_price = data_slice[-1]['close'] if data_slice else entry
        exit_reason = 'TIME'
    
    # Calculate P&L
    if direction == 'LONG':
        pnl = (exit_price - entry) / entry * position_size * leverage
    else:
        pnl = (entry - exit_price) / entry * position_size * leverage
    
    # Closing fee
    close_fee = position_size * TAKER_FEE
    
    # Funding fees (assume 3 funding periods per trade on average)
    funding = position_size * FUNDING_FEE * 3
    
    total_fees = open_fee + close_fee + funding
    net_pnl = pnl - total_fees
    
    return net_pnl, exit_price, exit_reason, total_fees


def backtest_btc(data_1h, data_1d, balance=1000):
    """Backtest BTC with optimal parameters"""
    config = OPTIMAL_STRATEGIES['BTCUSDT']
    trades = []
    equity = [balance]
    
    stop_mult = config['stop_atr_mult']  # 3.0
    target_mult = config['target_atr_mult']  # 6.0
    
    for i in range(50, len(data_1h) - 24):
        # Look for setup - price near fib level in uptrend
        recent_data = data_1h[i-50:i]
        highs = [c['high'] for c in recent_data]
        lows = [c['low'] for c in recent_data]
        closes = [c['close'] for c in recent_data]
        
        swing_high = max(highs[-20:])
        swing_low = min(lows[-20:])
        current = closes[-1]
        
        # Fib 0.618 zone
        fib_618 = swing_high - (swing_high - swing_low) * 0.618
        fib_50 = swing_high - (swing_high - swing_low) * 0.5
        
        # Check if price in entry zone
        if not (fib_618 * 0.99 <= current <= fib_50 * 1.01):
            continue
        
        # Check trend (higher timeframe)
        if len(data_1d) > 10:
            daily_trend = data_1d[i//24]['close'] > data_1d[i//24 - 10]['close']
            if not daily_trend:
                continue
        
        # Calculate ATR and levels
        atr = calculate_atr(recent_data)
        entry = current
        stop = entry - atr * stop_mult
        target = entry + atr * target_mult
        
        # Check minimum stop
        min_stop_pct = config['min_stop_pct']  # 0.75%
        if abs(entry - stop) / entry * 100 < min_stop_pct:
            continue
        
        # Simulate trade
        future_data = data_1h[i:i+24]
        pnl, exit_p, reason, fees = simulate_trade_futures(
            entry, stop, target, 'LONG', future_data, balance
        )
        
        balance += pnl
        equity.append(balance)
        
        trades.append({
            'entry': entry,
            'exit': exit_p,
            'pnl': pnl,
            'fees': fees,
            'reason': reason,
            'balance': balance
        })
    
    return trades, equity


def backtest_eth(data_1h, balance=1000):
    """Backtest ETH with selective filters"""
    config = OPTIMAL_STRATEGIES['ETHUSDT']
    trades = []
    equity = [balance]
    
    stop_mult = config['stop_atr_mult']  # 1.5
    target_mult = config['target_atr_mult']  # 3.0
    
    for i in range(30, len(data_1h) - 24):
        recent = data_1h[i-30:i]
        closes = [c['close'] for c in recent]
        
        # EMA 9/21
        ema9 = sum(closes[-9:]) / 9
        ema21 = sum(closes[-21:]) / 21
        
        # Check bullish alignment
        if closes[-1] < ema9 or ema9 < ema21:
            continue
        
        # Check for momentum (3 consecutive up candles)
        if not (closes[-1] > closes[-2] > closes[-3] > closes[-4]):
            continue
        
        # ATR and levels
        atr = calculate_atr(recent)
        entry = closes[-1]
        stop = entry - atr * stop_mult
        target = entry + atr * target_mult
        
        # Minimum stop check
        if abs(entry - stop) / entry * 100 < config['min_stop_pct']:
            continue
        
        future_data = data_1h[i:i+24]
        pnl, exit_p, reason, fees = simulate_trade_futures(
            entry, stop, target, 'LONG', future_data, balance
        )
        
        balance += pnl
        equity.append(balance)
        
        trades.append({
            'entry': entry,
            'exit': exit_p,
            'pnl': pnl,
            'fees': fees,
            'reason': reason,
            'balance': balance
        })
    
    return trades, equity


def backtest_sol(data_1h, balance=1000):
    """Backtest SOL with EMA crossover"""
    config = OPTIMAL_STRATEGIES.get('SOLUSDT', {})
    trades = []
    equity = [balance]
    
    # Use 50% position size
    position_factor = config.get('position_factor', 0.5)
    
    for i in range(30, len(data_1h) - 24):
        closes = [c['close'] for c in data_1h[i-30:i]]
        
        # EMA 12/26 crossover
        ema12_now = sum(closes[-12:]) / 12
        ema26_now = sum(closes[-26:]) / 26
        ema12_prev = sum(closes[-13:-1]) / 12
        ema26_prev = sum(closes[-27:-1]) / 26
        
        # Bullish crossover
        if not (ema12_prev < ema26_prev and ema12_now > ema26_now):
            continue
        
        entry = closes[-1]
        stop = entry * 0.97  # 3% fixed stop
        target = entry * 1.04  # 4% fixed target
        
        future_data = data_1h[i:i+24]
        pnl, exit_p, reason, fees = simulate_trade_futures(
            entry, stop, target, 'LONG', future_data, balance, risk_pct=0.03*position_factor
        )
        
        balance += pnl
        equity.append(balance)
        
        trades.append({
            'entry': entry,
            'exit': exit_p,
            'pnl': pnl,
            'fees': fees,
            'reason': reason,
            'balance': balance
        })
    
    return trades, equity


def backtest_xrp(data_1h, balance=1000):
    """Backtest XRP with EMA crossover"""
    config = OPTIMAL_STRATEGIES.get('XRPUSDT', {})
    trades = []
    equity = [balance]
    
    position_factor = config.get('position_factor', 0.5)
    
    for i in range(25, len(data_1h) - 24):
        closes = [c['close'] for c in data_1h[i-25:i]]
        
        # EMA 9/21 crossover
        ema9_now = sum(closes[-9:]) / 9
        ema21_now = sum(closes[-21:]) / 21
        ema9_prev = sum(closes[-10:-1]) / 9
        ema21_prev = sum(closes[-22:-1]) / 21
        
        if not (ema9_prev < ema21_prev and ema9_now > ema21_now):
            continue
        
        entry = closes[-1]
        stop = entry * 0.97
        target = entry * 1.04
        
        future_data = data_1h[i:i+24]
        pnl, exit_p, reason, fees = simulate_trade_futures(
            entry, stop, target, 'LONG', future_data, balance, risk_pct=0.03*position_factor
        )
        
        balance += pnl
        equity.append(balance)
        
        trades.append({
            'entry': entry,
            'exit': exit_p,
            'pnl': pnl,
            'fees': fees,
            'reason': reason,
            'balance': balance
        })
    
    return trades, equity


def backtest_bnb(data_1h, data_1d, balance=1000):
    """Backtest BNB with extreme selectivity"""
    config = OPTIMAL_STRATEGIES['BNBUSDT']
    trades = []
    equity = [balance]
    
    stop_mult = config['stop_atr_mult']  # 3.0
    target_mult = config['target_atr_mult']  # 6.0
    
    for i in range(50, len(data_1h) - 24):
        # Check daily trend > 5% over 10 days
        if len(data_1d) < i//24 + 10:
            continue
        
        daily_idx = i // 24
        trend_10d = (data_1d[daily_idx]['close'] - data_1d[daily_idx-10]['close']) / data_1d[daily_idx-10]['close']
        if trend_10d < 0.05:  # Need >5% trend
            continue
        
        # Check volume spike
        recent_vol = sum(c['volume'] for c in data_1h[i-24:i])
        avg_vol = sum(c['volume'] for c in data_1h[i-120:i]) / 5
        if recent_vol < avg_vol * 1.5:
            continue
        
        # Entry logic
        recent = data_1h[i-30:i]
        closes = [c['close'] for c in recent]
        entry = closes[-1]
        
        atr = calculate_atr(recent)
        stop = entry - atr * stop_mult
        target = entry + atr * target_mult
        
        future_data = data_1h[i:i+24]
        pnl, exit_p, reason, fees = simulate_trade_futures(
            entry, stop, target, 'LONG', future_data, balance
        )
        
        balance += pnl
        equity.append(balance)
        
        trades.append({
            'entry': entry,
            'exit': exit_p,
            'pnl': pnl,
            'fees': fees,
            'reason': reason,
            'balance': balance
        })
    
    return trades, equity


def calculate_metrics(trades, equity, initial_balance=1000):
    """Calculate performance metrics"""
    if not trades:
        return None
    
    total_pnl = sum(t['pnl'] for t in trades)
    winning = [t for t in trades if t['pnl'] > 0]
    losing = [t for t in trades if t['pnl'] <= 0]
    
    # Max drawdown
    peak = initial_balance
    max_dd = 0
    for bal in equity:
        if bal > peak:
            peak = bal
        dd = peak - bal
        if dd > max_dd:
            max_dd = dd
    
    # Profit factor
    gross_profit = sum(t['pnl'] for t in winning)
    gross_loss = abs(sum(t['pnl'] for t in losing))
    pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    return {
        'trades': len(trades),
        'wins': len(winning),
        'losses': len(losing),
        'win_rate': len(winning) / len(trades) * 100,
        'total_pnl': total_pnl,
        'total_pnl_pct': (total_pnl / initial_balance) * 100,
        'avg_trade': total_pnl / len(trades),
        'max_drawdown': max_dd,
        'max_dd_pct': (max_dd / initial_balance) * 100,
        'profit_factor': pf,
        'final_balance': equity[-1]
    }


if __name__ == '__main__':
    print("="*90)
    print("BACKTEST RESULTS - $1000 Binance Futures Account (5x Leverage)")
    print("Using Optimized Strategy Parameters")
    print("="*90)
    
    results = {}
    
    # BTC
    print("\n🔄 Running BTC backtest...")
    btc_1h = load_data('BTCUSDT', '1h')
    btc_1d = load_data('BTCUSDT', '1d')
    trades, equity = backtest_btc(btc_1h, btc_1d)
    results['BTC'] = calculate_metrics(trades, equity)
    
    # ETH
    print("🔄 Running ETH backtest...")
    eth_1h = load_data('ETHUSDT', '1h')
    trades, equity = backtest_eth(eth_1h)
    results['ETH'] = calculate_metrics(trades, equity)
    
    # SOL
    print("🔄 Running SOL backtest...")
    sol_1h = load_data('SOLUSDT', '1h')
    trades, equity = backtest_sol(sol_1h)
    results['SOL'] = calculate_metrics(trades, equity)
    
    # XRP
    print("🔄 Running XRP backtest...")
    xrp_1h = load_data('XRPUSDT', '1h')
    trades, equity = backtest_xrp(xrp_1h)
    results['XRP'] = calculate_metrics(trades, equity)
    
    # BNB
    print("🔄 Running BNB backtest...")
    bnb_1h = load_data('BNBUSDT', '1h')
    bnb_1d = load_data('BNBUSDT', '1d')
    trades, equity = backtest_bnb(bnb_1h, bnb_1d)
    results['BNB'] = calculate_metrics(trades, equity)
    
    # Print results
    print("\n" + "="*90)
    print(f"{'Symbol':<8} {'Trades':<8} {'Win%':<8} {'P&L $':<12} {'P&L %':<10} {'Max DD':<10} {'PF':<8} {'Final $':<12}")
    print("-"*90)
    
    total_pnl = 0
    for sym, r in results.items():
        if r:
            total_pnl += r['total_pnl']
            print(f"{sym:<8} {r['trades']:<8} {r['win_rate']:>6.1f}%  "
                  f"${r['total_pnl']:>8.2f}  {r['total_pnl_pct']:>6.2f}%   "
                  f"{r['max_dd_pct']:>5.1f}%    {r['profit_factor']:>4.2f}   "
                  f"${r['final_balance']:>8.2f}")
    
    print("-"*90)
    print(f"{'TOTAL':<8} {'':<8} {'':<8} ${total_pnl:>8.2f}  {(total_pnl/1000)*100:>6.2f}%")
    print("="*90)
    
    # Save results
    with open(RESULTS_DIR / 'accurate_backtest_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {RESULTS_DIR / 'accurate_backtest_results.json'}")
