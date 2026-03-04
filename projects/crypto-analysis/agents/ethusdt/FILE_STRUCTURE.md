# ETHUSDT Dedicated Run - File Architecture

## Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    ETHUSDT DATA PIPELINE                         │
└─────────────────────────────────────────────────────────────────┘

STEP 1: DATA PULLING (Every 5 minutes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
File: scripts/smart_data_fetcher.py
Cron: */5 * * * *
Output: data/binance/ETHUSDT/{1M,1w,1d,4h,1h,15m,5m}.csv

STEP 2: INDICATOR CALCULATION (Every 5 minutes + 10s delay)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
File: scripts/calculate_all_indicators.py
Cron: */5 * * * * (sleep 10)
Output: data/indicators/ETHUSDT_indicators.json

STEP 3: ETHUSDT AGENT ANALYSIS (Every 15 minutes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
File: agents/ethusdt/ethusdt_agent.py
Cron: */15 * * * *
Input: 
  - data/binance/ETHUSDT/*.csv (all 7 timeframes)
  - data/indicators/ETHUSDT_indicators.json
Output: agents/ethusdt/logs/agent.log

STEP 4: IMPROVEMENT AGENT (Daily at 6 AM)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
File: agents/ethusdt/improver/ethusdt_improver.py
Cron: 0 6 * * *
Input: 
  - backtest_data/ETHUSDT_trade_history.csv
  - agents/ethusdt/logs/agent.log
Output: agents/ethusdt/analysis/improvement_report_*.md
```

## File Descriptions

### Global Scripts (All Symbols)

| File | Purpose | Output |
|------|---------|--------|
| `scripts/smart_data_fetcher.py` | Pulls OHLCV from Binance API | CSV files per symbol/timeframe |
| `scripts/calculate_all_indicators.py` | Calculates EMA, RSI, MACD, VWAP, ATR, Bollinger | JSON indicators per symbol |

### ETHUSDT Dedicated Files

| File | Purpose | Runs |
|------|---------|------|
| `agents/ethusdt/ethusdt_agent.py` | Main trading agent | Every 15 min |
| `agents/ethusdt/scripts/run_agent.sh` | Execution wrapper | Every 15 min |
| `agents/ethusdt/config/agent.conf` | Configuration | - |
| `agents/ethusdt/state/agent_state.json` | Agent memory | Persistent |
| `agents/ethusdt/logs/agent.log` | Trading logs | Every 15 min |

### ETHUSDT Improvement Files

| File | Purpose | Runs |
|------|---------|------|
| `agents/ethusdt/improver/ethusdt_improver.py` | Performance analyzer | Daily 6 AM |
| `agents/ethusdt/improver/scripts/run_improver.sh` | Execution wrapper | Daily 6 AM |
| `agents/ethusdt/improver/state.json` | Improver memory | Persistent |
| `agents/ethusdt/analysis/improvement_report_*.md` | Generated reports | Daily |

## Data Storage

### Raw OHLCV Data
```
data/binance/ETHUSDT/
├── 1M.csv    (Monthly - 8 indicators)
├── 1w.csv    (Weekly - 8 indicators)
├── 1d.csv    (Daily - 11 indicators)
├── 4h.csv    (4 Hour - 11 indicators)
├── 1h.csv    (1 Hour - 8 indicators) ← Primary TF
├── 15m.csv   (15 Minute - 8 indicators)
└── 5m.csv    (5 Minute - 5 indicators) ← Execution TF
```

### Calculated Indicators
```
data/indicators/ETHUSDT_indicators.json
{
  "1M": {"ema_50": ..., "ema_200": ..., "macd_line": ...},
  "1w": {"ema_50": ..., "ema_200": ..., "macd_line": ...},
  "1d": {"ema_20": ..., "ema_50": ..., "vwap": ..., "rsi_14": ...},
  "4h": {"ema_9": ..., "ema_21": ..., "rsi_14": ..., "bb_upper": ...},
  "1h": {"ema_9": ..., "ema_25": ..., "rsi_14": ..., "vwap": ...},
  "15m": {"ema_9": ..., "ema_21": ..., "ema_50": ..., "rsi_9": ...},
  "5m": {"ema_9": ..., "rsi_7": ..., "vwap": ..., "atr_5": ...}
}
```

## Cron Job Schedule

```
# Global Pipeline (All Symbols)
*/5    * * * *  Data Fetcher
*/5    * * * *  Indicators (10s delay)

# ETHUSDT Dedicated
*/15   * * * *  ETH Agent (Trading)
0      6 * * *  ETH Improver (Analysis)
```

## Key Relationships

1. **Data Fetcher** → Creates/Updates CSV files
2. **Indicators** → Reads CSV → Calculates → Writes JSON
3. **ETH Agent** → Reads CSV + JSON → Analyzes → Logs results
4. **Improver** → Reads logs + history → Generates reports

## Dependencies

```
ethusdt_agent.py
  ├── requires: data/binance/ETHUSDT/*.csv (all 7 TFs)
  ├── requires: data/indicators/ETHUSDT_indicators.json
  └── outputs: agents/ethusdt/logs/agent.log

ethusdt_improver.py
  ├── requires: agents/ethusdt/logs/agent.log
  ├── requires: backtest_data/ETHUSDT_trade_history.csv
  └── outputs: agents/ethusdt/analysis/improvement_report_*.md
```
