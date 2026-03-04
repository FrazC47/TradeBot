#!/bin/bash
# ETHUSDT Improvement Agent Cron Job
# Runs daily to analyze performance and suggest optimizations

# Run the improvement agent
python3 /root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/improver/ethusdt_improver.py

# Run backtest simulation with current parameters
python3 /root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/improver/backtest_runner.py

# Analyze missed opportunities from last 24 hours
python3 /root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/improver/missed_opportunity_tracker.py

# Log completion
echo "[$(date)] ETHUSDT Improvement cycle complete" >> /root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/improver/logs/cron.log
