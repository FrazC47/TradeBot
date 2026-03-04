# ETHUSDT Self-Improvement Agent

A dedicated agent for continuous optimization of ETHUSDT trading strategy.

## Philosophy

**Profit First, Then Risk Reduction (Without Sacrificing Profit)**

1. **Maximize Total Profit** - Primary goal
2. **Increase Win Rate** - Secondary, without hurting profit
3. **Reduce Drawdown** - Tertiary, only if profit maintained
4. **Improve Risk-Adjusted Returns** - Final optimization

## What It Does

### Continuous Analysis
- **Win Analysis**: Find patterns in successful trades to replicate
- **Loss Analysis**: Identify what causes losses to eliminate
- **Missed Opportunities**: Find profitable setups that were filtered out
- **Parameter Optimization**: Suggest adjustments to improve performance

### Daily Tasks
1. Analyze yesterday's trades (if any)
2. Review historical performance trends
3. Identify missed opportunities
4. Generate optimization suggestions
5. Run backtest simulations
6. Create improvement reports

### Weekly Tasks
1. Comprehensive performance review
2. Strategy parameter tuning
3. Filter relaxation analysis
4. Risk/reward optimization

## Architecture

```
improver/
├── ethusdt_improver.py      # Main improvement engine
├── backtest_runner.py        # Backtest simulation
├── missed_opportunity_tracker.py  # Track filtered setups
├── scripts/
│   └── run_improver.sh       # Cron execution script
├── analysis/                 # Generated reports
│   └── improvement_report_YYYYMMDD_HHMM.md
└── logs/
    └── improver.log
```

## Key Features

### 1. Win Pattern Recognition
- Analyzes what makes winning trades successful
- Identifies optimal entry conditions
- Finds best trade duration patterns
- Discovers volume/momentum signatures

### 2. Loss Prevention
- Categorizes losing trades by cause
- Identifies early warning patterns
- Suggests filter adjustments
- Recommends stop placement improvements

### 3. Missed Opportunity Analysis
- Tracks setups that were filtered out
- Calculates potential profit from missed trades
- Identifies which filters are too strict
- Suggests filter relaxation tests

### 4. Parameter Optimization
- Tests parameter changes in simulation
- Validates optimizations with backtests
- Measures profit impact before applying
- Maintains performance history

## Usage

### Manual Run
```bash
cd /root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/improver
python3 ethusdt_improver.py
```

### Automated (Cron)
```bash
# Daily at 6 AM
0 6 * * * /root/.openclaw/workspace/projects/crypto-analysis/agents/ethusdt/improver/scripts/run_improver.sh
```

## Output

### Improvement Reports
Generated daily in `analysis/`:
- Current performance metrics
- Identified patterns (wins/losses)
- Missed opportunities
- Optimization suggestions
- Backtest validation results

### Suggestion Format
```
Priority: 1 (Highest)
Goal: maximize_total_profit
Current: $662 profit
Target: $900 profit
Expected Impact: Capture 40% of missed opportunities
Confidence: 70%
Test Required: Yes
```

## Decision Framework

### When to Apply Optimizations

**APPLY IMMEDIATELY** (High Confidence, No Test Required):
- Position sizing adjustments
- Risk management tweaks
- Logging/monitoring improvements

**BACKTEST FIRST** (Medium Confidence):
- Filter threshold changes
- Entry criteria modifications
- Stop/target adjustments

**PAPER TRADE** (Low Confidence):
- Major strategy changes
- New indicator additions
- Significant filter relaxations

### Profit Protection Rule

**NEVER apply an optimization that:**
- Reduces expected profit by >5%
- Increases max drawdown by >20%
- Has <60% confidence in backtest

## Integration with Trading Agent

The improvement agent works alongside the trading agent:

1. **Trading Agent** executes trades
2. **Improvement Agent** analyzes results
3. **Suggestions** are generated daily
4. **Validated changes** are applied weekly
5. **Performance** is continuously monitored

## Multi-Agent Vision

Once proven for ETHUSDT, create dedicated improvers for:
- BTCUSDT - Trend-following optimization
- SOLUSDT - Momentum optimization
- BNBUSDT - Selectivity optimization

Each with currency-specific optimization goals.

## License

Private - For personal trading use only
