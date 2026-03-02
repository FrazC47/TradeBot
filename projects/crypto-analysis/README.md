# Crypto Analysis Project

## Overview
Automated candlestick chart generation and analysis for Binance trading pairs.

## Active Cron Job
- **Name:** `binance_chart_generator`
- **Schedule:** Every 5 minutes
- **Last Run:** February 25, 2026 — 11:21 PM (Asia/Shanghai)
- **Status:** Active and running successfully

## Generated Charts
- **Symbols:** BTCUSDT, ETHUSDT, BNBUSDT
- **Timeframes:** 1h, 4h, 1d, 1w, 1M
- **Candles:** 100-200 per chart (103 for monthly)
- **Total:** 15 interactive charts per run

## Output Locations
- Interactive HTML: `charts/` (Plotly visualizations)
- Static PNG: `charts_png/` (if enabled)
- Index: `charts/index.html` — dashboard view

## Scripts (workspace root)
- `binance_kline_monitor.py` — Kline monitoring
- `binance_kline_processor.py` — Data processing
- `binance_kline_simple.py` — Simplified fetcher
- `compass_chart_generator.py` — Compass-style charts
- `compass_chart_enhanced.py` — Enhanced compass charts
- `generate_charts.py` — Main chart generator
- `generate_chart_images.py` — PNG export
- `view_charts.py` — Chart viewer utility
- `cleanup_charts.py` — Maintenance script

## Notes
- Charts refresh automatically via cron
- Historical data preserved in workspace root scripts
- Analysis notes and insights go here
