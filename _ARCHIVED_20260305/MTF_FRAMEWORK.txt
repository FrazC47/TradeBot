# Professional MTF Analysis Framework
## Sequential Flow & Logic

---

## Overview

This is a complete redesign of the MTF analysis system addressing all identified flaws:
- ✅ Regime detection (not just trend/bias)
- ✅ Weighted scoring (not simple counting)
- ✅ Signal state machine (prevents spam)
- ✅ Candle confirmation (not tick-based)
- ✅ Professional-grade architecture

---

## Sequential Analysis Flow

### **PHASE 1: Data Loading** (No analysis yet)

```
Step 1: Load Timeframe Data
├── 1M (Monthly):  104 candles ✓
├── 1w (Weekly):   447 candles ✓
├── 1d (Daily):    507 candles ✓
├── 4h (4-Hour):   542 candles ✓
├── 1h (1-Hour):   667 candles ✓
├── 15m (15-Min):  1142 candles ✓
└── 5m (5-Min):    229 candles ✓
```

**Logic:**
- Load ALL timeframes first
- Verify minimum candle requirements
- No analysis during loading
- Fail if < 4 timeframes available

---

### **PHASE 2: Regime Detection** (Top-down, per timeframe)

```
Step 2: Analyze Timeframes (1M → 5m)

1M:  ➖ NEUTRAL  | Regime: distribution    | Str: 0.60
1w:  ➖ NEUTRAL  | Regime: distribution    | Str: 0.60
1d:  ➖ NEUTRAL  | Regime: unknown         | Str: 0.30
4h:  ➖ NEUTRAL  | Regime: unknown         | Str: 0.30
1h:  ➖ NEUTRAL  | Regime: unknown         | Str: 0.30
15m: ➖ NEUTRAL  | Regime: range           | Str: 0.50
5m:  ➖ NEUTRAL  | Regime: unknown         | Str: 0.30
```

**Regime Detection Logic:**

```python
Regime Classification:
├── TREND_BULL      (structure > 0.5, ema > 0.4, momentum > 0.3)
├── TREND_BEAR      (structure < -0.5, ema < -0.4, momentum < -0.3)
├── PULLBACK_BULL   (trend structure but momentum < -0.2)
├── PULLBACK_BEAR   (trend structure but momentum > 0.2)
├── DISTRIBUTION    (weak structure, negative momentum)
├── ACCUMULATION    (weak structure, positive momentum)
├── RANGE           (no clear structure, low momentum)
└── UNKNOWN         (insufficient data)
```

**Inputs for Regime Detection:**
1. **Structure Score** (-1.0 to +1.0): Higher highs/lows vs lower highs/lows
2. **EMA Alignment** (-1.0 to +1.0): Price vs EMA9 vs EMA21 vs EMA50
3. **Momentum** (-1.0 to +1.0): Normalized RSI
4. **Volatility** (0.0 to 1.0): Annualized volatility

---

### **PHASE 3: Weighted MTF Scoring**

```
Step 3: Calculate Weighted MTF Score

Cluster Weights:
├── Macro (1M, 1w):        40% weight
├── Intermediate (1d, 4h): 35% weight
└── Execution (1h, 15m, 5m): 25% weight

Timeframe Weights:
├── 1M:  20% (of macro)
├── 1w:  20% (of macro)
├── 1d:  20% (of intermediate)
├── 4h:  15% (of intermediate)
├── 1h:  10% (of execution)
├── 15m: 10% (of execution)
└── 5m:   5% (of execution)
```

**Scoring Formula:**
```python
Cluster Score = Σ(direction × strength × weight × confidence) / Σ(weight × confidence)

Overall Score = (Macro × 0.40) + (Intermediate × 0.35) + (Execution × 0.25)
```

**Direction Thresholds:**
- BULLISH: Overall score > +0.2
- BEARISH: Overall score < -0.2
- NEUTRAL: Between -0.2 and +0.2

**Tradeable Requirements:**
- |Overall Score| >= 0.6
- Confidence >= 50%

---

### **PHASE 4: Signal State Management**

```
Step 4: Check Signal State Machine

Signal Lifecycle:
PENDING → ACTIVE → COOLDOWN → EXPIRED

State Transitions:
├── PENDING:   Signal detected, waiting candle confirmation
├── ACTIVE:    Confirmed, trade live
├── COOLDOWN:  Invalidated or completed, 120-min cooldown
└── EXPIRED:   No longer valid
```

