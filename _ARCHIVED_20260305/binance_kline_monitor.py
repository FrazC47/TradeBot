#!/usr/bin/env python3
"""
Binance Kline OHLCV Data Monitor

Fetches kline/candlestick data from Binance API for specified trading pairs,
saves to CSV files organized by symbol and interval, and calculates rolling statistics.
"""

import os
import sys
import json
import csv
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import statistics

import requests
import pandas as pd

# Binance API base URL
BINANCE_API_BASE = "https://api.binance.com"

# Default trading pairs to monitor
DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]

# Default intervals
DEFAULT_INTERVALS = ["1h", "4h", "1d", "1w", "1M"]

# Data directory
DATA_DIR = Path("/root/.openclaw/workspace/data/binance_klines")

# Kline interval mapping to pandas frequency
INTERVAL_TO_PANDAS = {
    "1s": "S",
    "1m": "min",
    "3m": "3min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "H",
    "2h": "2H",
    "4h": "4H",
    "6h": "6H",
    "8h": "8H",
    "12h": "12H",
    "1d": "D",
    "3d": "3D",
    "1w": "W",
    "1M": "M"
}


def fetch_klines(
    symbol: str,
    interval: str,
    limit: int = 1000,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None
) -> List[List]:
    """
    Fetch kline data from Binance API.
    
    Returns list of klines where each kline is:
    [open_time, open, high, low, close, volume, close_time, 
     quote_volume, trades, taker_buy_base, taker_buy_quote, ignore]
    """
    url = f"{BINANCE_API_BASE}/api/v3/klines"
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit
    }
    
    if start_time:
        params["startTime"] = start_time
    if end_time:
        params["endTime"] = end_time
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching klines for {symbol} ({interval}): {e}")
        return []


