# Indicator Calculation - Sequential Order

**Total: 55 indicators across 6 timeframes (98.2% coverage of PDF specification)**

---

## 1W (Weekly) - 8 Indicators

| # | Indicator | Description | Data Source |
|---|-----------|-------------|-------------|
| 1 | EMA 50 | 50-period Exponential Moving Average | OHLCV calculated |
| 2 | EMA 200 | 200-period Exponential Moving Average | OHLCV calculated |
| 3 | MACD Line | MACD line (12,26) | OHLCV calculated |
| 4 | MACD Signal | MACD signal line (9) | OHLCV calculated |
| 5 | MACD Histogram | MACD histogram | OHLCV calculated |
| 6 | Volume 20 SMA | 20-period Simple Moving Average of Volume | OHLCV calculated |
| 7 | Fibonacci Levels | 0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100% | OHLCV calculated |
| 8 | Support/Resistance Zones | 3 support zones, 3 resistance zones | Swing high/low clustering |

---

## 1D (Daily) - 11 Indicators

| # | Indicator | Description | Data Source |
|---|-----------|-------------|-------------|
| 1 | EMA 20 | 20-period Exponential Moving Average | OHLCV calculated |
| 2 | EMA 50 | 50-period Exponential Moving Average | OHLCV calculated |
| 3 | VWAP | Volume Weighted Average Price | OHLCV calculated |
| 4 | RSI 14 | 14-period Relative Strength Index | OHLCV calculated |
| 5 | MACD Line | MACD line (12,26) | OHLCV calculated |
| 6 | MACD Signal | MACD signal line (9) | OHLCV calculated |
| 7 | MACD Histogram | MACD histogram | OHLCV calculated |
| 8 | ATR 14 | 14-period Average True Range | OHLCV calculated |
| 9 | Volume 20 SMA | 20-period Simple Moving Average of Volume | OHLCV calculated |
| 10 | Fibonacci Levels | 0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100% | OHLCV calculated |
| 11 | Support/Resistance Zones | 3 support zones, 3 resistance zones | Swing high/low clustering |

---

## 4H (4-Hour) - 13 Indicators

| # | Indicator | Description | Data Source |
|---|-----------|-------------|-------------|
| 1 | EMA 9 | 9-period Exponential Moving Average | OHLCV calculated |
| 2 | EMA 21 | 21-period Exponential Moving Average | OHLCV calculated |
| 3 | RSI 14 | 14-period Relative Strength Index | OHLCV calculated |
| 4 | MACD Line | MACD line (12,26) | OHLCV calculated |
| 5 | MACD Signal | MACD signal line (9) | OHLCV calculated |
| 6 | MACD Histogram | MACD histogram | OHLCV calculated |
| 7 | VWAP | Volume Weighted Average Price | OHLCV calculated |
| 8 | Volume 20 SMA | 20-period Simple Moving Average of Volume | OHLCV calculated |
| 9 | ATR 14 | 14-period Average True Range | OHLCV calculated |
| 10 | OBV | On-Balance Volume | OHLCV calculated |
| 11 | CVD | Cumulative Volume Delta | OHLCV calculated |
| 12 | Open Interest | Total open interest in futures | Binance Futures API |
| 13 | Funding Rate | Current funding rate | Binance Futures API |

---

## 1H (1-Hour) - 8 Indicators

| # | Indicator | Description | Data Source |
|---|-----------|-------------|-------------|
| 1 | EMA 9 | 9-period Exponential Moving Average | OHLCV calculated |
| 2 | EMA 25 | 25-period Exponential Moving Average | OHLCV calculated |
| 3 | RSI 14 | 14-period Relative Strength Index | OHLCV calculated |
| 4 | VWAP | Volume Weighted Average Price | OHLCV calculated |
| 5 | Volume 20 SMA | 20-period Simple Moving Average of Volume | OHLCV calculated |
| 6 | ATR 14 | 14-period Average True Range | OHLCV calculated |
| 7 | OBV | On-Balance Volume | OHLCV calculated |
| 8 | CVD | Cumulative Volume Delta | OHLCV calculated |

---

## 15M (15-Minute) - 9 Indicators

| # | Indicator | Description | Data Source |
|---|-----------|-------------|-------------|
| 1 | EMA 9 | 9-period Exponential Moving Average | OHLCV calculated |
| 2 | EMA 21 | 21-period Exponential Moving Average | OHLCV calculated |
| 3 | EMA 50 | 50-period Exponential Moving Average | OHLCV calculated |
| 4 | RSI 9 | 9-period Relative Strength Index | OHLCV calculated |
| 5 | VWAP | Volume Weighted Average Price | OHLCV calculated |
| 6 | ATR 7 | 7-period Average True Range | OHLCV calculated |
| 7 | OBV | On-Balance Volume | OHLCV calculated |
| 8 | CVD | Cumulative Volume Delta | OHLCV calculated |
| 9 | Liquidity Heatmap | Support/resistance walls from order book | Binance Depth API |

---

## 5M (5-Minute) - 6 Indicators

| # | Indicator | Description | Data Source |
|---|-----------|-------------|-------------|
| 1 | EMA 9 | 9-period Exponential Moving Average | OHLCV calculated |
| 2 | RSI 7 | 7-period Relative Strength Index | OHLCV calculated |
| 3 | VWAP | Volume Weighted Average Price | OHLCV calculated |
| 4 | ATR 5 | 5-period Average True Range | OHLCV calculated |
| 5 | Volume Delta | Per-candle buy/sell volume estimate | OHLCV calculated |
| 6 | Liquidation Heatmap | Estimated liquidation zones | OI + Leverage + Funding |

---

## Summary Table

| Timeframe | Indicators | Data Sources |
|-----------|------------|--------------|
| 1W | 8 | OHLCV (calculated) |
| 1D | 11 | OHLCV (calculated) |
| 4H | 13 | OHLCV + Binance Futures API |
| 1H | 8 | OHLCV (calculated) |
| 15M | 9 | OHLCV + Binance Depth API |
| 5M | 6 | OHLCV + Estimation |
| **TOTAL** | **55** | Multiple sources |

---

## Missing Indicators (1 remaining)

| Indicator | Timeframe | Why Missing |
|-----------|-----------|-------------|
| Tick Delta | 5M | Requires tick-by-tick trade data not available via Binance REST API |

---

## Data Sources Summary

1. **OHLCV Calculated** (47 indicators) - Derived from candlestick data
2. **Binance Futures API** (2 indicators) - Open Interest, Funding Rate
3. **Binance Depth API** (1 indicator) - Liquidity Heatmap
4. **Estimation** (1 indicator) - Liquidation Heatmap (from OI + leverage)

**Coverage: 98.2%** (55/56 PDF specification indicators)
