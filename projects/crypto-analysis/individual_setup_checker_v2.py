#!/usr/bin/env python3
"""
Individual Setup Checker v2 - Using Unique Strategies Per Currency
Priority: ETH (most successful)
"""

import sys
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

# Add parent directory to path
sys.path.insert(0, '/root/.openclaw/workspace/projects/crypto-analysis')

from currency_strategies import (
    eth_strategy, btc_strategy, sol_strategy, xrp_strategy, bnb_strategy,
    get_strategy_config, STRATEGIES
)
from trade_reporter import report_trade

DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
INDICATORS_DIR = Path('/root/.openclaw/workspace/data/indicators')

def load_data(symbol: str, interval: str) -> List[Dict]:
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

def load_indicators(symbol: str) -> Dict:
    """Load calculated indicators"""
    filepath = INDICATORS_DIR / f"{symbol}_indicators.json"
    if not filepath.exists():
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def check_eth_setup() -> Optional[Dict]:
    """Check ETH using Selective Momentum Strategy v2"""
    data_1h = load_data('ETHUSDT', '1h')
    data_4h = load_data('ETHUSDT', '4h')
    indicators = load_indicators('ETHUSDT')
    
    if not data_1h:
        return None
    
    setup = eth_strategy(data_1h, data_4h, indicators)
    
    if setup:
        # Add position scaling info
        setup['position_scale_note'] = 'Enter 50% at signal, add 50% on confirmation'
        setup['strategy_version'] = 'v2.0 (with confirmation)'
    
    return setup

def check_btc_setup() -> Optional[Dict]:
    """Check BTC using Trend Following Strategy v2"""
    data_1h = load_data('BTCUSDT', '1h')
    data_1d = load_data('BTCUSDT', '1d')
    indicators = load_indicators('BTCUSDT')
    
    if not data_1h or not data_1d:
        return None
    
    setup = btc_strategy(data_1h, data_1d, indicators)
    
    if setup:
        setup['strategy_version'] = 'v2.0 (ADX + trend filters)'
    
    return setup

def check_sol_setup() -> Optional[Dict]:
    """Check SOL using EMA Momentum Strategy v2"""
    data_1h = load_data('SOLUSDT', '1h')
    indicators = load_indicators('SOLUSDT')
    
    if not data_1h:
        return None
    
    setup = sol_strategy(data_1h, indicators)
    
    if setup:
        setup['position_factor'] = 0.5
        setup['strategy_version'] = 'v2.0 (pullback entry)'
    
    return setup

def check_xrp_setup() -> Optional[Dict]:
    """XRP Strategy - DISABLED"""
    return None  # Strategy disabled

def check_bnb_setup() -> Optional[Dict]:
    """Check BNB using Extreme Selectivity Strategy v2"""
    data_1h = load_data('BNBUSDT', '1h')
    data_1d = load_data('BNBUSDT', '1d')
    indicators = load_indicators('BNBUSDT')
    
    if not data_1h or not data_1d:
        return None
    
    setup = bnb_strategy(data_1h, data_1d, indicators)
    
    if setup:
        setup['strategy_version'] = 'v2.0 (relaxed filters)'
    
    return setup

def print_setup(setup: Dict, symbol: str):
    """Print trade setup details"""
    if not setup:
        print(f"{symbol}: No setup found")
        return
    
    config = get_strategy_config(symbol)
    
    print(f"\n🎯 {symbol} {setup['direction']} SETUP FOUND")
    print(f"   Strategy: {setup.get('strategy', 'N/A')} {setup.get('strategy_version', '')}")
    
    if 'position_scale_note' in setup:
        print(f"   ⚠️  {setup['position_scale_note']}")
    
    print(f"   Entry: ${setup['entry']:.2f}")
    print(f"   Stop: ${setup['stop']:.2f} ({abs(setup['stop']-setup['entry'])/setup['entry']*100:.2f}%)")
    print(f"   Target: ${setup['target']:.2f} ({abs(setup['target']-setup['entry'])/setup['entry']*100:.2f}%)")
    
    if 'rr' in setup:
        print(f"   R:R Ratio: 1:{setup['rr']:.1f}")
    
    if 'position_factor' in setup:
        print(f"   Position Size: {setup['position_factor']*100:.0f}% of normal")
    
    # Print strategy-specific info
    if symbol == 'ETHUSDT':
        print(f"   Filters Applied:")
        print(f"     ✓ Volume > 1.0x average")
        print(f"     ✓ 2 consecutive bullish candles")
        print(f"     ✓ Close above breakout level")
        print(f"     ✓ ATR% < 4% (volatility check)")
    
    elif symbol == 'BTCUSDT':
        print(f"   Filters Applied:")
        print(f"     ✓ Daily trend bullish (price > EMA 20)")
        print(f"     ✓ ADX > 25 (trending market)")
        print(f"     ✓ Price in fib 0.5-0.618 zone")
        print(f"     ✓ Max 2 trades per day")
    
    elif symbol == 'SOLUSDT':
        print(f"   Filters Applied:")
        print(f"     ✓ EMA 12 > EMA 26")
        print(f"     ✓ ADX > 20")
        print(f"     ✓ Pullback to EMA 12 (within 2%)")

