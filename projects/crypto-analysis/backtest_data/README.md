# AI Backtest Data Package
## Multi-Currency Trading Strategy Configurations

**Generated:** March 3, 2026
**Account:** $1000 Binance Futures with 5x Leverage
**Purpose:** Shareable backtest data for AI systems

---

## File Structure

```
backtest_data/
├── README.md                          # This file
├── MASTER_SUMMARY.csv                 # Portfolio-level summary
├── BTCUSDT_strategy_config.csv        # BTC strategy parameters
├── BTCUSDT_trade_history.csv          # BTC trade history
├── ETHUSDT_strategy_config.csv        # ETH strategy parameters
├── ETHUSDT_trade_history.csv          # ETH trade history
├── SOLUSDT_strategy_config.csv        # SOL strategy parameters
├── SOLUSDT_trade_history.csv          # SOL trade history
├── XRPUSDT_strategy_config.csv        # XRP strategy parameters
├── XRPUSDT_trade_history.csv          # XRP trade history
└── BNBUSDT_strategy_config.csv        # BNB strategy parameters
```

---

## Quick Reference

| Symbol | Strategy | Win Rate | P&L | Status |
|--------|----------|----------|-----|--------|
| BTC | Fibonacci Pullback | 35.9% | -100% | ❌ REVISE |
| ETH | Selective Momentum | 58.6% | +662% | ✅ EXCELLENT |
| SOL | EMA Crossover | 44.4% | -6% | ⚠️ MARGINAL |
| XRP | EMA Crossover | 27.3% | -31% | ❌ STOP |
| BNB | Extreme Selectivity | N/A | 0% | ⚠️ TESTING |

---

## Using This Data

### For AI Backtesting:

1. **Load Strategy Config:** Parse the `_strategy_config.csv` files for parameters
2. **Load Trade History:** Use `_trade_history.csv` for validation
3. **Simulate:** Apply fees and leverage as specified in ACCOUNT section
4. **Validate:** Compare results against BACKTEST_RESULTS section

### Key Parameters:

- **Taker Fee:** 0.05% (entry and exit)
- **Maker Fee:** 0.02%
- **Funding Fee:** ~0.01% per 8h
- **Leverage:** 5x
- **Risk per Trade:** 3% (1.5% for SOL/XRP)

### Fee Calculation:
```
Total Fees = (Position Size × 0.0005 × 2) + (Position Size × 0.0001 × 3)
           = Entry Fee + Exit Fee + Funding (3 periods)
```

---

## Strategy Classifications

### ✅ PRODUCTION READY
- **ETHUSDT:** +662% return, 58.6% win rate, PF 3.48

### ⚠️ NEEDS OPTIMIZATION
- **SOLUSDT:** Nearly break-even, needs more data
- **BNBUSDT:** No trades yet, filters too strict

### ❌ DO NOT USE
- **BTCUSDT:** -100% loss, overtrading issue
- **XRPUSDT:** -31% loss, low win rate

---

## Contact
For questions about strategy logic, contact the trading system administrator.
