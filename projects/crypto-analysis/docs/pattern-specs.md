# Candlestick Pattern Specifications

## Overview
This document defines the detection criteria for Japanese candlestick patterns used in the crypto analysis system. All patterns follow STRICT detection thresholds to ensure only textbook-quality patterns are identified.

---

## Basic Patterns

### 1. Doji Family

#### Standard Doji
- **Criteria**: Open price equals Close price (within 0.1% tolerance)
- **Body**: Very small or non-existent
- **Wicks**: Can vary in length
- **Significance**: Indecision in the market

#### Long-Legged Doji
- **Criteria**: 
  - Open ≈ Close (within 0.1%)
  - Upper wick ≥ 2x body size
  - Lower wick ≥ 2x body size
- **Significance**: Strong indecision, potential reversal

#### Dragonfly Doji
- **Criteria**:
  - Open ≈ Close (within 0.1%)
  - No upper wick (or very small < 10% of range)
  - Long lower wick (≥ 2x body)
- **Significance**: Bullish reversal at bottom

#### Gravestone Doji
- **Criteria**:
  - Open ≈ Close (within 0.1%)
  - Long upper wick (≥ 2x body)
  - No lower wick (or very small < 10% of range)
- **Significance**: Bearish reversal at top

### 2. Hammer
- **Criteria**:
  - Appears at the bottom of a downtrend
  - Small body at the upper end of the trading range
  - Lower wick ≥ 2x body size
  - Little to no upper wick (< 10% of body)
  - Body color can be bullish or bearish (bullish preferred)
- **Significance**: Bullish reversal

### 3. Inverted Hammer
- **Criteria**:
  - Appears at the bottom of a downtrend
  - Small body at the lower end of the trading range
  - Upper wick ≥ 2x body size
  - Little to no lower wick (< 10% of body)
- **Significance**: Bullish reversal (weaker than hammer)

### 4. Shooting Star
- **Criteria**:
  - Appears at the top of an uptrend
  - Small body at the lower end of the trading range
  - Upper wick ≥ 2x body size
  - Little to no lower wick (< 10% of body)
- **Significance**: Bearish reversal

### 5. Bullish Engulfing
- **Criteria**:
  - First candle: Bearish (close < open)
  - Second candle: Bullish (close > open)
  - Second candle's body completely engulfs first candle's body
  - Second candle's open ≤ First candle's close
  - Second candle's close ≥ First candle's open
  - First candle should not be a doji
- **Significance**: Strong bullish reversal

### 6. Bearish Engulfing
- **Criteria**:
  - First candle: Bullish (close > open)
  - Second candle: Bearish (close < open)
  - Second candle's body completely engulfs first candle's body
  - Second candle's open ≥ First candle's close
  - Second candle's close ≤ First candle's open
  - First candle should not be a doji
- **Significance**: Strong bearish reversal

---

## Intermediate Patterns

### 7. Morning Star
- **Criteria** (3-candle pattern):
  - **Candle 1**: Long bearish candle
    - Body ≥ 50% of candle range
    - Close near low
  - **Candle 2**: Small body (star)
    - Gaps down from Candle 1's close
    - Body < 30% of Candle 1's body
    - Can be bullish, bearish, or doji
  - **Candle 3**: Long bullish candle
    - Body ≥ 50% of candle range
    - Close > 50% into Candle 1's body
    - Preferably closes above Candle 1's open
- **Significance**: Strong bullish reversal

### 8. Evening Star
- **Criteria** (3-candle pattern):
  - **Candle 1**: Long bullish candle
    - Body ≥ 50% of candle range
    - Close near high
  - **Candle 2**: Small body (star)
    - Gaps up from Candle 1's close
    - Body < 30% of Candle 1's body
    - Can be bullish, bearish, or doji
  - **Candle 3**: Long bearish candle
    - Body ≥ 50% of candle range
    - Close < 50% into Candle 1's body
    - Preferably closes below Candle 1's open
- **Significance**: Strong bearish reversal

### 9. Bullish Harami
- **Criteria**:
  - First candle: Long bearish candle
    - Body > average body size
  - Second candle: Small bullish candle
    - Completely inside first candle's body
    - Open > First candle's close
    - Close < First candle's open
    - Body < 50% of first candle's body
- **Significance**: Bullish reversal (weaker than engulfing)

### 10. Bearish Harami
- **Criteria**:
  - First candle: Long bullish candle
    - Body > average body size
  - Second candle: Small bearish candle
    - Completely inside first candle's body
    - Open < First candle's close
    - Close > First candle's open
    - Body < 50% of first candle's body
- **Significance**: Bearish reversal (weaker than engulfing)

### 11. Piercing Pattern
- **Criteria**:
  - First candle: Long bearish candle
  - Second candle: Bullish candle
    - Opens below first candle's low (gap down)
    - Closes above 50% of first candle's body
    - Closes below first candle's open
