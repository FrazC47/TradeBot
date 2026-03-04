# ETHUSDT Dedicated Run - Complete File Structure

## Overview
This document shows all files involved in the ETHUSDT dedicated trading system.

## 1. DATA PULLING (Global - All Currencies)

### Primary Fetcher
**File:** `/root/.openclaw/workspace/projects/crypto-analysis/scripts/smart_data_fetcher.py`
- Runs every 5 minutes via cron
- Fetches OHLCV data for ALL currencies (including ETHUSDT)
- Uses smart fetching (only when new candles available)
- Saves to: `/root/.openclaw/workspace/data/binance/ETHUSDT/{timeframe}.csv`

### Cron Job
```
*/5 * * * * cd /root/.openclaw/workspace/projects/crypto-analysis && \
  /usr/bin/python3 scripts/smart_data_fetcher.py >> \
  /root/.openclaw/workspace/projects/crypto-analysis/logs/fetcher.log 2>&1
```

---

## 2. INDICATOR CALCULATION (Global - All Currencies)

### Primary Calculator
**File:** `/root/.openclaw/workspace/projects/crypto-analysis/scripts/calculate_all_indicators.py`
- Runs every 5 minutes (10s after fetcher)
- Calculates indicators for ALL currencies
- Saves to: `/root/.openclaw/workspace/data/indicators/ETHUSDT_indicators.json`

### Cron Job
```
*/5 * * * * sleep 10 && cd /root/.openclaw/workspace/projects/crypto-analysis && \
  /usr/bin/python3 scripts/calculate_all_indicators.py >> \
  /root/.openclaw/workspace/projects/crypto-analysis/logs/indicators.log 2>&1
```

---

## 3. ETHUSDT DEDICATED AGENT

### Main Agent
**File:** `/root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/ethusdt_agent.py`
- **Runs:** Every 15 minutes
- **Purpose:** Dedicated ETHUSDT analysis and trade identification
- **Loads:** All 7 timeframes (1M, 1w, 1d, 4h, 1h, 15m, 5m)
- **Uses:** Indicators from global calculator
- **Outputs:** Trade setups to logs

### Agent Runner Script
**File:** `/root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/scripts/run_agent.sh`

### Agent Configuration
**File:** `/root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/config/agent.conf`

### Agent State
**File:** `/root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/state/agent_state.json`

### Agent Logs
**File:** `/root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/logs/agent.log`

---

## 4. ETHUSDT IMPROVEMENT AGENT

### Improvement Engine
**File:** `/root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/improver/ethusdt_improver.py`
- **Runs:** Daily at 6 AM
- **Purpose:** Continuous optimization

### Improvement Runner
**File:** `/root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/improver/scripts/run_improver.sh`

### Improvement Reports
**Location:** `/root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/analysis/`

---

## 5. DATA FLOW

```
Global Data Fetcher (5 min) ──▶ ETHUSDT CSV Files
                                      │
Global Indicator Calc (5 min) ──▶ ETHUSDT_indicators.json
                                      │
ETHUSDT Agent (15 min) ────────▶ Analysis & Setup Detection
                                      │
ETHUSDT Improver (Daily) ──────▶ Optimization & Reports
```

---

## 6. CRON JOBS FOR ETHUSDT

| Job | Frequency | File |
|-----|-----------|------|
| Data Fetch | */5 * * * * | `scripts/smart_data_fetcher.py` |
| Indicators | */5 * * * * | `scripts/calculate_all_indicators.py` |
| **ETH Agent** | */15 * * * * | `agents/ethusdt/scripts/run_agent.sh` |
| **ETH Improver** | 0 6 * * * | `agents/ethusdt/improver/scripts/run_improver.sh` |

---

## 7. KEY FILES LIST

### Global (All Currencies)
- `scripts/smart_data_fetcher.py` - Data pulling
- `scripts/calculate_all_indicators.py` - Indicator calculation
- `logs/fetcher.log` - Fetch logs
- `logs/indicators.log` - Calculation logs

### ETHUSDT Data
- `data/binance/ETHUSDT/{1M,1w,1d,4h,1h,15m,5m}.csv` - OHLCV data
- `data/indicators/ETHUSDT_indicators.json` - Calculated indicators

### ETHUSDT Agent
- `agents/ethusdt/ethusdt_agent.py` - Main agent
- `agents/ethusdt/scripts/run_agent.sh` - Runner
- `agents/ethusdt/config/agent.conf` - Configuration
- `agents/ethusdt/state/agent_state.json` - State
- `agents/ethusdt/logs/agent.log` - Logs

### ETHUSDT Improver
- `agents/ethusdt/improver/ethusdt_improver.py` - Improvement engine
- `agents/ethusdt/improver/scripts/run_improver.sh` - Runner
- `agents/ethusdt/analysis/improvement_report_*.md` - Reports
