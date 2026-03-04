#!/bin/bash
# ETHUSDT Dedicated Agent Cron Job
# Runs every 15 minutes during active trading hours

# Set environment
export PYTHONPATH=/root/.openclaw/workspace/projects/crypto-analysis:$PYTHONPATH
export ETHUSDT_AGENT_CONFIG=/root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/config/agent.conf

# Log file with timestamp
LOG_FILE="/root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/logs/cron_$(date +\%Y\%m\%d).log"

# Run the agent
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting ETHUSDT Agent" >> "$LOG_FILE"
python3 /root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/ethusdt_agent.py >> "$LOG_FILE" 2>&1

# Check exit code
if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ETHUSDT Agent completed successfully" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ETHUSDT Agent FAILED" >> "$LOG_FILE"
fi

echo "---" >> "$LOG_FILE"
