#!/bin/bash
# Auto-sync script for TradeBot repository
# Run at session start to check for GitHub updates

cd /root/.openclaw/workspace

echo "🔍 Checking for updates from GitHub..."

# Fetch latest from origin
git fetch origin main 2>/dev/null

if [ $? -ne 0 ]; then
    echo "⚠️  Could not reach GitHub, using local version"
    exit 0
fi

# Get current and remote commit hashes
LOCAL=$(git rev-parse HEAD 2>/dev/null)
REMOTE=$(git rev-parse origin/main 2>/dev/null)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "📥 Updates found on GitHub"
    echo "   Local:  ${LOCAL:0:7}"
    echo "   Remote: ${REMOTE:0:7}"
    echo ""
    echo "🔄 Pulling updates..."
    git pull origin main
    echo ""
    echo "✅ Sync complete"
    
    # Show recent commits
    echo ""
    echo "📋 Recent changes:"
    git log --oneline -3
else
    echo "✅ Already up to date (${LOCAL:0:7})"
fi
