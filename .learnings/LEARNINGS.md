# Self-Improvement Learnings Log

## Format
Each entry should include:
- **ID**: LRN-YYYYMMDD-XXX format
- **Priority**: low | medium | high | critical
- **Status**: pending | resolved | promoted
- **Area**: frontend | backend | infra | tests | docs | config | trading | analysis
- **Summary**: Brief description
- **Details**: Full context
- **Suggested Action**: Specific fix
- **Metadata**: Source, related files, tags, etc.

---

## Critical Learnings

### [LRN-20260304-001] XRP Strategy Failure - No HTF Trend Check

**Logged**: 2026-03-04T13:58:00Z  
**Priority**: critical  
**Status**: pending  
**Area**: trading

#### Summary
XRP strategy had 27% win rate, losing 31% of account due to missing higher timeframe trend check

#### Details
Backtest revealed XRP strategy was taking long positions during bearish daily trends. The strategy only looked at 1h timeframe without confirming daily direction. This resulted in 8 trades with only 3 wins (37.5% win rate) and significant losses.

#### Suggested Action
- PAUSE XRP trading immediately
- Add daily trend filter (price > EMA 20 daily) before any XRP entry
- Redesign strategy completely before reactivation

#### Metadata
- **Source**: backtest_analysis
- **Related Files**: /projects/crypto-analysis/currency_strategies.py
- **Tags**: xrp, trend-following, counter-trend, failure
- **See Also**: LRN-20260304-002
- **Recurrence-Count**: 1
- **First-Seen**: 2026-03-04
- **Last-Seen**: 2026-03-04

---

### [LRN-20260304-002] BTC Strategy Overtrading in Choppy Markets

**Logged**: 2026-03-04T13:58:00Z  
**Priority**: critical  
**Status**: pending  
**Area**: trading

#### Summary
BTC strategy generated 345 trades with 35.9% win rate, losing 100% of account due to overtrading without market regime filter

#### Details
Strategy entered trades in ranging/sideways markets without checking if market was trending. ADX was often below 25 (choppy conditions) but trades were still taken. 102 trades (45% of losses) occurred in choppy markets.

#### Suggested Action
- Add ADX filter > 25 before entry
- Add daily trend confirmation (price > EMA 20 daily)
- Limit to maximum 2 trades per day
- Increase ATR multiplier from 3x to 4x for wider stops

#### Metadata
- **Source**: backtest_analysis
- **Related Files**: /projects/crypto-analysis/currency_strategies.py
- **Tags**: btc, overtrading, adx, choppy-market, trend-filter
- **See Also**: LRN-20260304-003
- **Recurrence-Count**: 1
- **First-Seen**: 2026-03-04
- **Last-Seen**: 2026-03-04

---

## High Priority Learnings

### [LRN-20260304-003] ETH Late Entry Losses at Extended Range

**Logged**: 2026-03-04T13:58:00Z  
**Priority**: high  
**Status**: pending  
**Area**: trading

#### Summary
3 ETH losses occurred when entering at >78% of price range with low volume (<0.75x average)

#### Details
Forensics analysis showed losing trades had:
- Range location: 78.5%, 82.1%, and 234% (extreme late entry)
- Volume ratios: 0.62x, 0.71x, and 0.48x (below threshold)
- All were chasing extended moves rather than entering on pullbacks

#### Suggested Action
- Add range location filter: only enter if < 70% of recent range
- Increase volume threshold from 0.8x to 1.0x average
- Add RSI filter (max 75) to avoid overbought entries

#### Metadata
- **Source**: trade_forensics
- **Related Files**: /projects/crypto-analysis/backtest_data/TRADE_FORENSICS_REPORT.txt
- **Tags**: eth, late-entry, volume, range-location, chase-trade
- **See Also**: LRN-20260304-004
- **Recurrence-Count**: 1
- **First-Seen**: 2026-03-04
- **Last-Seen**: 2026-03-04

---

## Medium Priority Learnings

### [LRN-20260304-004] Missed Opportunities Due to Strict Filters

**Logged**: 2026-03-04T13:58:00Z  
**Priority**: medium  
**Status**: pending  
**Area**: trading

#### Summary
478 profitable setups were filtered out, missing 1,988% potential profit due to overly strict entry criteria

#### Details
Analysis of missed opportunities revealed:
- 91% blocked by "NO_BREAKOUT" filter (need pullback entry option)
- 94% blocked by "DAILY_TREND_BEARISH" (daily EMAs too slow for crypto)
- Top missed trade: +13.59% profit on ETH (Feb 6, 2026 V-bottom reversal)

#### Suggested Action
- Consider hybrid approach: 70% core strategy + 30% opportunistic with relaxed filters
- Add pullback entry option (not just breakout)
- Consider 4h trend instead of daily for faster signals
- Test relaxed filters in backtest before deployment

#### Metadata
- **Source**: missed_opportunity_analysis
- **Related Files**: /projects/crypto-analysis/backtest_data/MISSED_OPPORTUNITIES_REPORT.md
- **Tags**: filters, opportunity-cost, breakout, pullback, trend-filter
- **See Also**: LRN-20260304-002, LRN-20260304-003
- **Recurrence-Count**: 1
- **First-Seen**: 2026-03-04
- **Last-Seen**: 2026-03-04

---

### [LRN-20260304-005] SOL EMA Crossover Lagging Entries

**Logged**: 2026-03-04T13:58:00Z  
**Priority**: medium  
**Status**: pending  
**Area**: trading

#### Summary
SOL strategy entered 12-15% into trend due to lagging EMA crossover signal

#### Details
EMA 12/26 crossover is a lagging indicator. By the time crossover occurred, price had already moved significantly. Combined with 3% fixed stops, this resulted in poor risk/reward.

#### Suggested Action
- Add pullback entry to EMA 12 after crossover (not at crossover)
- Add RSI momentum filter (50-70 range) to avoid exhausted trends
- Reduce stop to 2.5% for better risk management
- Add ADX filter > 20 to avoid chop

#### Metadata
- **Source**: backtest_analysis
- **Related Files**: /projects/crypto-analysis/currency_strategies.py
- **Tags**: sol, ema, lagging-indicator, pullback, momentum
- **Recurrence-Count**: 1
- **First-Seen**: 2026-03-04
- **Last-Seen**: 2026-03-04

---

## Low Priority Learnings

---

*Last Updated: 2026-03-04 13:58:00Z*
