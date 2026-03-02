#!/usr/bin/env python3
"""
Chart viewer - starts HTTP server and opens charts in browser
"""

import subprocess
import sys
import webbrowser
from pathlib import Path
import time

CHARTS_DIR = Path('/root/.openclaw/workspace/charts')

def start_server():
    """Start HTTP server in background"""
    import socket
    
    # Check if port is already in use
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8080))
    sock.close()
    
    if result == 0:
        print("Server already running on port 8080")
        return True
    
    # Start server
    proc = subprocess.Popen(
        [sys.executable, '-m', 'http.server', '8080'],
        cwd=CHARTS_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    
    # Wait for server to start
    time.sleep(1)
    
    # Verify it's running
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8080))
    sock.close()
    
    if result == 0:
        print(f"✓ Server started on http://localhost:8080")
        return True
    else:
        print("✗ Failed to start server")
        return False

def open_chart(symbol=None, interval=None):
    """Open specific chart or index page"""
    
    if not start_server():
        return
    
    if symbol and interval:
        url = f"http://localhost:8080/{symbol}_{interval}.html"
    else:
        url = "http://localhost:8080/"
    
    print(f"Opening {url}")
    webbrowser.open(url)

def list_charts():
    """List all available charts"""
    charts = sorted(CHARTS_DIR.glob('*.html'))
    
    print("\nAvailable Charts:")
    print("=" * 50)
    
    for chart in charts:
        if chart.name == 'index.html':
            continue
        # Parse filename: SYMBOL_interval.html
        parts = chart.stem.split('_')
        if len(parts) == 2:
            symbol, interval = parts
            print(f"  {symbol} - {interval}")
    
    print("\nView all: http://localhost:8080/")
    print("=" * 50)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='View Binance candlestick charts')
    parser.add_argument('--symbol', '-s', help='Symbol (e.g., BTCUSDT)')
    parser.add_argument('--interval', '-i', help='Interval (e.g., 1h, 4h, 1d, 1w, 1M)')
    parser.add_argument('--list', '-l', action='store_true', help='List available charts')
    
    args = parser.parse_args()
    
    if args.list:
        list_charts()
    elif args.symbol and args.interval:
        open_chart(args.symbol, args.interval)
    else:
        open_chart()  # Open index page
