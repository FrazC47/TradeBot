# ETHUSDT Dedicated Trading Agent

A specialized trading agent exclusively for Ethereum (ETHUSDT) on Binance Futures.

## Overview

This agent is designed specifically for ETH's unique characteristics:
- **Volatility patterns**: ETH-specific ATR and range calculations
- **Momentum behavior**: Optimized for ETH's trend dynamics
- **Volume profiles**: ETH-specific volume analysis
- **Risk management**: Position scaling tailored to ETH

## Architecture

```
ethusdt/
├── ethusdt_agent.py      # Main agent logic
├── config/
│   ├── agent.conf        # Agent configuration
│   └── crontab.txt       # Cron job settings
├── scripts/
│   └── run_agent.sh      # Execution script
├── logs/                 # Agent logs
│   └── agent.log
└── state/                # Agent state
    └── agent_state.json
```

## Features

### ETH-Specific Optimizations
- **EMA 9/21**: Tuned for ETH's momentum
- **RSI 40-75**: Avoids ETH's common whipsaws
- **Volume >1.0x**: Ensures real participation
- **Range <70%**: Prevents chasing extended moves
- **Position Scaling**: 50% initial + 50% on confirmation

### Independent Operation
- Dedicated data loading (only ETHUSDT)
- Separate indicator calculations
- Independent state management
- Isolated logging

## Installation

### 1. Setup Cron Job
```bash
# Add to crontab
crontab -e

# Paste this line:
*/15 * * * * /root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/scripts/run_agent.sh
```

### 2. Verify Permissions
```bash
chmod +x /root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/scripts/run_agent.sh
```

### 3. Test Run
```bash
cd /root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt
python3 ethusdt_agent.py
```

## Configuration

Edit `config/agent.conf` to adjust:
- Risk parameters
- Entry criteria
- Filter thresholds
- Notification settings

## Monitoring

### View Logs
```bash
# Real-time logstail -f /root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/logs/agent.log

# Daily cron logs
tail -f /root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/logs/cron_$(date +%Y%m%d).log
```

### Check State
```bash
cat /root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/state/agent_state.json
```

## Performance Tracking

The agent tracks:
- Total trades
- Win/loss ratio
- Daily trade count
- Active setups
- Total P&L

## Next Steps for Multi-Agent System

Once ETHUSDT agent is proven:

1. **Create BTCUSDT Agent**
   - Trend-following strategy
   - Fibonacci pullback entries
   - Wider stops (higher volatility)

2. **Create SOLUSDT Agent**
   - EMA crossover strategy
   - Smaller position sizes
   - Faster timeframes

3. **Create XRPUSDT Agent**
   - Complete redesign needed
   - Test new approach

4. **Create BNBUSDT Agent**
   - Extreme selectivity
   - Volume spike detection

Each agent will have:
- Dedicated directory structure
- Currency-specific logic
- Independent cron jobs
- Separate state management

## License

Private - For personal trading use only