- **Significance**: Bullish reversal

### 12. Dark Cloud Cover
- **Criteria**:
  - First candle: Long bullish candle
  - Second candle: Bearish candle
    - Opens above first candle's high (gap up)
    - Closes below 50% of first candle's body
    - Closes above first candle's open
- **Significance**: Bearish reversal

### 13. Tweezer Tops
- **Criteria**:
  - First candle: Bullish candle
  - Second candle: Bearish candle
  - Highs are equal (within 0.1% tolerance)
  - Second candle's body shows rejection of higher prices
- **Significance**: Bearish reversal at resistance

### 14. Tweezer Bottoms
- **Criteria**:
  - First candle: Bearish candle
  - Second candle: Bullish candle
  - Lows are equal (within 0.1% tolerance)
  - Second candle's body shows rejection of lower prices
- **Significance**: Bullish reversal at support

---

## Advanced Patterns

### 15. Three White Soldiers
- **Criteria** (3-candle pattern):
  - All three candles are bullish (close > open)
  - Each candle opens within the previous candle's body
  - Each candle closes near its high (upper wick < 20% of body)
  - Progressive higher closes
  - Bodies should be of similar size (not too small, not too large)
  - Preferably appears after a downtrend or consolidation
- **Significance**: Strong bullish continuation/reversal

### 16. Three Black Crows
- **Criteria** (3-candle pattern):
  - All three candles are bearish (close < open)
  - Each candle opens within the previous candle's body
  - Each candle closes near its low (lower wick < 20% of body)
  - Progressive lower closes
  - Bodies should be of similar size
  - Preferably appears after an uptrend or consolidation
- **Significance**: Strong bearish continuation/reversal

### 17. Abandoned Baby
- **Criteria** (3-candle pattern):
  - **Candle 1**: Long candle in direction of trend
  - **Candle 2**: Doji
    - Gaps away from Candle 1 (no overlap in wicks)
    - Completely isolated
  - **Candle 3**: Long candle opposite to trend
    - Gaps away from Candle 2 (no overlap in wicks)
    - Preferably similar size to Candle 1
- **Significance**: Very strong reversal (rare pattern)

### 18. Morning Doji Star
- **Criteria** (3-candle pattern):
  - **Candle 1**: Long bearish candle
  - **Candle 2**: Doji (any type)
    - Gaps down from Candle 1
    - Body very small (< 5% of Candle 1's body)
  - **Candle 3**: Long bullish candle
    - Closes well into Candle 1's body (> 50%)
- **Significance**: Strong bullish reversal

### 19. Evening Doji Star
- **Criteria** (3-candle pattern):
  - **Candle 1**: Long bullish candle
  - **Candle 2**: Doji (any type)
    - Gaps up from Candle 1
    - Body very small (< 5% of Candle 1's body)
  - **Candle 3**: Long bearish candle
    - Closes well into Candle 1's body (> 50%)
- **Significance**: Strong bearish reversal

---

## Detection Parameters

### Threshold Constants
```python
DOJI_TOLERANCE = 0.001          # 0.1% for open/close equality
WICK_RATIO = 2.0                # Wick must be 2x body size
BODY_PERCENTAGE = 0.5           # 50% for long candle body
SMALL_BODY_RATIO = 0.3          # 30% for star candles
ENGULFING_THRESHOLD = 1.0       # Complete engulfing required
GAP_THRESHOLD = 0.001           # 0.1% for gap detection
EQUAL_PRICE_TOLERANCE = 0.001   # 0.1% for tweezer patterns
```

### Trend Detection
- **Uptrend**: Last 3 candles showing higher highs and higher lows
- **Downtrend**: Last 3 candles showing lower highs and lower lows
- **Consolidation**: Neither uptrend nor downtrend

### Pattern Strength Classification
- **Strong**: All criteria met perfectly
- **Moderate**: Minor deviations in wick ratios or body sizes
- **Weak**: Multiple criteria borderline (excluded in strict mode)

---

## Visual Representation

### Color Coding
- **Bullish Patterns**: Bright green outline (#00FF00)
- **Bearish Patterns**: Bright red outline (#FF0000)
- **Neutral (Doji)**: Yellow/white outline (#FFFF00)
- **Outline Thickness**: 3px

### Annotations
- Text label positioned above/below pattern
- Arrow pointing to first candle of pattern
- Semi-transparent box around multi-candle patterns
- Legend on chart bottom-right

---

## Implementation Notes

1. **Strict Mode**: Only patterns meeting ALL criteria are detected
2. **Context Matters**: Trend direction affects pattern validity
3. **Volume Confirmation**: Higher volume on reversal candles increases reliability
4. **Multi-Timeframe**: Patterns detected independently on each timeframe
5. **Overlap Handling**: When patterns overlap, prioritize the stronger signal
