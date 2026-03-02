#!/usr/bin/env python3
"""
Smart Data Fetcher - Production Implementation
Step 1: Pulling APIs via Scheduled Cron Jobs

Features:
- Smart fetching (only when new candles available)
- Server time sync with Binance
- Backfill logic for missed runs
- Atomic file writes
- State management
- Rate limiting with weights
- Concurrency lock
"""

import requests
import csv
import json
import time
import os
import sys
import fcntl
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Configuration
DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
STATE_FILE = Path('/root/.openclaw/workspace/data/fetcher_state.json')
LOCK_FILE = Path('/tmp/mtf_fetcher.lock')
LOG_FILE = Path('/root/.openclaw/workspace/logs/fetcher.log')

# Binance API Configuration
BINANCE_SPOT_URL = 'https://api.binance.com/api/v3'
BINANCE_FUTURES_URL = 'https://fapi.binance.com/fapi/v1'
BINANCE_FUTURES_DATA_URL = 'https://fapi.binance.com/futures/data'

# Symbols to fetch
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']

# Timeframe intervals in milliseconds
TIMEFRAME_INTERVALS = {
    '1M': 30 * 24 * 60 * 60 * 1000,    # ~30 days
    '1w': 7 * 24 * 60 * 60 * 1000,      # 7 days
    '1d': 24 * 60 * 60 * 1000,          # 1 day
    '4h': 4 * 60 * 60 * 1000,           # 4 hours
    '1h': 60 * 60 * 1000,               # 1 hour
    '15m': 15 * 60 * 1000,              # 15 minutes
    '5m': 5 * 60 * 1000                 # 5 minutes
}

# Binance API weights
API_WEIGHTS = {
    '/klines': 1,
    '/depth': 5,           # limit=100
    '/depth?limit=500': 25,
    '/premiumIndex': 1,
    '/fundingRate': 1,
    '/openInterestHist': 1
}

# Rate limiting state
class RateLimiter:
    def __init__(self, max_weight_per_minute=1200):
        self.max_weight = max_weight_per_minute
        self.current_weight = 0
        self.window_start = time.time()
    
    def check_and_consume(self, endpoint: str) -> bool:
        """Check if we can make request, consume weight if yes"""
        now = time.time()
        
        # Reset window every minute
        if now - self.window_start >= 60:
            self.current_weight = 0
            self.window_start = now
        
        weight = API_WEIGHTS.get(endpoint, 1)
        
        if self.current_weight + weight > self.max_weight:
            # Wait for next minute
            sleep_time = 60 - (now - self.window_start) + 1
            log_message(f"Rate limit approaching, sleeping {sleep_time:.0f}s")
            time.sleep(sleep_time)
            self.current_weight = 0
            self.window_start = time.time()
        
        self.current_weight += weight
        return True

rate_limiter = RateLimiter()


