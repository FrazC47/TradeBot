# Professional MTF Analysis Framework v2
## Production-Grade Specification

---

## 1. WEIGHTED SCORING (Mathematically Consistent)

### Cluster Weights (sum = 1.0)
| Cluster | Weight | Timeframes |
|---------|--------|------------|
| Macro | 0.40 | 1M, 1W |
| Intermediate | 0.35 | 1D, 4H |
| Execution | 0.25 | 1H, 15M, 5M |

### Within-Cluster Weights (each sums to 1.0)
**Macro Cluster:**
- 1M: 0.50
- 1W: 0.50

**Intermediate Cluster:**
- 1D: 0.60
- 4H: 0.40

**Execution Cluster:**
- 1H: 0.40
- 15M: 0.40
- 5M: 0.20

### Final Weight Calculation
```python
# Effective weight = cluster_weight × within_cluster_weight
1M:  0.40 × 0.50 = 0.20
1W:  0.40 × 0.50 = 0.20
1D:  0.35 × 0.60 = 0.21
4H:  0.35 × 0.40 = 0.14
1H:  0.25 × 0.40 = 0.10
15M: 0.25 × 0.40 = 0.10
5M:  0.25 × 0.20 = 0.05

# Verify: 0.20 + 0.20 + 0.21 + 0.14 + 0.10 + 0.10 + 0.05 = 1.00 ✓
```

### Scoring Formula
```python
TF_contrib = direction × strength × confidence × within_cluster_weight

ClusterScore = Σ(TF_contrib) / Σ(within_cluster_weight × confidence)

OverallScore = (0.40 × Macro) + (0.35 × Intermediate) + (0.25 × Execution)
```

---

## 2. BIAS vs TRADEABLE THRESHOLDS (Clear Separation)

### Bias Classification
| Score Range | Bias Label |
|-------------|------------|
| ≥ +0.20 | BullishBias |
| ≤ -0.20 | BearishBias |
| -0.20 to +0.20 | NeutralBias |

### Tradeable Requirements
| Requirement | Threshold |
|-------------|-----------|
| Overall Score | \|score\| ≥ 0.45 |
| Confidence | ≥ 0.50 |
| Minimum Timeframes | 4 of 7 |

### Decision Matrix
```
Score = +0.50, Confidence = 0.60 → BullishBias + Tradeable ✓
Score = +0.30, Confidence = 0.70 → BullishBias + Not Tradeable
Score = +0.15, Confidence = 0.80 → NeutralBias + Not Tradeable
Score = -0.55, Confidence = 0.45 → BearishBias + Not Tradeable (low confidence)
```

---

## 3. REGIME DEFINITIONS (Volume-Optional)

### Option B: Enhanced Definitions with Structure Conditions

```python
TREND_BULL:
  - structure > +0.50 (higher highs/lows)
  - ema_alignment > +0.40
  - momentum > +0.20
  - NOT in range (range_pct < 0.10)

TREND_BEAR:
  - structure < -0.50 (lower highs/lows)
  - ema_alignment < -0.40
  - momentum < -0.20
  - NOT in range (range_pct < 0.10)

PULLBACK_BULL:
  - structure > +0.30 (still higher highs/lows)
  - ema_alignment > +0.20
  - momentum < -0.20 (temporary weakness)
  - price > key_support (structure intact)

PULLBACK_BEAR:
  - structure < -0.30 (still lower highs/lows)
  - ema_alignment < -0.20
  - momentum > +0.20 (temporary strength)
  - price < key_resistance (structure intact)

RANGE:
  - range_pct > 0.15 (15% of price)
  - \|structure\| < 0.30
  - \|ema_alignment\| < 0.30

RANGE_BULL_DRIFT:  # Renamed from ACCUMULATION
  - RANGE conditions
  - higher lows within range
  - momentum > +0.10

RANGE_BEAR_DRIFT:  # Renamed from DISTRIBUTION
  - RANGE conditions
  - lower highs within range
  - momentum < -0.10

BREAKOUT:
  - Previous regime = RANGE
  - Close > range_high + ATR
  - Volume > 1.5 × avg (if available)

BREAKDOWN:
  - Previous regime = RANGE
  - Close < range_low - ATR
  - Volume > 1.5 × avg (if available)
```

---

## 4. MOMENTUM CALCULATION (Enhanced)