**Duplicate Prevention:**
```python
Signal ID = {symbol}_{direction}_{entry_rounded_to_$100}

Checks:
├── If existing signal ACTIVE → Block new signal
├── If existing signal PENDING → Block new signal
├── If existing signal COOLDOWN (< 120 min) → Block new signal
└── If existing signal EXPIRED → Allow new signal
```

**Expiration Rules:**
- PENDING signals expire after 4 hours
- COOLDOWN signals expire after 120 minutes
- ACTIVE signals invalidated on structure break

---

### **PHASE 5: Trade Setup Generation** (Only if all conditions met)

```
Step 5: Generate Trade Setup (if tradeable)

Conditions Required:
1. MTF Score |overall| >= 0.6
2. Confidence >= 50%
3. No duplicate signal in state machine
4. Candle confirmation received

Trade Parameters:
├── Entry:     Fibonacci 0.618 level (from lowest TF)
├── Stop Loss: Fibonacci 0.786 level or ATR-based
├── Target:    Fibonacci 0.382 level (1:2 R:R minimum)
├── Size:      Risk-based (3% account, ATR-adjusted)
└── Leverage:  Volatility-adjusted (5x default, 3x high vol, 10x low vol)
```

---

## Complete Sequential Flow Diagram

```
START
  │
  ▼
┌─────────────────────────────────────┐
│ PHASE 1: DATA LOADING               │
│ Load all 7 timeframe CSV files      │
│ Verify minimum candle counts        │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ PHASE 2: REGIME DETECTION           │
│ For each timeframe (1M → 5m):       │
│   - Calculate structure score       │
│   - Calculate EMA alignment         │
│   - Calculate momentum              │
│   - Classify regime                 │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ PHASE 3: WEIGHTED MTF SCORING       │
│ - Add each timeframe to scorer      │
│ - Calculate cluster scores          │
│ - Calculate overall score           │
│ - Determine direction               │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ DECISION: Tradeable?                │
│ Score |0.6| AND Confidence 50%?     │
└─────────────────────────────────────┘
  │
  ├── NO ──→ Save analysis, END
  │
  ▼ YES
┌─────────────────────────────────────┐
│ PHASE 4: SIGNAL STATE CHECK         │
│ - Generate signal ID                │
│ - Check for duplicates              │
│ - Check cooldown status             │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ DECISION: Signal allowed?           │
│ No duplicate AND not in cooldown?   │
└─────────────────────────────────────┘
  │
  ├── NO ──→ Log blocked signal, END
  │
  ▼ YES
┌─────────────────────────────────────┐
│ PHASE 5: TRADE SETUP                │
│ - Calculate entry/stop/target       │
│ - Calculate position size           │
│ - Create signal (PENDING state)     │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ PHASE 6: CANDLE CONFIRMATION        │
│ Wait for next candle close          │
│ Validate signal still valid         │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│ DECISION: Confirmed?                │
│ Price action validates signal?      │
└─────────────────────────────────────┘
  │
  ├── NO ──→ Invalidate, cooldown, END
  │
  ▼ YES
┌─────────────────────────────────────┐
│ SIGNAL ACTIVE                       │
│ Alert user with trade details       │
│ Monitor for invalidation            │
└─────────────────────────────────────┘
  │
  ▼
END
```

---

## Key Improvements Over Old System

| Aspect | Old System | New System |
|--------|------------|------------|
| **Regime** | Trend/Bias only | 7 regimes (trend, pullback, distribution, etc.) |
| **Scoring** | Simple count (min 3 aligned) | Weighted clusters (macro 40%, intermediate 35%, execution 25%) |
| **Timeframe Weights** | Equal | Hierarchical (1M=20%, 5m=5%) |
| **Signal Control** | None (spam) | State machine with cooldown |
| **Confirmation** | Tick-based | Candle-close based |
| **Invalidation** | Undefined | Clear rules (structure break, timeout) |
| **Duplicates** | Allowed | Blocked by signal ID |

---

## Files Created

```
projects/crypto-analysis/core/
├── regime_detector.py          # Market regime classification
├── weighted_mtf_scorer.py      # Weighted cluster scoring
├── signal_state_machine.py     # Signal lifecycle management
└── professional_mtf_engine.py  # Main orchestrator
```

---

## Next Steps (If Approved)

1. **Add candle confirmation logic** (wait for close, not tick)
2. **Add dynamic position sizing** (ATR-based, volatility-adjusted)
3. **Add liquidity context** (order blocks, imbalances)
4. **Add invalidation rules** (structure break detection)
5. **Integration with existing setup checker**

Ready to proceed with any of these or review current implementation.