@dataclass
class FetcherState:
    """State for each symbol/timeframe"""
    last_fetch: int          # timestamp ms
    last_candle_open: int    # last candle open time ms
    last_candle_close: int   # last candle close time ms
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class SmartDataFetcher:
    """
    Production-grade smart data fetcher
    """
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.state_file = STATE_FILE
        self.server_time_offset = 0
        self.state: Dict[str, FetcherState] = {}
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        self.load_state()
        self.sync_server_time()
    
    def sync_server_time(self):
        """Sync with Binance server time"""
        try:
            response = requests.get(f'{BINANCE_SPOT_URL}/time', timeout=10)
            response.raise_for_status()
            server_time = response.json()['serverTime']
            local_time = int(time.time() * 1000)
            self.server_time_offset = server_time - local_time
            log_message(f"Server time synced. Offset: {self.server_time_offset}ms")
        except Exception as e:
            log_message(f"Failed to sync server time: {e}")
            self.server_time_offset = 0
    
    def get_server_time(self) -> int:
        """Get current server time"""
        return int(time.time() * 1000) + self.server_time_offset
    
    def load_state(self):
        """Load fetcher state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.state = {}
                    for k, v in data.items():
                        # Handle both old and new state formats
                        if isinstance(v, dict):
                            if 'last_candle_open' in v:
                                self.state[k] = FetcherState.from_dict(v)
                            elif 'last_candle' in v:
                                # Old format migration
                                self.state[k] = FetcherState(
                                    last_fetch=v.get('last_fetch', 0),
                                    last_candle_open=v.get('last_candle', 0),
                                    last_candle_close=v.get('last_fetch', 0)
                                )
                log_message(f"Loaded state for {len(self.state)} symbol/timeframes")
            except Exception as e:
                log_message(f"Error loading state: {e}")
                self.state = {}
    
    def save_state(self):
        """Save fetcher state atomically"""
        try:
            tmp_file = self.state_file.with_suffix('.tmp')
            with open(tmp_file, 'w') as f:
                json.dump(
                    {k: v.to_dict() for k, v in self.state.items()}, 
                    f, 
                    indent=2
                )
            tmp_file.rename(self.state_file)
        except Exception as e:
            log_message(f"Error saving state: {e}")
    
    def get_state_key(self, symbol: str, interval: str) -> str:
        """Generate state key"""
        return f"{symbol}_{interval}"
    
    def get_last_candle_from_csv(self, symbol: str, interval: str) -> Optional[int]:
        """Get last candle open time from CSV"""
        filepath = self.data_dir / symbol / f"{interval}.csv"
        
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r') as f:
                # Read last line efficiently
                f.seek(0, 2)  # Seek to end
                if f.tell() < 100:  # File too small
                    return None
                
                # Find last newline
                pos = f.tell() - 100
                f.seek(max(0, pos))
                lines = f.readlines()
                
                if len(lines) < 2:
                    return None
                
                # Parse last data line
                last_line = lines[-1].strip()
                if not last_line or last_line.startswith('open_time'):
                    return None
                
                # CSV format: open_time,open,high,low,close,volume,...
                open_time = int(last_line.split(',')[0])
                return open_time
        except Exception as e:
            log_message(f"Error reading CSV for {symbol}/{interval}: {e}")
            return None
    
    def should_fetch(self, symbol: str, interval: str) -> Tuple[bool, str]:
        """
        Determine if we should fetch new data
        Returns: (should_fetch, reason)
        """
        state_key = self.get_state_key(symbol, interval)
        interval_ms = TIMEFRAME_INTERVALS[interval]
        server_now = self.get_server_time()
        
        # Get last candle time (prefer state, fallback to CSV)
        if state_key in self.state:
            last_candle = self.state[state_key].last_candle_open
        else:
            last_candle = self.get_last_candle_from_csv(symbol, interval)
        
        if last_candle is None:
            return True, "No existing data"
        
        # Calculate next candle time
        next_candle = last_candle + interval_ms
        
        # Check if new candle should be available
        if server_now >= next_candle:
            time_since = (server_now - last_candle) / 1000
            candles_missed = (server_now - next_candle) // interval_ms + 1
            return True, f"{candles_missed} new candle(s) available ({time_since:.0f}s since last)"
        else:
            time_until = (next_candle - server_now) / 1000
            return False, f"Next candle in {time_until:.0f}s"
    
    def fetch_klines(self, symbol: str, interval: str, 
                     start_time: Optional[int] = None,
                     end_time: Optional[int] = None,
                     limit: int = 1000) -> List[List]:
        """
        Fetch klines from Binance API with rate limiting
        """
        rate_limiter.check_and_consume('/klines')
        
        url = f'{BINANCE_SPOT_URL}/klines'
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            log_message(f"API error for {symbol}/{interval}: {e}")
            return []
    
    def fetch_with_backfill(self, symbol: str, interval: str) -> List[List]:
        """
        Fetch all candles since last known, with backfill for missed runs
        """
        state_key = self.get_state_key(symbol, interval)
        interval_ms = TIMEFRAME_INTERVALS[interval]
        server_now = self.get_server_time()
        
        # Get starting point
        if state_key in self.state:
            last_candle = self.state[state_key].last_candle_open
        else:
            last_candle = self.get_last_candle_from_csv(symbol, interval)
        
        if last_candle is None:
            # No existing data - fetch recent history (last 100 candles)
            start_ms = server_now - (100 * interval_ms)
            log_message(f"    No existing data, fetching last 100 candles")
        else:
            start_ms = last_candle + interval_ms  # Next expected candle
        
        all_candles = []
        current_start = start_ms
        max_iterations = 10  # Safety limit
        
        for iteration in range(max_iterations):
            if current_start >= server_now:
                break
            
            candles = self.fetch_klines(
                symbol=symbol,
                interval=interval,
                start_time=current_start,
                end_time=server_now,
                limit=1000
            )
            
            if not candles:
                break
            
            all_candles.extend(candles)
            
            # Update start for next batch
            last_fetched_open = int(candles[-1][0])
            current_start = last_fetched_open + interval_ms
            
            # Safety: don't fetch incomplete current candle
            if current_start + interval_ms > server_now:
                break
            
            # Small delay between batches
            time.sleep(0.1)
        
        return all_candles
    
    def merge_and_save(self, symbol: str, interval: str, 
                       new_candles: List[List]) -> int:
        """
        Merge new candles with existing CSV and save atomically
        Returns: number of new candles added
        """
        if not new_candles:
            return 0
        
        symbol_dir = self.data_dir / symbol
        symbol_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = symbol_dir / f"{interval}.csv"
        
        # Load existing data
        existing = {}
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        open_time = int(row['open_time'])
                        existing[open_time] = row
            except Exception as e:
                log_message(f"Error reading existing CSV: {e}")
        
        # Add new candles
        added_count = 0
        for candle in new_candles:
            open_time = int(candle[0])
            if open_time not in existing:
                existing[open_time] = {
                    'open_time': candle[0],
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5],
                    'close_time': candle[6],
                    'quote_volume': candle[7],
                    'trades': candle[8],
                    'taker_buy_volume': candle[9],
                    'taker_buy_quote_volume': candle[10],
                    'ignore': candle[11] if len(candle) > 11 else ''
                }
                added_count += 1
        
        if added_count == 0:
            return 0
        
        # Sort by open_time and write atomically
        sorted_candles = sorted(existing.values(), key=lambda x: int(x['open_time']))
        
        try:
            tmp_file = filepath.with_suffix('.tmp')
            with open(tmp_file, 'w', newline='') as f:
                fieldnames = [
                    'open_time', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 
                    'taker_buy_volume', 'taker_buy_quote_volume', 'ignore'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(sorted_candles)
            
            tmp_file.rename(filepath)
            
            # Update state with last candle
            last_candle = sorted_candles[-1]
            state_key = self.get_state_key(symbol, interval)
            self.state[state_key] = FetcherState(
                last_fetch=int(time.time() * 1000),
                last_candle_open=int(last_candle['open_time']),
                last_candle_close=int(last_candle['close_time'])
            )
            
            return added_count
            
        except Exception as e:
            log_message(f"Error saving CSV: {e}")
            return 0
    
    def run(self):
        """Main fetcher loop"""
        log_message("="*60)
        log_message(f"Smart Data Fetcher Started: {datetime.now()}")
        log_message("="*60)
        
        total_fetched = 0
        total_skipped = 0
        
        for symbol in SYMBOLS:
            log_message(f"\nProcessing {symbol}...")
            
            for interval in TIMEFRAME_INTERVALS.keys():
                should_fetch, reason = self.should_fetch(symbol, interval)
                
                if not should_fetch:
                    log_message(f"  {interval}: SKIP - {reason}")
                    total_skipped += 1
                    continue
                
                log_message(f"  {interval}: FETCH - {reason}")
                
                # Fetch with backfill
                candles = self.fetch_with_backfill(symbol, interval)
                
                if candles:
                    added = self.merge_and_save(symbol, interval, candles)
                    log_message(f"    Added {added} new candles")
                    total_fetched += added
                else:
                    log_message(f"    No data returned")
                
                # Small delay between requests
                time.sleep(0.2)
        
        # Save state
        self.save_state()
        
        log_message(f"\n{'='*60}")
        log_message(f"Complete: {total_fetched} candles fetched, {total_skipped} skipped")
        log_message(f"{'='*60}\n")
        
        return total_fetched > 0


def log_message(message: str):
    """Log to file and stdout"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    
    print(log_line)
    
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(log_line + '\n')
    except:
        pass


def acquire_lock() -> Optional[int]:
    """Prevent overlapping runs"""
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except (IOError, OSError):
        return None


def release_lock(fd: int):
    """Release lock"""
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        LOCK_FILE.unlink(missing_ok=True)
    except:
        pass


def main():
    """Entry point"""
    # Check for overlapping runs
    lock_fd = acquire_lock()
    if lock_fd is None:
        log_message("ERROR: Another instance is running. Exiting.")
        sys.exit(0)
    
    try:
        fetcher = SmartDataFetcher()
        success = fetcher.run()
        sys.exit(0 if success else 1)
    finally:
        release_lock(lock_fd)


if __name__ == "__main__":
    main()
