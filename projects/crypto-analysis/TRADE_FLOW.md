# Trade Identification Flow - Sequential Procedure

## Overview
This document describes the exact procedure executed each time data is refreshed to identify trade setups.

## Data Refresh Schedule
- **Frequency**: Every 5 minutes (cron job)
- **Data source**: Binance API (futures)
- **Timeframes**: 5m, 15m, 1h, 4h, 1d, 1w, 1M

---

## Sequential Flow

### Step 1: Data Collection (0-30 seconds)
```
For each symbol (BTC, ETH, BNB):
  1. Fetch latest OHLCV data from Binance
  2. Update CSV files: data/binance/{SYMBOL}/{INTERVAL}.csv
  3. Verify data integrity (no gaps, timestamps aligned)
```

### Step 2: Multi-Timeframe Analysis (30-60 seconds)
```
Run mtf_analyzer.py:
  1. Analyze top-down: 1M → 1w → 1d → 4h → 1h → 15m → 5m
  2. For each timeframe:
     - Calculate EMA9, EMA25, EMA50
     - Calculate VWAP
     - Calculate RSI(14)
     - Calculate MACD
     - Calculate ATR(14)
     - Identify Fibonacci levels (20-period high/low)
     - Detect patterns (engulfing, hammer, shooting star)
  3. Carry higher TF context down:
     - Trend direction
     - Key support/resistance
     - Fibonacci levels
     - Divergence signals
  4. Save to: mtf_analysis/{SYMBOL}_mtf_*.json
```

### Step 3: Symbol-Specific Setup Detection (60-90 seconds)
```
Run check_setups.py:
  
  For BTC (Fibonacci Pullback Strategy):
    1. Check daily trend alignment (5-day comparison)
    2. If bullish daily:
       - Look for price within 1% of 0.618, 0.5, or 0.382 Fib
       - Check RSI < 70
       - Check volume > 0.8x average
       - Calculate stop: entry - (ATR * 3.0)
       - Calculate target: entry + (ATR * 6.0)
    3. If bearish daily:
       - Same logic inverted
    4. If setup found:
       - Calculate position size (3% risk, 5x leverage)
       - Format alert message
       - Send notification
  
  For ETH (Momentum Breakout Strategy):
    1. Calculate 20-period high/low
    2. Check volume > 1.2x average
    3. If price > 20-high * 1.005:
       - Long entry
       - Stop: 20-period low
       - Target: entry + (entry - stop) * 2
    4. If price < 20-low * 0.995:
       - Short entry
       - Stop: 20-period high
       - Target: entry - (stop - entry) * 2
    5. If setup found:
       - Calculate position size
       - Send notification
  
  For BNB (Extreme Selectivity):
    1. Check daily trend > 5% over 10 days
    2. Check volume > 1.5x average
    3. If trend bullish:
       - Look for price at 0.5 Fib level
       - Check RSI < 65
       - Calculate stop: entry - (ATR * 3.0)
       - Calculate target: entry + (ATR * 6.0)
    4. If trend bearish:
       - Same logic inverted
    5. If setup found:
       - Calculate position size
       - Send notification
```

### Step 4: Futures Divergence Check (90-120 seconds)
```
Run futures_ohlcv_divergence.py:
  1. Compare spot vs futures prices
  2. Calculate funding rate impact
  3. If significant divergence (>0.5%):
     - Note in setup context
     - Adjust position sizing if needed
```

### Step 5: Alert Generation (120-150 seconds)
```
If any setups found:
  1. Format alert with:
     - Symbol and direction
     - Entry price
     - Stop loss
     - Target
     - Position size (USD)
     - R:R ratio
     - Setup type (Fib pullback, Breakout, etc.)
     - Confidence score
  2. Send to configured channels
  
If no setups:
  - Silent (no output)
```

### Step 6: Chart Generation (Background/async)
```
Generate/update charts:
  - charts/{SYMBOL}_{INTERVAL}.html
  - Include all indicators
  - Mark recent setups if any
```

---

## Decision Tree

```
Data Refresh Triggered
         │
         ▼
┌─────────────────────┐
│ 1. Fetch new data   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. MTF Analysis     │
│    (all timeframes) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 3. Check BTC        │
│    Fib pullback?    │
└──────────┬──────────┘
     Yes /   \ No
        /     \
       ▼       ▼
  [Alert]   [Continue]
                │
                ▼
       ┌─────────────────┐
       │ 4. Check ETH    │
       │   Breakout?     │
       └────────┬────────┘
          Yes /   \ No
             /     \
            ▼       ▼
       [Alert]   [Continue]
                     │
                     ▼
            ┌─────────────────┐
            │ 5. Check BNB    │
            │   Extreme?      │
            └────────┬────────┘
               Yes /   \ No
                  /     \
                 ▼       ▼
            [Alert]   [Silent]
                         │
                         ▼
                    [End Cycle]
```

---

## Alert Format Example

```
🎯 TRADE SETUP: BTCUSDT LONG

Strategy: Fibonacci Pullback
Entry: $62,450.00
Stop: $61,850.00 (-0.96%)
Target: $64,150.00 (+2.72%)
R:R = 1:2.8

Position: $1,500 (5x leverage)
Risk: $45 (3% of account)

Context:
• Daily trend: Bullish (+3.2% over 5 days)
• At 0.618 Fib level
• RSI: 58 (neutral)
• Volume: 1.1x average

Confidence: 75%
```

---

## Cron Jobs

```bash
# Every 5 minutes
*/5 * * * * cd /root/.openclaw/workspace && python3 projects/crypto-analysis/scripts/check_setups.py

# Every 15 minutes
*/15 * * * * cd /root/.openclaw/workspace && python3 futures_ohlcv_divergence.py

# Every hour
0 * * * * cd /root/.openclaw/workspace && python3 mtf_analyzer.py
```

---

## Files Involved

| File | Purpose |
|------|---------|
| `check_setups.py` | Main setup detection |
| `mtf_analyzer.py` | Multi-timeframe analysis |
| `futures_ohlcv_divergence.py` | Spot-futures comparison |
| `FINAL_STRATEGIES_V3.json` | Strategy parameters |
| `data/binance/{SYMBOL}/{TF}.csv` | Price data |
| `mtf_analysis/{SYMBOL}_mtf_*.json` | MTF context |