```python
def calculate_momentum(closes, period=14, roc_bars=5):
    """
    Combined RSI + Rate of Change momentum
    """
    # RSI component (60%)
    rsi = calculate_rsi(closes, period)
    rsi_norm = (rsi - 50) / 25  # Maps 25-75 RSI to -1 to +1
    rsi_norm = max(-1, min(1, rsi_norm))  # Clip
    
    # ROC component (40%)
    if len(closes) >= roc_bars + 1:
        atr = calculate_atr(closes, period)
        roc = (closes[-1] - closes[-roc_bars-1]) / closes[-roc_bars-1]
        roc_norm = roc / (atr / closes[-1] * 5)  # Normalize by ATR
        roc_norm = max(-1, min(1, roc_norm))  # Clip
    else:
        roc_norm = 0
    
    # Combined
    momentum = 0.6 * rsi_norm + 0.4 * roc_norm
    return max(-1, min(1, momentum))
```

---

## 5. CANDLE CONFIRMATION (Explicit Rules)

### Confirmation Timeframe
**Execution timeframe (5m)** - must close to confirm

### Confirmation Conditions

**LONG Setup:**
```python
confirmed = any([
    close > entry_zone_high,           # Price acceptance above entry
    bullish_engulfing(candle),          # Strong reversal pattern
    break_of_structure_high(highs),     # Breaks micro lower high
    close > ema9 and momentum > 0       # Momentum confirmation
])
```

**SHORT Setup:**
```python
confirmed = any([
    close < entry_zone_low,             # Price acceptance below entry
    bearish_engulfing(candle),          # Strong reversal pattern
    break_of_structure_low(lows),       # Breaks micro higher low
    close < ema9 and momentum < 0       # Momentum confirmation
])
```

### Expiration Rule
```python
if pending_candles >= 6:  # 6 × 5m = 30 minutes
    invalidate_signal(signal_id, reason="No confirmation within 30 min")
    transition_to_cooldown()
```

---

## 6. SIGNAL ID (Stable Hash)

```python
def generate_signal_id(symbol, direction, entry_low, entry_high, stop, exec_tf, macro_regime):
    """
    Stable signal ID using setup parameters
    """
    import hashlib
    
    # Use entry zone mid rounded to ATR/2 for stability
    atr = calculate_atr_from_context()
    entry_mid = (entry_low + entry_high) / 2
    rounded_entry = round(entry_mid / (atr / 2)) * (atr / 2)
    
    # Create unique string
    unique_str = f"{symbol}_{direction}_{exec_tf}_{rounded_entry:.0f}_{stop:.0f}_{macro_regime}"
    
    # Hash for compactness (optional - can use string directly)
    signal_id = hashlib.md5(unique_str.encode()).hexdigest()[:12]
    
    return signal_id, unique_str  # Return both for debugging
```

**Human-readable format:**
```
BTCUSDT_LONG_5m_65400_64700_trend_bull
```

---

## 7. ACTIVE INVALIDATION (Explicit Triggers)

### Invalidation Conditions (ANY triggers exit)

```python
def check_active_invalidation(signal, current_analysis):
    """
    Returns (invalidated: bool, reason: str)
    """
    # 1. Stop loss hit
    if (signal.direction == "LONG" and price <= signal.stop_loss) or \
       (signal.direction == "SHORT" and price >= signal.stop_loss):
        return True, "Stop loss hit"
    
    # 2. Macro or Intermediate bias flips beyond threshold
    macro_score = current_analysis['mtf_score']['macro']
    intermediate_score = current_analysis['mtf_score']['intermediate']
    
    if signal.direction == "LONG":
        if macro_score < -0.20 and current_analysis['macro_strength'] > 0.50:
            return True, "Macro bias flipped bearish"
        if intermediate_score < -0.20 and current_analysis['intermediate_strength'] > 0.50:
            return True, "Intermediate bias flipped bearish"
    
    if signal.direction == "SHORT":
        if macro_score > +0.20 and current_analysis['macro_strength'] > 0.50:
            return True, "Macro bias flipped bullish"
        if intermediate_score > +0.20 and current_analysis['intermediate_strength'] > 0.50:
            return True, "Intermediate bias flipped bullish"
    
    # 3. Execution regime becomes weak range
    exec_regime = current_analysis['timeframes']['5m']['regime']
    exec_strength = current_analysis['timeframes']['5m']['strength']
    exec_duration = current_analysis['timeframes']['5m']['bars_in_regime']
    
    if exec_regime == "RANGE" and exec_strength < 0.35 and exec_duration >= 3:
        return True, "Execution in weak range for 3+ candles"
    
    # 4. Time-based expiry
    active_duration = now - signal.activated_at
    if active_duration > timedelta(hours=6):
        return True, "Active > 6 hours without TP1"
    
    # 5. Structure break on execution timeframe
    if signal.direction == "LONG":
        if current_analysis['timeframes']['5m']['structure_broken']:
            return True, "Execution structure broken"
    
    return False, ""
```

