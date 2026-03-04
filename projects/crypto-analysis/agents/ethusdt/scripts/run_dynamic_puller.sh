#!/bin/bash
# ETHUSDT Dynamic Data Puller
# Runs every minute but only pulls 1m data when setup is active
# Otherwise skips to save API calls

# Check if we should run (every minute, but only pull when needed)
cd /root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt

# Run dynamic puller
python3 dynamic_data_puller.py

# Log for debugging
echo "[$(date)] Dynamic puller executed" >> /root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/dynamic_puller_cron.log
