# Futures Market Sentiment Analysis

## Overview
Automated futures market sentiment monitoring system analyzing Open Interest (OI), Funding Rates, and Long/Short ratios for BTCUSDT, ETHUSDT, and BNBUSDT.

## Key Metrics

| Metric | Bullish Signal | Bearish Signal |
|--------|---------------|----------------|
| Funding Rate | < -0.05% (oversold) | > 0.05% (overheated) |
| OI Change | +10% in 1h (new positions) | -10% in 1h (capitulation) |
| L/S Ratio | < 0.5 (retail short) | > 3.0 (retail long) |

## Components

### 1. `futures_sentiment_analyzer.py`
Core analysis engine that:
- Loads COMPASS futures data (OI, funding, L/S ratio)
- Calculates sentiment scores
- Detects divergences (price vs OI)
- Identifies liquidation risks
- Generates comprehensive reports

### 2. `sentiment_monitor.py`
Quick check script for cron jobs:
- Runs every 15 minutes
- Generates sentiment snapshot
- Alerts on extreme conditions
- Logs to `monitor.log`

### 3. `sentiment_summary.py`
2-hour summary generator:
- Aggregates sentiment trends
- Identifies market-wide patterns
- Creates actionable insights
- Logs to `summary.log`

## Output Files

### Sentiment Reports
- `analysis/sentiment/sentiment_YYYYMMDD_HHMM.md` - Individual snapshots
- `analysis/sentiment/latest_sentiment.md` - Most recent report

### Summary Reports
- `analysis/sentiment/summary_YYYYMMDD_HHMM.md` - 2-hour summaries
- `analysis/sentiment/latest_summary.md` - Most recent summary

### Logs
- `analysis/sentiment/monitor.log` - Monitor execution log
- `analysis/sentiment/summary.log` - Summary execution log

## Cron Jobs

```
# Every 15 minutes - sentiment check
*/15 * * * * sentiment_monitor.py

# Every 2 hours - summary report
0 */2 * * * sentiment_summary.py

# Daily cleanup - keep 7 days of reports
0 0 * * * cleanup old reports
```

## Sentiment Scoring

### Funding Rate
- **Overheated (>0.05%)**: Longs paying high funding - bearish contrarian
- **Oversold (<-0.05%)**: Shorts paying high funding - bullish contrarian
- **Neutral**: Balanced funding

### Open Interest
- **+10% in 1h**: Significant new positions - momentum signal
- **-10% in 1h**: Capitulation or profit taking
- **Stable**: Consolidation phase

### Long/Short Ratio
- **>3.0**: Retail heavily long - contrarian bearish
- **<0.5**: Retail heavily short - contrarian bullish
- **0.5-3.0**: Balanced positioning

## Liquidation Risk Levels

| Level | Description |
|-------|-------------|
| 🔴🚀 High Long | Overleveraged longs vulnerable to cascade |
| 🟠 Moderate Long | Long bias with moderate risk |
| 🟢 Low | Balanced positioning |
| 🔵 Moderate Short | Short bias with moderate squeeze risk |
| 🟢💥 High Short | Overleveraged shorts vulnerable to squeeze |

## Usage

### Manual Check
```bash
cd /root/.openclaw/workspace/projects/crypto-analysis
python3 sentiment_monitor.py
```

### Generate Summary
```bash
python3 sentiment_summary.py
```

### Full Analysis
```bash
python3 futures_sentiment_analyzer.py
```

## Data Sources
- COMPASS analysis data: `/root/.openclaw/workspace/compass_analysis/`
- Binance Futures API (via COMPASS fetcher)

## Alert Conditions

The system automatically alerts on:
1. **Extreme Funding**: |rate| > 0.05%
2. **Extreme Positioning**: L/S ratio > 3.0 or < 0.5
3. **High Liquidation Risk**: Either direction
4. **Divergences**: Price vs OI mismatches

## Directory Structure
```
projects/crypto-analysis/
├── futures_sentiment_analyzer.py  # Core analyzer
├── sentiment_monitor.py           # 15-min monitor
├── sentiment_summary.py           # 2-hour summary
├── crontab.txt                    # Cron configuration
├── analysis/
│   └── sentiment/
│       ├── sentiment_*.md         # Individual reports
│       ├── summary_*.md           # Summary reports
│       ├── latest_sentiment.md    # Latest snapshot
│       ├── latest_summary.md      # Latest summary
│       ├── monitor.log            # Monitor logs
│       └── summary.log            # Summary logs
└── README.md                      # This file
```

## Notes
- Data updates every 5 minutes via COMPASS
- Sentiment analysis runs every 15 minutes
- Summary reports every 2 hours
- Reports auto-cleaned after 7 days
