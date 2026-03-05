#!/bin/bash
# Repository Cleanup Script
# Keeps only crypto-analysis related files
# Moves other projects to separate locations for later repo creation

set -e

echo "========================================"
echo "Repository Cleanup - Crypto Analysis Only"
echo "========================================"
echo ""

# Create backup directory for non-crypto files
mkdir -p /root/.openclaw/workspace/_MOVED_PROJECTS

echo "Step 1: Moving non-crypto projects to _MOVED_PROJECTS/"
echo "--------------------------------------------------------"

# Move Falcon UAT project
if [ -d "/root/.openclaw/workspace/projects/falcon" ]; then
    echo "  Moving projects/falcon -> _MOVED_PROJECTS/falcon-uat"
    mv /root/.openclaw/workspace/projects/falcon /root/.openclaw/workspace/_MOVED_PROJECTS/falcon-uat
fi

echo ""
echo "Step 2: Cleaning up root-level non-crypto files"
echo "--------------------------------------------------------"

# List of files to remove from root (keep only essential workspace files)
FILES_TO_REMOVE=(
    "auto_sync.py"
    "compass_master.py"
    "compass_trade_tracker.py"
    "sync_repo.sh"
    "view_charts.py"
)

for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "/root/.openclaw/workspace/$file" ]; then
        echo "  Removing $file"
        rm "/root/.openclaw/workspace/$file"
    fi
done

echo ""
echo "Step 3: Moving old MTF framework docs to archive"
echo "--------------------------------------------------------"

mkdir -p /root/.openclaw/workspace/_ARCHIVED

OLD_DOCS=(
    "MTF_FRAMEWORK_v3.1.md"
    "MTF_FRAMEWORK_v3.4.md"
    "MTF_SUMMARY.txt"
    "PROFESSIONAL_MTF_FRAMEWORK.md"
    "MTF_FRAMEWORK_V2.md"
)

for doc in "${OLD_DOCS[@]}"; do
    if [ -f "/root/.openclaw/workspace/$doc" ]; then
        echo "  Archiving $doc"
        mv "/root/.openclaw/workspace/$doc" /root/.openclaw/workspace/_ARCHIVED/
    fi
done

echo ""
echo "Step 4: Cleaning up duplicate/backup files"
echo "--------------------------------------------------------"

# Remove duplicate strategy files (keep only FINAL_STRATEGIES.json)
STRATEGY_DUPS=(
    "/root/.openclaw/workspace/projects/crypto-analysis/backtests/final_strategies_20260301.json"
    "/root/.openclaw/workspace/projects/crypto-analysis/backtests/FINAL_STRATEGIES_V3.json"
    "/root/.openclaw/workspace/projects/crypto-analysis/backtests/FINAL_STRATEGIES_V4.json"
    "/root/.openclaw/workspace/projects/crypto-analysis/backtests/final_strategies_proportional.json"
)

for file in "${STRATEGY_DUPS[@]}"; do
    if [ -f "$file" ]; then
        echo "  Removing duplicate: $(basename $file)"
        rm "$file"
    fi
done

echo ""
echo "Step 5: Organizing crypto-analysis structure"
echo "--------------------------------------------------------"

# Create proper directory structure
mkdir -p /root/.openclaw/workspace/projects/crypto-analysis/{docs,tests,config}

# Move documentation files
echo "  Organizing documentation..."
if [ -f "/root/.openclaw/workspace/projects/crypto-analysis/docs/nginx-setup.md" ]; then
    mv /root/.openclaw/workspace/projects/crypto-analysis/docs/nginx-setup.md /root/.openclaw/workspace/projects/crypto-analysis/docs/ 2>/dev/null || true
fi

# Move pattern specs if exists
if [ -f "/root/.openclaw/workspace/projects/crypto-analysis/docs/pattern-specs.md" ]; then
    mv /root/.openclaw/workspace/projects/crypto-analysis/docs/pattern-specs.md /root/.openclaw/workspace/projects/crypto-analysis/docs/ 2>/dev/null || true
fi

echo ""
echo "========================================"
echo "Cleanup Summary"
echo "========================================"
echo ""
echo "✅ Kept in repo:"
echo "  - projects/crypto-analysis/ (main trading system)"
echo "  - .learnings/ (self-improvement logs)"
echo "  - AGENTS.md, SOUL.md, TOOLS.md, USER.md (workspace config)"
echo ""
echo "📦 Moved to _MOVED_PROJECTS/:"
echo "  - falcon-uat/ (UAT testing framework)"
echo ""
echo "📁 Archived to _ARCHIVED/:"
echo "  - Old MTF framework documentation"
echo ""
echo "🗑️  Deleted:"
echo "  - Root-level sync scripts"
echo "  - Duplicate strategy files"
echo ""
echo "Next steps:"
echo "  1. Review _MOVED_PROJECTS/ for separate repo creation"
echo "  2. Commit cleaned crypto-analysis repo"
echo "  3. Create new repos for moved projects"
echo ""
