# Step 1: Smart Data Fetcher
## Production Implementation

---

## Overview

This is the **production-ready implementation** of Step 1: pulling API data via scheduled cron jobs.

**Features:**
- ✅ Smart fetching (only when new candles available)
- ✅ Server time sync with Binance
- ✅ Backfill logic for missed runs
- ✅ Atomic file writes
- ✅ State management
- ✅ Rate limiting with weights
- ✅ Concurrency lock (prevents overlapping runs)

---

## Files

| File | Purpose |
|------|---------|
| `step1_smart_fetcher.py` | Main fetcher implementation |
| `setup_cron.sh` | Cron job installer |

---

## Installation

### 1. Install Cron Jobs

```bash
cd /root/.openclaw/workspace/projects/crypto-analysis
./setup_cron.sh
```

This installs:
- Fetcher every 5 minutes
- Daily log rotation
- Weekly state backup

### 2. Verify Installation

```bash
# Check cron jobs
crontab -l

# Test fetcher manually
python3 step1_smart_fetcher.py

# Monitor logs
tail -f /root/.openclaw/workspace/logs/fetcher.log
```

---

## How It Works

### Smart Fetching Logic

```
Check last candle time (from state or CSV)
    ↓
Calculate next candle time
    ↓
Compare to Binance server time
    ↓
New candle ready? → YES → Fetch with backfill
                → NO  → Skip (save API call)
```

### API Calls Made

| Timeframe | Frequency | Endpoint |
|-----------|-----------|----------|
| 5m | Every 5 min | `/api/v3/klines?interval=5m` |
| 15m | Every 15 min | `/api/v3/klines?interval=15m` |
| 1h | Every 1 hour | `/api/v3/klines?interval=1h` |
| 4h | Every 4 hours | `/api/v3/klines?interval=4h` |
| 1d | Every 1 day | `/api/v3/klines?interval=1d` |
| 1w | Every 1 week | `/api/v3/klines?interval=1w` |
| 1M | Every 1 month | `/api/v3/klines?interval=1M` |

### API Savings

| Method | Calls/Day |
|--------|-----------|
| Blind polling | ~10,080 |
| **Smart fetch** | **~2,040** |
| **Savings** | **~80%** |

---

## Configuration

### Symbols

Edit `SYMBOLS` list in `step1_smart_fetcher.py`:

```python
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']
```

### Data Directory

Data saved to:
```
/data/binance/
├── BTCUSDT/
│   ├── 1M.csv
│   ├── 1w.csv
│   ├── 1d.csv
│   ├── 4h.csv
│   ├── 1h.csv
│   ├── 15m.csv
│   └── 5m.csv
├── ETHUSDT/
└── ...
```

### State File

```
/data/fetcher_state.json
```

Tracks last fetch times to enable smart fetching.

---

## Production Features

### 1. Server Time Sync
```python
# Syncs with Binance server time on startup
# Prevents drift issues
```

### 2. Backfill Logic
```python
# If job is down for 2 hours
# Fetches ALL missed candles on next run
# Not just the latest one
```

### 3. Atomic Writes
```python
# Writes to .tmp file first
# Then renames to .csv
# Prevents corruption during writes
```

### 4. Rate Limiting
```python
# Tracks API weight per minute
# Respects 1,200 weight/min limit
# Auto-sleeps if approaching limit
```

### 5. Concurrency Lock
```python
# Uses file lock (fcntl)
# Prevents overlapping runs
# If job takes >5 min, next run skips
```

---

## Monitoring

### Logs

```bash
# Real-time fetcher log
tail -f /root/.openclaw/workspace/logs/fetcher.log

# Cron execution log
tail -f /root/.openclaw/workspace/logs/cron_fetcher.log
```

### Log Format

```
[2026-03-02 15:30:00] Smart Data Fetcher Started
[2026-03-02 15:30:01] Server time synced. Offset: 23ms
[2026-03-02 15:30:02] Processing BTCUSDT...
[2026-03-02 15:30:03]   5m: FETCH - 1 new candle(s) available (302s ago)
[2026-03-02 15:30:04]     Added 1 new candles
[2026-03-02 15:30:05]   15m: SKIP - Next candle in 423s
...
[2026-03-02 15:30:45] Complete: 5 candles fetched, 30 skipped
```

---

## Troubleshooting

### Issue: "Another instance is running"

**Cause:** Previous run hasn't finished

**Fix:**
```bash
# Check if process is stuck
ps aux | grep step1_smart_fetcher

# Kill if needed
kill -9 <PID>

# Remove lock file
rm /tmp/mtf_fetcher.lock
```

### Issue: No data being fetched

**Check:**
```bash
# Verify server time sync
python3 -c "import requests; print(requests.get('https://api.binance.com/api/v3/time').json())"

# Check state file
cat /root/.openclaw/workspace/data/fetcher_state.json

# Verify CSV files exist
ls -la /root/.openclaw/workspace/data/binance/BTCUSDT/
```

### Issue: Rate limit errors

**Fix:**
- Reduce symbols
- Increase delay between requests (edit `time.sleep(0.2)`)
- Check weight usage in logs

---

## Next Steps

After Step 1 is running smoothly:

1. **Step 2:** Calculate indicators
2. **Step 3:** MTF analysis
3. **Step 4:** Check setups

See `../MTF_FRAMEWORK_v3.4.md` for full architecture.

---

## Status

✅ Production-ready
✅ Tested with 5 symbols
✅ 80% API savings vs blind polling
✅ Handles missed runs (backfill)
✅ Atomic file operations
✅ Rate limit protection
