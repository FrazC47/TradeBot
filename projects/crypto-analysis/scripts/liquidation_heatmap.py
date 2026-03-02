#!/usr/bin/env python3
"""
Liquidation Heatmap Estimator - Estimates liquidation zones from OI and price levels
Since Binance liquidation data requires API authentication, we estimate based on:
1. Open Interest concentration at price levels
2. Leverage estimates (from funding rates)
3. Historical liquidation clusters
"""

import requests
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path('/root/.openclaw/workspace/data/futures')
LIQUIDITY_DIR = Path('/root/.openclaw/workspace/data/liquidity')
LIQUIDATION_DIR = Path('/root/.openclaw/workspace/data/liquidations')

FUTURES_API = 'https://fapi.binance.com/fapi/v1'

SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']

# Estimated average leverage by symbol (based on typical Binance Futures usage)
DEFAULT_LEVERAGE = {
    'BTCUSDT': 20,
    'ETHUSDT': 25,
    'BNBUSDT': 15,
    'SOLUSDT': 20,
    'XRPUSDT': 15
}

def fetch_open_interest_stats(symbol, period='1h'):
    """Fetch Open Interest statistics"""
    url = f"{FUTURES_API}/openInterestHist"
    params = {
        'symbol': symbol,
        'period': period,
        'limit': 100
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  Error fetching OI stats: {e}")
        return None

def fetch_long_short_ratio(symbol, period='1h'):
    """
    Fetch top trader long/short account ratio
    """
    url = f"https://fapi.binance.com/futures/data/topLongShortAccountRatio"
    params = {
        'symbol': symbol,
        'period': period,
        'limit': 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  Error fetching ratio: {e}")
        return None

def fetch_taker_volume_ratio(symbol, period='1h'):
    """Fetch taker buy/sell volume ratio"""
    url = f"{FUTURES_API}/takerlongshortRatio"
    params = {
        'symbol': symbol,
        'period': period,
        'limit': 100
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  Error fetching taker ratio: {e}")
        return None

def fetch_recent_trades(symbol, limit=1000):
    """Fetch recent trades to estimate activity"""
    url = f"{FUTURES_API}/aggTrades"
    params = {
        'symbol': symbol,
        'limit': limit
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  Error fetching trades: {e}")
        return None

def estimate_liquidation_zones(symbol, current_price, open_interest, leverage=20):
    """
    Estimate liquidation zones based on leverage and OI
    
    At X leverage:
    - Long liquidation when price drops ~ (100/X)%
    - Short liquidation when price rises ~ (100/X)%
    
    We estimate clusters at standard leverage tiers
    """
    zones = []
    
    # Standard leverage tiers on Binance Futures
    leverage_tiers = [5, 10, 20, 50, 100]
    
    for lev in leverage_tiers:
        # Maintenance margin is typically 0.5% - 2.5% depending on position size
        # Liquidation happens when margin < maintenance margin
        # Rough estimate: liquidation at ~ (100/lev) - 1% buffer
        liquidation_pct = (100 / lev) - 1.0  # -1% buffer for maintenance margin
        
        if liquidation_pct <= 0:
            continue
        
        # Long liquidation zone (below current price)
        long_liq_price = current_price * (1 - liquidation_pct / 100)
        
        # Short liquidation zone (above current price)
        short_liq_price = current_price * (1 + liquidation_pct / 100)
        
        # Estimate liquidation amount (proportional to OI and inversely to leverage)
        # Higher leverage = more liquidations at smaller moves
        estimated_liq_amount = open_interest * (1 / lev) * 0.1  # 10% of positions at risk
        
        zones.append({
            'leverage_tier': lev,
            'liquidation_pct': round(liquidation_pct, 2),
            'long_liquidation_price': round(long_liq_price, 2),
            'short_liquidation_price': round(short_liq_price, 2),
            'distance_pct_long': round(-liquidation_pct, 2),
            'distance_pct_short': round(liquidation_pct, 2),
            'estimated_liquidation_value_usd': round(estimated_liq_amount * current_price, 2)
        })
    
    return zones

def analyze_funding_impact(funding_rate):
    """
    Analyze funding rate impact on liquidation risk
    Positive funding = longs pay shorts = potential long liquidation pressure
    Negative funding = shorts pay longs = potential short liquidation pressure
    """
    if funding_rate > 0.0001:  # > 0.01%
        return {
            'bias': 'short',
            'pressure': 'long_liquidation',
            'intensity': 'high' if funding_rate > 0.001 else 'medium'
        }
    elif funding_rate < -0.0001:  # < -0.01%
        return {
            'bias': 'long',
            'pressure': 'short_liquidation',
            'intensity': 'high' if funding_rate < -0.001 else 'medium'
        }
    else:
        return {
            'bias': 'neutral',
            'pressure': 'none',
            'intensity': 'low'
        }

def generate_liquidation_heatmap(symbol):
    """Generate estimated liquidation heatmap for a symbol"""
    print(f"\n{symbol}:")
    print("-" * 70)
    
    # Load latest futures data
    latest_file = DATA_DIR / 'latest_futures_data.json'
    if not latest_file.exists():
        print("  ❌ No futures data available")
        return None
    
    with open(latest_file, 'r') as f:
        futures_data = json.load(f).get(symbol, {})
    
    if not futures_data:
        print("  ❌ No data for symbol")
        return None
    
    current_price = futures_data.get('mark_price', 0)
    open_interest = futures_data.get('open_interest', 0)
    funding_rate = futures_data.get('funding_rate', 0)
    
    if not current_price:
        print("  ❌ No price data")
        return None
    
    leverage = DEFAULT_LEVERAGE.get(symbol, 20)
    
    # Estimate liquidation zones
    liq_zones = estimate_liquidation_zones(symbol, current_price, open_interest, leverage)
    
    # Analyze funding impact
    funding_impact = analyze_funding_impact(funding_rate)
    
    # Fetch long/short ratio
    ls_ratio = fetch_long_short_ratio(symbol)
    long_short_ratio = 1.0
    if ls_ratio and len(ls_ratio) > 0:
        long_short_ratio = float(ls_ratio[0].get('longShortRatio', 1.0))
    
    # Calculate heat scores
    for zone in liq_zones:
        # Higher heat if:
        # 1. Funding pressure aligns with liquidation direction
        # 2. High OI at that leverage tier
        # 3. Extreme long/short ratio
        
        heat_score = 0
        
        # Funding alignment bonus
        if funding_impact['pressure'] == 'long_liquidation':
            heat_score += 30  # Long liquidations more likely
        elif funding_impact['pressure'] == 'short_liquidation':
            heat_score += 20  # Short liquidations slightly less common
        
        # Long/short imbalance
        if long_short_ratio > 1.5:  # More longs
            heat_score += 20  # Long liquidation risk higher
        elif long_short_ratio < 0.67:  # More shorts
            heat_score += 15  # Short liquidation risk higher
        
        # Leverage tier (higher leverage = more liquidations)
        if zone['leverage_tier'] >= 50:
            heat_score += 25
        elif zone['leverage_tier'] >= 20:
            heat_score += 15
        
        zone['heat_score'] = min(100, heat_score)
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'symbol': symbol,
        'current_price': current_price,
        'open_interest': open_interest,
        'funding_rate': funding_rate,
        'funding_impact': funding_impact,
        'long_short_ratio': long_short_ratio,
        'estimated_leverage': leverage,
        'liquidation_zones': liq_zones,
        'nearest_long_liquidation': next((z for z in liq_zones if z['distance_pct_long'] < 0), None),
        'nearest_short_liquidation': next((z for z in liq_zones if z['distance_pct_short'] > 0), None)
    }
    
    # Display summary
    print(f"  Price: ${current_price:,.2f}")
    print(f"  Open Interest: {open_interest:,.0f} contracts")
    print(f"  Funding Rate: {funding_rate:.4%}")
    print(f"  Long/Short Ratio: {long_short_ratio:.2f}")
    print(f"  Funding Bias: {funding_impact['bias']} ({funding_impact['intensity']})")
    print()
    print("  Estimated Liquidation Zones:")
    print(f"  {'Leverage':<10} {'Long Liq':<15} {'Short Liq':<15} {'Est. Value':<15} {'Heat':<6}")
    print("  " + "-" * 65)
    for zone in liq_zones:
        print(f"  {zone['leverage_tier']}x{'':<7} ${zone['long_liquidation_price']:<14,.0f} ${zone['short_liquidation_price']:<14,.0f} ${zone['estimated_liquidation_value_usd']:<14,.0f} {zone['heat_score']}/100")
    
    return result

def main():
    print("=" * 80)
    print("LIQUIDATION HEATMAP ESTIMATOR")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    print("Note: Binance liquidation data requires API authentication.")
    print("This tool estimates liquidation zones based on OI, leverage, and funding rates.")
    print()
    
    LIQUIDATION_DIR.mkdir(parents=True, exist_ok=True)
    
    all_liquidations = {}
    
    for symbol in SYMBOLS:
        analysis = generate_liquidation_heatmap(symbol)
        if analysis:
            all_liquidations[symbol] = analysis
    
    # Save to file
    output_file = LIQUIDATION_DIR / 'liquidation_heatmap.json'
    with open(output_file, 'w') as f:
        json.dump(all_liquidations, f, indent=2)
    
    print(f"\n  Saved liquidation data to: {output_file}")
    
    print()
    print("=" * 80)
    print("LIQUIDATION ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
