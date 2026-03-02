# Pattern-Enhanced Chart Generator - Run Log

## 2026-03-02 17:59 (Asia/Shanghai)

### Summary
- **Total Charts Generated:** 21
- **Total Patterns Detected:** 748
- **Symbols:** BTCUSDT, ETHUSDT, BNBUSDT
- **Timeframes:** 5m, 15m, 1h, 4h, 1d, 1w, 1M

### Pattern Detection by Symbol
| Symbol | Total Patterns | Fibonacci Correlated |
|--------|---------------|---------------------|
| BTCUSDT | 255 | 139 |
| ETHUSDT | 237 | 113 |
| BNBUSDT | 256 | 114 |

### Generated Files
All charts saved to: `/root/.openclaw/workspace/projects/crypto-analysis/charts/`

- `index.html` - Dashboard with all chart links
- Individual charts: `{SYMBOL}_{TIMEFRAME}.html`

### Indicator Matrix Applied
| Timeframe | EMAs | RSI | MACD | VWAP | ATR | Fibonacci | S/R |
|-----------|------|-----|------|------|-----|-----------|-----|
| 5m | 9,21 | 5 | - | Session | 5 | ✓ | - |
| 15m | 9,21,50 | 7 | - | Micro | 7 | ✓ | - |
| 1h | 9,25 | 14 | - | Session | 14 | - | - |
| 4h | 9,21 | 14 | ✓ | Session | 14 | - | - |
| 1d | 20,50 | 14 | ✓ | Session | 14 | ✓ | - |
| 1w | 50,200 | - | ✓ | - | - | ✓ | ✓ |
| 1M | 50,200 | - | ✓ | - | - | ✓ | ✓ |

### Notes
- Pattern detection includes Japanese candlestick patterns with Fibonacci level correlation
- All charts include Bollinger Bands as baseline indicator
- Previous Day High/Low/Close lines included for intraday timeframes
