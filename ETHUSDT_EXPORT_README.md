# ETHUSDT TradeBot - Export Package

**Export Date:** 2026-03-05 17:22  
**File:** `ETHUSDT_TradeBot_Export_20260305_1722.tar.gz`  
**Size:** 3.2 MB  
**Total Files:** 150

---

## What's Included

### 📁 Core System Files
- `agents/ethusdt_agent.py` - Main trading agent
- `agents/dynamic_data_puller.py` - Data fetcher
- `agents/modules/` - All strategy modules:
  - `mtf_engine_v34.py` - Multi-timeframe engine
  - `fundamental_analyzer.py` - On-chain analysis
  - `regime_detector.py` - Market regime detection
  - `drawdown_recovery.py` - Risk management
  - `dynamic_rr.py` - Dynamic risk/reward
  - `buffer_system.py` - Anti-manipulation
  - `advanced_profit_manager.py` - Profit scenarios
  - `dynamic_frequency.py` - Frequency escalation
  - `notifier.py` - Telegram notifications
- `agents/improver/ethusdt_improver_v2.py` - Self-improvement (100 iterations)
- `agents/auto_implementer/auto_implementer_v2.py` - Auto-deployment
- `agents/backtest_reviews/` - 6-hour review system
- `agents/scripts/` - All execution scripts

### 📊 Data Files
- `data/raw/` - Historical price data (7 timeframes):
  - 1M, 1w, 1d, 4h, 1h, 15m, 5m
  - 6,846 total candles
- `data/indicators/` - Pre-calculated indicators (60 per timeframe)
- `backtests/` - Backtest results and trade history

### 📋 Configuration
- `config/crontab.txt` - Cron job configuration
- `config/dynamic_frequency_state.json`
- `docs/` - Complete documentation:
  - Indicator formulas
  - Strategy sources
  - Execution summaries
  - Improver documentation

### 📝 State & Logs
- `state/agent_state.json`
- `logs/` - Execution logs
- `analysis/` - Analysis outputs

---

## Import Instructions (New OpenClaw Instance)

### Step 1: Extract Archive
```bash
cd /root/.openclaw/workspace
tar -xzf ETHUSDT_TradeBot_Export_20260305_1722.tar.gz
```

### Step 2: Install Cron Jobs
```bash
crontab ETHUSDT_TradeBot/config/crontab.txt
```

### Step 3: Set Permissions
```bash
chmod +x ETHUSDT_TradeBot/agents/scripts/*.sh
chmod +x ETHUSDT_TradeBot/agents/improver/scripts/*.sh
chmod +x ETHUSDT_TradeBot/agents/auto_implementer/scripts/*.sh
chmod +x ETHUSDT_TradeBot/agents/backtest_reviews/scripts/*.sh
```

### Step 4: Optional - Configure Telegram Notifications
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### Step 5: Verify Installation
```bash
# Check cron jobs
crontab -l | grep ETHUSDT

# Run agent manually to test
./ETHUSDT_TradeBot/agents/scripts/run_agent.sh
```

---

## System Requirements

- Python 3.8+
- pandas, numpy
- requests
- cron (for scheduled tasks)

---

## Active Jobs After Import

| Schedule | Job |
|----------|-----|
| Every 1 min | Dynamic data puller |
| Every 15 min | Trading agent |
| Every 6 hours | Backtest review |
| Daily 6 AM | Improver (100 iterations) |
| Daily 6:30 AM | Auto-implementer |
| Hourly :02 | Indicator calculation |

---

## Note

This is a complete, self-contained system. All data, indicators, and state are included. The system will continue from where it left off on the original instance.
