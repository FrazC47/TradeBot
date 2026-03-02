#!/usr/bin/env python3
"""
Liquidity Heatmap Generator - Analyzes order book depth for support/resistance zones
Uses Binance Futures API depth endpoint
"""

import requests
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path('/root/.openclaw/workspace/data/futures')
LIQUIDITY_DIR = Path('/root/.openclaw/workspace/data/liquidity')

FUTURES_API = 'https://fapi.binance.com/fapi/v1'
SPOT_API = 'https://api.binance.com/api/v3'

SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']

def fetch_order_book(symbol, limit=500, use_futures=True):
    """Fetch order book depth"""
    base_url = FUTURES_API if use_futures else SPOT_API
    endpoint = '/depth' if use_futures else '/depth'
    
    url = f"{base_url}{endpoint}"
    params = {
        'symbol': symbol,
        'limit': min(limit, 1000)  # Max 1000
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  Error fetching depth for {symbol}: {e}")
        return None

def analyze_liquidity(order_book, symbol, current_price=None):
    """Analyze order book for liquidity heatmap"""
    if not order_book:
        return None
    
    bids = [(float(p), float(q)) for p, q in order_book.get('bids', [])]
    asks = [(float(p), float(q)) for p, q in order_book.get('asks', [])]
    
    if not bids or not asks:
        return None
    
    # Get current price
    best_bid = bids[0][0]
    best_ask = asks[0][0]
    if current_price is None:
        current_price = (best_bid + best_ask) / 2
    
    # Calculate liquidity at different ranges
    ranges = [
        (0.001, '0.1%'),
        (0.005, '0.5%'),
        (0.01, '1%'),
        (0.02, '2%'),
        (0.05, '5%')
    ]
    
    liquidity_profile = {}
    for pct, label in ranges:
        lower = current_price * (1 - pct)
        upper = current_price * (1 + pct)
        
        bid_liq = sum(q for p, q in bids if p >= lower)
        ask_liq = sum(q for p, q in asks if p <= upper)
        
        bid_value = bid_liq * current_price
        ask_value = ask_liq * current_price
        
        liquidity_profile[label] = {
            'price_range': [round(lower, 2), round(upper, 2)],
            'bid_qty': round(bid_liq, 4),
            'ask_qty': round(ask_liq, 4),
            'bid_value_usd': round(bid_value, 2),
            'ask_value_usd': round(ask_value, 2),
            'imbalance': round((bid_liq - ask_liq) / (bid_liq + ask_liq + 0.0001), 4)
        }
    
    # Find walls (liquidity clusters)
    def find_walls(orders, side, cluster_size=100, top_n=5):
        """Find liquidity walls by clustering orders"""
        clusters = defaultdict(float)
        for p, q in orders[:100]:  # Top 100 orders
            cluster = round(p / cluster_size) * cluster_size
            clusters[cluster] += q
        
        sorted_walls = sorted(clusters.items(), key=lambda x: x[1], reverse=True)
        return [
            {
                'price': price,
                'qty': round(qty, 4),
                'value_usd': round(qty * current_price, 2),
                'distance_pct': round((price - current_price) / current_price * 100, 2)
            }
            for price, qty in sorted_walls[:top_n]
        ]
    
    support_walls = find_walls(bids, 'bid')
    resistance_walls = find_walls(asks, 'ask')
    
    # Calculate cumulative liquidity (what happens if price moves X%)
    cumulative = []
    for pct in [0.005, 0.01, 0.015, 0.02, 0.03, 0.05]:
        target_bid = current_price * (1 - pct)
        target_ask = current_price * (1 + pct)
        
        cum_bid = sum(q for p, q in bids if p >= target_bid)
        cum_ask = sum(q for p, q in asks if p <= target_ask)
        
        cumulative.append({
            'move_pct': pct * 100,
            'bid_liquidation_wall': round(cum_bid, 4),
            'ask_liquidation_wall': round(cum_ask, 4)
        })
    
    return {
        'timestamp': datetime.now().isoformat(),
        'symbol': symbol,
        'current_price': current_price,
        'spread': round(best_ask - best_bid, 2),
        'spread_pct': round((best_ask - best_bid) / current_price * 100, 4),
        'liquidity_profile': liquidity_profile,
        'support_walls': support_walls,
        'resistance_walls': resistance_walls,
        'cumulative_liquidity': cumulative,
        'total_bid_qty': round(sum(q for _, q in bids), 4),
        'total_ask_qty': round(sum(q for _, q in asks), 4)
    }

def generate_heatmap(symbol):
    """Generate liquidity heatmap for a symbol"""
    print(f"\n{symbol}:")
    print("-" * 60)
    
    # Fetch futures order book (more liquid)
    order_book = fetch_order_book(symbol, limit=500, use_futures=True)
    
    if not order_book:
        print("  ❌ Failed to fetch order book")
        return None
    
    # Analyze
    analysis = analyze_liquidity(order_book, symbol)
    
    if not analysis:
        print("  ❌ Failed to analyze liquidity")
        return None
    
    # Display summary
    print(f"  Price: {analysis['current_price']:,.2f}")
    print(f"  Spread: {analysis['spread']} ({analysis['spread_pct']:.4f}%)")
    print()
    
    print("  Liquidity Profile:")
    for label, data in analysis['liquidity_profile'].items():
        print(f"    {label:4s}: Bids ${data['bid_value_usd']:>15,.0f} | Asks ${data['ask_value_usd']:>15,.0f} | Imb: {data['imbalance']:+6.1%}")
    
    print()
    print("  Support Walls (Bid Liquidity):")
    for wall in analysis['support_walls'][:3]:
        print(f"    {wall['price']:>10,.2f}: {wall['qty']:>8.3f} ({wall['distance_pct']:+.2f}%)")
    
    print()
    print("  Resistance Walls (Ask Liquidity):")
    for wall in analysis['resistance_walls'][:3]:
        print(f"    {wall['price']:>10,.2f}: {wall['qty']:>8.3f} ({wall['distance_pct']:+.2f}%)")
    
    return analysis

def main():
    print("=" * 80)
    print("LIQUIDITY HEATMAP GENERATOR")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    LIQUIDITY_DIR.mkdir(parents=True, exist_ok=True)
    
    all_liquidity = {}
    
    for symbol in SYMBOLS:
        analysis = generate_heatmap(symbol)
        if analysis:
            all_liquidity[symbol] = analysis
    
    # Save to file
    output_file = LIQUIDITY_DIR / 'liquidity_heatmap.json'
    with open(output_file, 'w') as f:
        json.dump(all_liquidity, f, indent=2)
    
    print(f"\n  Saved liquidity data to: {output_file}")
    
    print()
    print("=" * 80)
    print("LIQUIDITY ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