def klines_to_dataframe(klines: List[List]) -> pd.DataFrame:
    """Convert kline data to pandas DataFrame."""
    if not klines:
        return pd.DataFrame()
    
    columns = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_buy_base",
        "taker_buy_quote", "ignore"
    ]
    
    df = pd.DataFrame(klines, columns=columns)
    
    # Convert numeric columns
    numeric_cols = ["open", "high", "low", "close", "volume", 
                    "quote_volume", "taker_buy_base", "taker_buy_quote"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Convert time columns
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    
    # Convert integer columns
    df["trades"] = pd.to_numeric(df["trades"], downcast="integer")
    
    return df


def calculate_rolling_stats(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Calculate rolling statistics for the dataframe."""
    if df.empty or len(df) < window:
        return df
    
    # Price volatility (standard deviation of close prices)
    df["price_volatility"] = df["close"].rolling(window=window).std()
    
    # Volume moving average
    df["volume_ma"] = df["volume"].rolling(window=window).mean()
    
    # Price change percentage
    df["price_change_pct"] = df["close"].pct_change() * 100
    
    # High-Low range
    df["hl_range"] = ((df["high"] - df["low"]) / df["low"]) * 100
    
    # True Range and ATR (Average True Range)
    df["prev_close"] = df["close"].shift(1)
    df["tr1"] = df["high"] - df["low"]
    df["tr2"] = abs(df["high"] - df["prev_close"])
    df["tr3"] = abs(df["low"] - df["prev_close"])
    df["true_range"] = df[["tr1", "tr2", "tr3"]].max(axis=1)
    df["atr"] = df["true_range"].rolling(window=window).mean()
    
    # Buy/Sell pressure
    df["buy_pressure"] = (df["taker_buy_base"] / df["volume"]) * 100
    
    # Clean up temporary columns
    df = df.drop(columns=["prev_close", "tr1", "tr2", "tr3"])
    
    return df


def get_csv_path(symbol: str, interval: str) -> Path:
    """Get the CSV file path for a symbol and interval."""
    symbol_dir = DATA_DIR / symbol.upper()
    symbol_dir.mkdir(parents=True, exist_ok=True)
    return symbol_dir / f"{interval}.csv"


def load_existing_data(csv_path: Path) -> pd.DataFrame:
    """Load existing CSV data if it exists."""
    if not csv_path.exists():
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(csv_path)
        if "open_time" in df.columns:
            df["open_time"] = pd.to_datetime(df["open_time"])
        if "close_time" in df.columns:
            df["close_time"] = pd.to_datetime(df["close_time"])
        return df
    except Exception as e:
        print(f"Error loading existing data from {csv_path}: {e}")
        return pd.DataFrame()


def save_data(df: pd.DataFrame, csv_path: Path):
    """Save DataFrame to CSV."""
    try:
        df.to_csv(csv_path, index=False)
        print(f"Saved {len(df)} rows to {csv_path}")
    except Exception as e:
        print(f"Error saving data to {csv_path}: {e}")


def merge_and_deduplicate(existing_df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
    """Merge existing and new data, removing duplicates."""
    if existing_df.empty:
        return new_df
    if new_df.empty:
        return existing_df
    
    # Combine dataframes
    combined = pd.concat([existing_df, new_df], ignore_index=True)
    
    # Remove duplicates based on open_time
    combined = combined.drop_duplicates(subset=["open_time"], keep="last")
    
    # Sort by open_time
    combined = combined.sort_values("open_time").reset_index(drop=True)
    
    return combined


def fetch_and_update_symbol(
    symbol: str,
    interval: str,
    lookback_days: int = 30,
    calculate_stats: bool = True
) -> Tuple[int, bool]:
    """
    Fetch and update kline data for a single symbol/interval.
    
    Returns: (rows_added, success)
    """
    csv_path = get_csv_path(symbol, interval)
    existing_df = load_existing_data(csv_path)
    
    # Determine what data to fetch
    if existing_df.empty:
        # No existing data, fetch lookback period
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = end_time - (lookback_days * 24 * 60 * 60 * 1000)
        print(f"Fetching {lookback_days} days of data for {symbol} ({interval})")
    else:
        # Fetch only new data since last record
        last_time = existing_df["close_time"].max()
        start_time = int(last_time.timestamp() * 1000)
        end_time = int(datetime.now().timestamp() * 1000)
        print(f"Fetching new data for {symbol} ({interval}) since {last_time}")
    
    # Fetch data in batches if needed
    all_klines = []
    current_start = start_time
    max_iterations = 10  # Prevent infinite loops
    iteration = 0
    
    while iteration < max_iterations:
        klines = fetch_klines(symbol, interval, limit=1000, 
                             start_time=current_start, end_time=end_time)
        if not klines:
            break
        
        all_klines.extend(klines)
        
        # Check if we've reached the end
        last_kline_time = klines[-1][6]  # close_time of last kline
        if last_kline_time >= end_time or len(klines) < 1000:
            break
        
        # Move to next batch
        current_start = last_kline_time + 1
        iteration += 1
        time.sleep(0.1)  # Rate limiting
    
    if not all_klines:
        print(f"No new data available for {symbol} ({interval})")
        return 0, True
    
    # Convert to DataFrame
    new_df = klines_to_dataframe(all_klines)
    
    # Merge with existing data
    combined_df = merge_and_deduplicate(existing_df, new_df)
    
    # Calculate rolling statistics
    if calculate_stats and not combined_df.empty:
        combined_df = calculate_rolling_stats(combined_df)
    
    # Save data
    save_data(combined_df, csv_path)
    
    rows_added = len(combined_df) - len(existing_df)
    return rows_added, True


def get_stats_summary(symbol: str, interval: str) -> Optional[Dict]:
    """Get summary statistics for a symbol/interval."""
    csv_path = get_csv_path(symbol, interval)
    df = load_existing_data(csv_path)
    
    if df.empty:
        return None
    
    latest = df.iloc[-1]
    
    summary = {
        "symbol": symbol,
        "interval": interval,
        "total_records": len(df),
        "latest_time": latest["open_time"].strftime("%Y-%m-%d %H:%M:%S"),
        "latest_close": float(latest["close"]),
        "latest_volume": float(latest["volume"]),
    }
    
    # Add rolling stats if available
    if "price_volatility" in df.columns and pd.notna(latest.get("price_volatility")):
        summary["price_volatility"] = float(latest["price_volatility"])
    if "volume_ma" in df.columns and pd.notna(latest.get("volume_ma")):
        summary["volume_ma"] = float(latest["volume_ma"])
    if "atr" in df.columns and pd.notna(latest.get("atr")):
        summary["atr"] = float(latest["atr"])
    if "buy_pressure" in df.columns and pd.notna(latest.get("buy_pressure")):
        summary["buy_pressure"] = float(latest["buy_pressure"])
    
    # 24h stats if we have enough data
    if len(df) >= 24 and interval in ["1h", "30m", "15m"]:
        last_24 = df.tail(24)
        summary["24h_high"] = float(last_24["high"].max())
        summary["24h_low"] = float(last_24["low"].min())
        summary["24h_volume"] = float(last_24["volume"].sum())
        summary["24h_change_pct"] = ((latest["close"] - last_24.iloc[0]["open"]) 
                                      / last_24.iloc[0]["open"] * 100)
    
    return summary


def run_monitor(
    symbols: List[str],
    intervals: List[str],
    lookback_days: int = 30
) -> Dict:
    """Run the kline monitor for specified symbols and intervals."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "symbols_processed": [],
        "errors": [],
        "summaries": []
    }
    
    total_rows_added = 0
    
    for symbol in symbols:
        for interval in intervals:
            try:
                rows_added, success = fetch_and_update_symbol(
                    symbol, interval, lookback_days
                )
                
                if success:
                    results["symbols_processed"].append(f"{symbol}:{interval}")
                    total_rows_added += rows_added
                    
                    # Get summary
                    summary = get_stats_summary(symbol, interval)
                    if summary:
                        results["summaries"].append(summary)
                else:
                    results["errors"].append(f"{symbol}:{interval} - fetch failed")
                
                # Rate limiting between requests
                time.sleep(0.2)
                
            except Exception as e:
                error_msg = f"{symbol}:{interval} - {str(e)}"
                print(f"Error: {error_msg}")
                results["errors"].append(error_msg)
    
    results["total_rows_added"] = total_rows_added
    
    # Save summary report
    report_path = DATA_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nReport saved to: {report_path}")
    except Exception as e:
        print(f"Error saving report: {e}")
    
    return results


def print_summary(results: Dict):
    """Print a formatted summary of the results."""
    print("\n" + "=" * 60)
    print("BINANCE KLINE MONITOR SUMMARY")
    print("=" * 60)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Total rows added: {results.get('total_rows_added', 0)}")
    print(f"Symbols processed: {len(results['symbols_processed'])}")
    
    if results["summaries"]:
        print("\n--- Latest Data Summary ---")
        for summary in results["summaries"]:
            print(f"\n{summary['symbol']} ({summary['interval']}):")
            print(f"  Latest Close: ${summary['latest_close']:,.2f}")
            print(f"  Volume: {summary['latest_volume']:,.4f}")
            
            if "price_volatility" in summary:
                print(f"  Price Volatility (20-period): {summary['price_volatility']:.4f}")
            if "volume_ma" in summary:
                print(f"  Volume MA (20-period): {summary['volume_ma']:,.4f}")
            if "buy_pressure" in summary:
                print(f"  Buy Pressure: {summary['buy_pressure']:.2f}%")
            if "24h_change_pct" in summary:
                print(f"  24h Change: {summary['24h_change_pct']:+.2f}%")
    
    if results["errors"]:
        print("\n--- Errors ---")
        for error in results["errors"]:
            print(f"  - {error}")
    
    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Binance Kline OHLCV Data Monitor"
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=DEFAULT_SYMBOLS,
        help=f"Trading pairs to monitor (default: {DEFAULT_SYMBOLS})"
    )
    parser.add_argument(
        "--intervals",
        nargs="+",
        default=DEFAULT_INTERVALS,
        help=f"Kline intervals (default: {DEFAULT_INTERVALS})"
    )
    parser.add_argument(
        "--lookback",
        type=int,
        default=30,
        help="Days of historical data to fetch for new symbols (default: 30)"
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only print summary of existing data without fetching"
    )
    
    args = parser.parse_args()
    
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.summary_only:
        # Just print summaries
        print("\n--- Existing Data Summary ---")
        for symbol in args.symbols:
            for interval in args.intervals:
                summary = get_stats_summary(symbol, interval)
                if summary:
                    print(f"\n{summary['symbol']} ({summary['interval']}):")
                    print(f"  Records: {summary['total_records']}")
                    print(f"  Latest: ${summary['latest_close']:,.2f} @ {summary['latest_time']}")
                else:
                    print(f"\n{symbol} ({interval}): No data available")
    else:
        # Run full monitor
        results = run_monitor(args.symbols, args.intervals, args.lookback)
        print_summary(results)


if __name__ == "__main__":
    main()