def main():
    """Main function - check all currencies with priority on ETH"""
    print("="*90)
    print("INDIVIDUAL SETUP CHECKER v2 - UNIQUE STRATEGIES PER CURRENCY")
    print("Priority: ETH (most successful strategy)")
    print("="*90)
    print()
    
    setups_found = []
    
    # Priority 1: ETH (most successful)
    print("🔍 Checking ETH (Priority 1 - Most Successful)...")
    eth_setup = check_eth_setup()
    print_setup(eth_setup, 'ETHUSDT')
    if eth_setup:
        setups_found.append(('ETHUSDT', eth_setup))
    print()
    
    # Priority 2: BTC (revised strategy)
    print("🔍 Checking BTC (Priority 2 - Revised Strategy)...")
    btc_setup = check_btc_setup()
    print_setup(btc_setup, 'BTCUSDT')
    if btc_setup:
        setups_found.append(('BTCUSDT', btc_setup))
    print()
    
    # Priority 3: SOL (improved strategy)
    print("🔍 Checking SOL (Priority 3 - Improved Strategy)...")
    sol_setup = check_sol_setup()
    print_setup(sol_setup, 'SOLUSDT')
    if sol_setup:
        setups_found.append(('SOLUSDT', sol_setup))
    print()
    
    # Priority 4: BNB (experimental)
    print("🔍 Checking BNB (Priority 4 - Experimental)...")
    bnb_setup = check_bnb_setup()
    print_setup(bnb_setup, 'BNBUSDT')
    if bnb_setup:
        setups_found.append(('BNBUSDT', bnb_setup))
    print()
    
    # XRP - Disabled
    print("🔍 Checking XRP...")
    print("   ❌ Strategy DISABLED - Underperforming (27% win rate)")
    print("   Recommendation: Redesign strategy before reactivating")
    print()
    
    # Summary
    print("="*90)
    print(f"SUMMARY: {len(setups_found)} setup(s) found")
    print("="*90)
    
    if setups_found:
        print("\n✅ SETUPS FOUND:")
        for symbol, setup in setups_found:
            print(f"   • {symbol}: {setup['direction']} @ ${setup['entry']:.2f}")
        
        # Generate reports with charts
        print("\n📊 Generating trade reports with charts...")
        for symbol, setup in setups_found:
            try:
                report_setup = {
                    'direction': setup['direction'],
                    'entry': setup['entry'],
                    'entry_low': setup['entry'] * 0.995,
                    'entry_high': setup['entry'] * 1.005,
                    'stop': setup['stop'],
                    'target': setup['target'],
                    'strategy': setup.get('strategy', 'Technical Setup'),
                    'position_factor': setup.get('position_factor', 1.0)
                }
                
                result = report_trade(symbol, report_setup)
                print(f"   ✅ Report generated for {symbol}")
            except Exception as e:
                print(f"   ⚠️  Could not generate report for {symbol}: {e}")
    else:
        print("\n⚠️  No setups found today")
        print("   ETH: Waiting for momentum breakout with confirmation")
        print("   BTC: Waiting for fib pullback in trending market")
        print("   SOL: Waiting for EMA pullback entry")
        print("   BNB: Waiting for trend + volume setup")
    
    print("\n" + "="*90)
    print("Strategy Versions:")
    print("  ETH: v2.0 (confirmation candle + position scaling)")
    print("  BTC: v2.0 (ADX filter + daily trend check)")
    print("  SOL: v2.0 (pullback entry + ADX filter)")
    print("  XRP: DISABLED")
    print("  BNB: v2.0 (relaxed filters)")
    print("="*90)

if __name__ == '__main__':
    main()
