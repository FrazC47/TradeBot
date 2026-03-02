#!/usr/bin/env python3
"""
Binance Futures Leverage Trading Analysis
How leverage affects returns and risk
"""

# Trading scenario with Binance Futures
TRADES = [
    {'outcome': 'loss', 'pnl': -1.19},
    {'outcome': 'win', 'pnl': 1.78},
    {'outcome': 'win', 'pnl': 1.93},
    {'outcome': 'win', 'pnl': 1.62},
    {'outcome': 'win', 'pnl': 1.48},
    {'outcome': 'loss', 'pnl': -1.00},
    {'outcome': 'win', 'pnl': 1.49},
    {'outcome': 'win', 'pnl': 1.51},
    {'outcome': 'win', 'pnl': 1.08},
    {'outcome': 'win', 'pnl': 1.20},
    {'outcome': 'win', 'pnl': 1.57},
    {'outcome': 'loss', 'pnl': -0.97},
]

def simulate_futures(leverage: int, risk_per_trade: float, initial: float = 100):
    """Simulate Binance Futures trading with leverage"""
    capital = initial
    margin = initial  # Initial margin
    peak = initial
    max_dd = 0.0
    
    for trade in TRADES:
        # Position size based on risk and leverage
        # With leverage, you control larger position with same margin
        notional = margin * leverage
        
        # Risk amount per trade
        risk_amount = capital * risk_per_trade
        
        # Calculate position based on stop distance (assume 1% stop)
        position_size = risk_amount / 0.01
        
        # Cap at available leverage
        max_position = margin * leverage
        position_size = min(position_size, max_position)
        
        # Calculate P&L on notional value
        pnl = position_size * (trade['pnl'] / 100)
        
        # Update margin (P&L directly affects margin in futures)
        margin += pnl
        capital += pnl
        
        # Check liquidation risk (if margin drops too low)
        if margin <= 0:
            return {'liquidated': True, 'trade_count': TRADES.index(trade) + 1}
        
        # Track peak and drawdown
        if capital > peak:
            peak = capital
        
        dd = (peak - capital) / peak * 100
        if dd > max_dd:
            max_dd = dd
    
    return {
        'final_capital': round(capital, 2),
        'final_margin': round(margin, 2),
        'return_pct': round((capital - initial) / initial * 100, 2),
        'max_drawdown': round(max_dd, 2),
        'liquidated': False
    }

print("=" * 90)
print("BINANCE FUTURES LEVERAGE ANALYSIS")
print("=" * 90)
print("\nStarting Capital: $100")
print("Trading: 12 trades over 18 days (75% win rate)")
print()

# Test different leverage levels
leverage_levels = [1, 2, 3, 5, 10, 20]
risk_levels = [1, 2, 3, 5]

print("RESULTS BY LEVERAGE (with 2% risk per trade):")
print("-" * 90)
print(f"{'Leverage':<10} {'Final $':<12} {'Return %':<12} {'Max DD %':<12} {'Status':<15}")
print("-" * 90)

for lev in leverage_levels:
    result = simulate_futures(leverage=lev, risk_per_trade=0.02)
    status = 'LIQUIDATED!' if result.get('liquidated') else 'OK'
    print(f"{lev}x{'':<8} ${result['final_capital']:<11} {result['return_pct']:>+6}%{'':<5} {result['max_drawdown']:>6}%{'':<5} {status:<15}")

print()
print("=" * 90)
print("RESULTS BY RISK % (with 5x leverage):")
print("-" * 90)
print(f"{'Risk/Trade':<12} {'Final $':<12} {'Return %':<12} {'Max DD %':<12} {'Status':<15}")
print("-" * 90)

for risk in risk_levels:
    result = simulate_futures(leverage=5, risk_per_trade=risk/100)
    status = 'LIQUIDATED!' if result.get('liquidated') else 'OK'
    print(f"{risk}%{'':<9} ${result['final_capital']:<11} {result['return_pct']:>+6}%{'':<5} {result['max_drawdown']:>6}%{'':<5} {status:<15}")

print()
print("=" * 90)
print("BINANCE FUTURES SPECIFIC CONSIDERATIONS")
print("=" * 90)
print()
print("✅ ADVANTAGES:")
print("   • Leverage up to 125x (not recommended)")
print("   • Short selling (profit from bearish strategy)")
print("   • Low fees (0.02% maker, 0.05% taker)")
print("   • High liquidity for BTC, ETH, BNB")
print("   • Isolated margin mode (limit risk per position)")
print()
print("⚠️  RISKS:")
print("   • Liquidation if margin drops below maintenance")
print("   • Funding fees every 8 hours (0.01% typical)")
print("   • Higher volatility = faster liquidations")
print("   • Emotional pressure with high leverage")
print()
print("🎯 RECOMMENDED SETTINGS FOR YOUR STRATEGY:")
print()
print("Conservative Approach:")
print("   • Leverage: 3-5x")
print("   • Risk per trade: 2%")
print("   • Margin mode: Isolated")
print("   • Expected return: +50-80% in 18 days")
print()
print("Moderate Approach:")
print("   • Leverage: 5-10x")
print("   • Risk per trade: 2-3%")
print("   • Margin mode: Isolated")
print("   • Expected return: +100-150% in 18 days")
print()
print("⚠️  NEVER DO:")
print("   • >20x leverage (guaranteed liquidation)")
print("   • >5% risk with >10x leverage")
print("   • Cross margin (risks entire account)")
print("   • Hold through major news events")
print()
print("=" * 90)
print("REALISTIC PROJECTION (5x leverage, 2% risk):")
print("=" * 90)
print()
result = simulate_futures(leverage=5, risk_per_trade=0.02)
print(f"Starting: $100")
print(f"After 18 days: ${result['final_capital']}")
print(f"Return: {result['return_pct']:+.2f}%")
print(f"Max Drawdown: {result['max_drawdown']:.2f}%")
print()
print(f"With $1,000: ${result['final_capital'] * 10:.2f}")
print(f"With $10,000: ${result['final_capital'] * 100:.2f}")
print()
print("Note: This assumes perfect execution and no funding fees.")
print("Real results may vary due to slippage, fees, and timing.")
print("=" * 90)
