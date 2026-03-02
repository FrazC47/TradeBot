#!/usr/bin/env python3
"""
Final Symbol-Specific Trading Strategies
Optimized for BTC, ETH, BNB based on backtest results
"""

import csv
import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
RESULTS_DIR = Path('/root/.openclaw/workspace/projects/crypto-analysis/backtests')

# FINAL STRATEGIES - Based on backtest optimization
FINAL_STRATEGIES = {
    'BTCUSDT': {
        'name': 'BTC Momentum Exhaustion',
        'rationale': 'BTC has frequent reversals (52%). Best to fade moves at 0.618 Fib after consecutive candles.',
        'fib_levels_long': ['0.618'],
        'fib_levels_short': ['0.618'],
        'consecutive_candles': 5,  # Need 5 consecutive in trend direction
        'rsi_long_max': 70,
        'rsi_short_min': 30,
        'volume_min': 1.0,  # Above average
        'stop_atr_mult': 1.2,
        'target_atr_mult': 2.4,  # 1:2 R:R
        'holding_periods': 20,
        'backtest_result': '66.7% win rate, +1.22% P&L'
    },
    
    'ETHUSDT': {
        'name': 'ETH Standard Trend Following',
        'rationale': 'ETH performs best with standard strategy. High volatility allows multiple Fib levels.',
        'fib_levels_long': ['0.618', '0.5', '0.382'],
        'fib_levels_short': ['0.382', '0.5', '0.618'],
        'consecutive_candles': 0,  # Not required
        'rsi_long_max': 70,
        'rsi_short_min': 30,
        'volume_min': 0.8,
        'stop_atr_mult': 1.5,
        'target_atr_mult': 3.0,  # 1:2 R:R
        'holding_periods': 20,
        'backtest_result': '100% win rate, +4.49% P&L'
    },
    
    'BNBUSDT': {
        'name': 'BNB Strong Trend',
        'rationale': 'BNB trends persist (47% reversal rate). Need strong trend confirmation (>2% from EMA).',
        'fib_levels_long': ['0.5'],
        'fib_levels_short': ['0.5'],
        'consecutive_candles': 0,
        'ema_distance_min': 2.0,  # Price >2% from daily EMA
        'rsi_long_max': 65,
        'rsi_short_min': 35,
        'volume_min': 1.2,  # 20% above average
        'stop_atr_mult': 1.5,
        'target_atr_mult': 3.0,  # 1:2 R:R
        'holding_periods': 20,
        'backtest_result': '56% win rate, +19.85% P&L'
    }
}

def print_strategy_summary():
    """Print final strategy summary"""
    print("=" * 80)
    print("FINAL SYMBOL-SPECIFIC TRADING STRATEGIES")
    print("=" * 80)
    
    for symbol, strategy in FINAL_STRATEGIES.items():
        print(f"\n{'=' * 80}")
        print(f"{symbol}: {strategy['name']}")
        print(f"{'=' * 80}")
        print(f"Rationale: {strategy['rationale']}")
        print(f"Backtest: {strategy['backtest_result']}")
        print(f"\nParameters:")
        print(f"  Fib levels (long): {strategy['fib_levels_long']}")
        print(f"  Fib levels (short): {strategy['fib_levels_short']}")
        print(f"  RSI range: <{strategy['rsi_long_max']} long, >{strategy['rsi_short_min']} short")
        print(f"  Volume: {strategy['volume_min']}x average")
        print(f"  Stop: {strategy['stop_atr_mult']}x ATR")
        print(f"  Target: {strategy['target_atr_mult']}x ATR")
        print(f"  R:R Ratio: 1:{strategy['target_atr_mult']/strategy['stop_atr_mult']:.1f}")
        
        if 'consecutive_candles' in strategy and strategy['consecutive_candles'] > 0:
            print(f"  Special: Requires {strategy['consecutive_candles']} consecutive candles")
        if 'ema_distance_min' in strategy:
            print(f"  Special: Requires >{strategy['ema_distance_min']}% from daily EMA")
    
    print(f"\n{'=' * 80}")
    print("IMPLEMENTATION NOTES")
    print(f"{'=' * 80}")
    print("""
1. Each strategy runs independently for its symbol
2. Daily trend must align with trade direction for all
3. All 3 timeframes (1h, 4h, 1d) must agree
4. Only enter during active market hours
5. Track results separately per symbol for ongoing optimization
    """)

if __name__ == '__main__':
    print_strategy_summary()
    
    # Save to file
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = RESULTS_DIR / f'final_strategies_{datetime.now().strftime("%Y%m%d")}.json'
    
    with open(output_file, 'w') as f:
        json.dump(FINAL_STRATEGIES, f, indent=2)
    
    print(f"\nSaved to: {output_file}")