---

## 8. CONDITIONAL ENTRY RULES (Fib vs Range)

```python
def calculate_entry_setup(regime, fib_levels, range_levels, atr):
    """
    Entry depends on regime type
    """
    if regime in ["TREND_BULL", "PULLBACK_BULL", "TREND_BEAR", "PULLBACK_BEAR"]:
        # Use Fibonacci in trending regimes
        entry = fib_levels['0.618']
        stop = fib_levels['0.786']
        target = fib_levels['0.382']
        
    elif regime in ["RANGE", "RANGE_BULL_DRIFT", "RANGE_BEAR_DRIFT"]:
        # Use range edges in ranging regimes
        if regime == "RANGE_BULL_DRIFT":
            entry = range_levels['low'] + atr * 0.5
            stop = range_levels['low'] - atr
            target = range_levels['high'] - atr * 0.5
        elif regime == "RANGE_BEAR_DRIFT":
            entry = range_levels['high'] - atr * 0.5
            stop = range_levels['high'] + atr
            target = range_levels['low'] + atr * 0.5
        else:  # Pure range - no trade
            return None
            
    elif regime in ["BREAKOUT", "BREAKDOWN"]:
        # Use breakout pullback
        if regime == "BREAKOUT":
            entry = fib_levels['0.50']  # 50% pullback of breakout candle
            stop = fib_levels['0.786']
            target = fib_levels['0.0'] + (fib_levels['0.0'] - fib_levels['1.0'])
        else:  # BREAKDOWN
            entry = fib_levels['0.50']
            stop = fib_levels['0.786']
            target = fib_levels['0.0'] - (fib_levels['1.0'] - fib_levels['0.0'])
    
    return {'entry': entry, 'stop': stop, 'target': target}
```

---

## 9. CONFIDENCE CALCULATION (Per Timeframe)

```python
def calculate_tf_confidence(regime, strength, data_quality):
    """
    Confidence based on:
    - Regime clarity (40%)
    - Signal strength (40%)
    - Data quality (20%)
    """
    # Regime clarity
    if regime in ["TREND_BULL", "TREND_BEAR", "RANGE"]:
        regime_clarity = 1.0
    elif regime in ["PULLBACK_BULL", "PULLBACK_BEAR"]:
        regime_clarity = 0.8
    elif regime in ["BREAKOUT", "BREAKDOWN"]:
        regime_clarity = 0.7
    else:
        regime_clarity = 0.4
    
    # Signal strength (already 0-1)
    signal_strength = strength
    
    # Data quality
    data_quality_score = min(1.0, data_quality['candles'] / 100)
    
    confidence = (0.40 * regime_clarity + 
                  0.40 * signal_strength + 
                  0.20 * data_quality_score)
    
    return confidence
```

---

## Summary of Critical Fixes

| Issue | Fix Applied |
|-------|-------------|
| Weighting inconsistency | Within-cluster weights sum to 1.0, verified total = 1.0 |
| Bias vs Tradeable confusion | Separate thresholds: Bias ≥0.20, Tradeable ≥0.45 |
| Regime ambiguity | Renamed ACCUMULATION/DISTRIBUTION, added conditions |
| Weak momentum | Combined RSI (60%) + ROC/ATR (40%) |
| Candle confirmation undefined | Explicit 5m confirmation with 4 conditions + 30-min timeout |
| Signal ID collision | Hash-based on setup parameters, ATR-rounded entry |
| Invalidation vague | 5 explicit triggers with clear conditions |
| Fib over-prescriptive | Conditional entry based on regime type |

---

## Files Updated

```
projects/crypto-analysis/core/
├── regime_detector.py          # Updated with enhanced regimes
├── weighted_mtf_scorer.py      # Fixed weights (sum to 1.0)
├── signal_state_machine.py     # Added explicit invalidation
├── momentum_calculator.py      # NEW: RSI + ROC combined
├── entry_calculator.py         # NEW: Conditional entry rules
└── professional_mtf_engine.py  # Updated with all fixes
```

---

Ready for implementation review or next component (dynamic sizing / liquidity context).
