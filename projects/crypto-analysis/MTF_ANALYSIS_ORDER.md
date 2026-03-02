# Multi-Timeframe Analysis Order

## Analysis Sequence (Top-Down Hierarchy)

The MTF analyzer processes timeframes in **hierarchical order** from **highest to lowest**:

```
1M → 1w → 1d → 4h → 1h → 15m → 5m
```

### Why This Order?

**Top-Down Analysis Principle:**
- Higher timeframes establish the **major trend** and **key structural levels**
- Lower timeframes provide **precision entry/exit** within the higher timeframe context
- Each timeframe inherits "bias" from the one above it

---

## Detailed Analysis Flow

### Step 1: Monthly (1M) - Macro Structure
**Purpose:** Identify long-term trend and major support/resistance
- Calculates EMA 50/200 for long-term trend
- Determines if market is in bull/bear phase
- Sets the "higher_tf_bias" for weekly analysis

### Step 2: Weekly (1w) - Major Trend
**Purpose:** Confirm long-term trend direction
- Uses bias from Monthly as context
- Identifies key swing highs/lows
- Updates "higher_tf_bias" for daily analysis

### Step 3: Daily (1d) - Trend Direction
**Purpose:** Determine intermediate trend
- Uses bias from Weekly as context
- Calculates trend alignment
- Updates "higher_tf_bias" for 4H analysis

### Step 4: 4-Hour (4h) - Trading Bias
**Purpose:** Establish trading direction
- Uses bias from Daily as context
- Key timeframe for swing trading
- Updates "higher_tf_bias" for 1H analysis

### Step 5: 1-Hour (1h) - Entry Timing
**Purpose:** Fine-tune entry timing
- Uses bias from 4H as context
- Identifies micro-structure
- Updates "higher_tf_bias" for 15M analysis

### Step 6: 15-Minute (15m) - Precision Entry
**Purpose:** Pinpoint entry zones
- Uses bias from 1H as context
- Liquidity heatmap analysis
- Updates "higher_tf_bias" for 5M analysis

### Step 7: 5-Minute (5m) - Execution
**Purpose:** Exact entry/exit execution
- Uses bias from 15M as context
- Liquidation heatmap for stop placement
- Final trade execution level

---

## Bias Propagation

```
Monthly Bias
    ↓ (inherited by)
Weekly Bias
    ↓ (inherited by)
Daily Bias
    ↓ (inherited by)
4H Bias
    ↓ (inherited by)
1H Bias
    ↓ (inherited by)
15M Bias
    ↓ (inherited by)
5M Bias (Final Execution)
```

### Alignment Scoring

Each timeframe is scored against the higher timeframe:
- **Aligned** (+30% strength) - Trend matches higher TF
- **Neutral** (0%) - No clear trend
- **Misaligned** (-30% strength) - Trend contradicts higher TF

**Minimum 3 aligned timeframes required for trade setup.**

---

## Example Analysis Output

```
Analyzing BTCUSDT
======================================================================
  Analyzing 1M... BULLISH | RSI: 58.2 | Confidence: high
  Analyzing 1w... BULLISH | RSI: 52.1 | Confidence: high  (Aligned with 1M)
  Analyzing 1d... BULLISH | RSI: 45.8 | Confidence: medium (Aligned with 1w)
  Analyzing 4h... BEARISH | RSI: 38.2 | Confidence: low   (Pullback in uptrend)
  Analyzing 1h... BEARISH | RSI: 35.5 | Confidence: low   (Continuation)
  Analyzing 15m... BULLISH | RSI: 42.1 | Confidence: medium (Bounce forming)
  Analyzing 5m... BULLISH | RSI: 48.5 | Confidence: medium (Entry trigger)
```

**Interpretation:**
- Monthly/Weekly/Daily = Bullish (major uptrend)
- 4H/1H = Bearish (pullback within uptrend)
- 15M/5M = Bullish (pullback ending, entry opportunity)

---

## Key Levels Carried Down

Each timeframe passes key levels to lower timeframes:

| From | To | Levels Passed |
|------|-----|---------------|
| 1M | 1w | Major swing highs/lows, EMA 200 |
| 1w | 1d | Weekly support/resistance, Fibonacci |
| 1d | 4h | Daily key levels, trend bias |
| 4h | 1h | 4H Fibonacci levels, structure |
| 1h | 15m | Hourly micro-structure |
| 15m | 5m | Liquidity walls, entry zones |

---

## Trade Setup Generation

After all 7 timeframes are analyzed:

1. **Count aligned timeframes** (minimum 3 required)
2. **Determine overall bias** (bullish/bearish/neutral)
3. **Calculate confidence %** (aligned / total)
4. **Generate entry/exit levels** from lowest timeframe Fibonacci
5. **Recommend position size** based on confidence

**No trade setup generated if:**
- Less than 3 timeframes aligned
- Confidence below 50%
- Mixed signals (no clear bias)

---

## Summary

| Phase | Timeframes | Purpose |
|-------|------------|---------|
| **Macro** | 1M, 1w | Long-term trend direction |
| **Intermediate** | 1d, 4h | Trading bias establishment |
| **Micro** | 1h, 15m | Entry timing precision |
| **Execution** | 5m | Exact entry/exit points |

**Total: 7 timeframes analyzed in sequence (1M → 5m)**
