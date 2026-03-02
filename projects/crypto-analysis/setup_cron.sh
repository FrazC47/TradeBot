#!/bin/bash
# Cron Setup Script for MTF Framework Step 1
# Run this to install the cron jobs

echo "Setting up MTF Framework cron jobs..."

# Create cron entries
CRON_JOBS=$(cat <<'EOF'
# MTF Framework - Step 1: Smart Data Fetcher
# Runs every 5 minutes
*/5 * * * * cd /root/.openclaw/workspace && /usr/bin/python3 projects/crypto-analysis/step1_smart_fetcher.py >> /root/.openclaw/workspace/logs/cron_fetcher.log 2>&1

# MTF Framework - Daily log rotation
0 0 * * * cd /root/.openclaw/workspace/logs && find . -name "*.log" -mtime +7 -delete

# MTF Framework - Weekly state backup
0 2 * * 0 cd /root/.openclaw/workspace/data && tar -czf backup_$(date +\%Y\%m\%d).tar.gz fetcher_state.json binance/ && find . -name "backup_*.tar.gz" -mtime +30 -delete
EOF
)

# Install cron jobs
(crontab -l 2>/dev/null; echo "$CRON_JOBS") | crontab -

echo "Cron jobs installed successfully!"
echo ""
echo "Current cron jobs:"
crontab -l
echo ""
echo "To verify the fetcher is working:"
echo "  tail -f /root/.openclaw/workspace/logs/fetcher.log"
echo ""
echo "To check cron execution:"
echo "  tail -f /root/.openclaw/workspace/logs/cron_fetcher.log"
