#!/usr/bin/env python3
"""
Binance Candlestick Chart Generator
Generates interactive HTML candlestick charts for all currency pairs and timeframes
"""

import csv
import json
from datetime import datetime
from pathlib import Path
import base64
from typing import List, Dict, Optional

# Data directory
DATA_DIR = Path('/root/.openclaw/workspace/data/binance')
OUTPUT_DIR = Path('/root/.openclaw/workspace/charts')

# Color scheme
COLORS = {
    'up': '#26a69a',      # Green for bullish
    'down': '#ef5350',    # Red for bearish
    'wick': '#787b86',    # Gray for wicks
    'bg': '#131722',      # Dark background
    'grid': '#2a2e39',    # Grid lines
    'text': '#d1d4dc',    # Text color
    'volume_up': 'rgba(38, 166, 154, 0.3)',
    'volume_down': 'rgba(239, 83, 80, 0.3)'
}


def load_ohlcv_data(symbol: str, interval: str, limit: int = 200) -> List[Dict]:
    """Load OHLCV data from CSV file"""
    filepath = DATA_DIR / symbol / f"{interval}.csv"
    
    if not filepath.exists():
        return []
    
    data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                data.append({
                    'timestamp': int(row['open_time']),
                    'datetime': datetime.fromtimestamp(int(row['open_time']) / 1000),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume'])
                })
            except (ValueError, KeyError):
                continue
    
    # Return last N candles
    return data[-limit:] if len(data) > limit else data


def generate_chart_html(symbol: str, interval: str, data: List[Dict]) -> str:
    """Generate HTML candlestick chart using lightweight-charts"""
    
    if not data:
        return f"<p>No data available for {symbol} {interval}</p>"
    
    # Prepare candlestick data
    candles = []
    volumes = []
    
    for i, d in enumerate(data):
        timestamp = int(d['timestamp'] / 1000)  # Convert to seconds
        
        candles.append({
            'time': timestamp,
            'open': round(d['open'], 2),
            'high': round(d['high'], 2),
            'low': round(d['low'], 2),
            'close': round(d['close'], 2)
        })
        
        # Volume bars
        color = COLORS['up'] if d['close'] >= d['open'] else COLORS['down']
        volumes.append({
            'time': timestamp,
            'value': round(d['volume'], 4),
            'color': color
        })
    
    # Calculate price range for y-axis
    highs = [d['high'] for d in data]
    lows = [d['low'] for d in data]
    price_range = max(highs) - min(lows)
    price_padding = price_range * 0.1
    
    # Latest price info
    latest = data[-1]
    prev = data[-2] if len(data) > 1 else latest
    change = latest['close'] - prev['close']
    change_pct = (change / prev['close']) * 100 if prev['close'] else 0
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{symbol} {interval} Chart</title>
    <script src="https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            background: {COLORS['bg']}; 
            color: {COLORS['text']}; 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            padding: 20px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid {COLORS['grid']};
        }}
        .symbol-info h1 {{
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 5px;
        }}
        .interval {{
            font-size: 14px;
            color: #787b86;
        }}
        .price-info {{
            text-align: right;
        }}
        .current-price {{
            font-size: 28px;
            font-weight: 600;
        }}
        .price-change {{
            font-size: 16px;
            margin-top: 5px;
        }}
        .positive {{ color: {COLORS['up']}; }}
        .negative {{ color: {COLORS['down']}; }}
        #chart-container {{
            width: 100%;
            height: 600px;
            background: {COLORS['bg']};
            border-radius: 8px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-top: 20px;
            padding: 15px;
            background: {COLORS['grid']};
            border-radius: 8px;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-label {{
            font-size: 12px;
            color: #787b86;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 16px;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="symbol-info">
            <h1>{symbol}</h1>
            <span class="interval">{interval} Interval</span>
        </div>
        <div class="price-info">
            <div class="current-price">${latest['close']:,.2f}</div>
            <div class="price-change {'positive' if change >= 0 else 'negative'}">
                {'+' if change >= 0 else ''}{change:,.2f} ({'+' if change_pct >= 0 else ''}{change_pct:.2f}%)
            </div>
        </div>
    </div>
    
    <div id="chart-container"></div>
    
    <div class="stats">
        <div class="stat-item">
            <div class="stat-label">Open</div>
            <div class="stat-value">${latest['open']:,.2f}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">High</div>
            <div class="stat-value">${latest['high']:,.2f}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Low</div>
            <div class="stat-value">${latest['low']:,.2f}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Volume</div>
            <div class="stat-value">{latest['volume']:,.2f}</div>
        </div>
    </div>

    <script>
        const chartContainer = document.getElementById('chart-container');
        
        const chart = LightweightCharts.createChart(chartContainer, {{
            layout: {{
                background: {{ color: '{COLORS['bg']}' }},
                textColor: '{COLORS['text']}',
            }},
            grid: {{
                vertLines: {{ color: '{COLORS['grid']}' }},
                horzLines: {{ color: '{COLORS['grid']}' }},
            }},
            crosshair: {{
                mode: LightweightCharts.CrosshairMode.Normal,
            }},
            rightPriceScale: {{
                borderColor: '{COLORS['grid']}',
            }},
            timeScale: {{
                borderColor: '{COLORS['grid']}',
                timeVisible: true,
                secondsVisible: false,
            }},
        }});
        
        // Candlestick series
        const candleSeries = chart.addCandlestickSeries({{
            upColor: '{COLORS['up']}',
            downColor: '{COLORS['down']}',
            borderUpColor: '{COLORS['up']}',
            borderDownColor: '{COLORS['down']}',
            wickUpColor: '{COLORS['up']}',
            wickDownColor: '{COLORS['down']}',
        }});
        
        candleSeries.setData({json.dumps(candles)});
        
        // Volume histogram
        const volumeSeries = chart.addHistogramSeries({{
            color: '{COLORS['up']}',
            priceFormat: {{
                type: 'volume',
            }},
            priceScaleId: '',
            scaleMargins: {{
                top: 0.85,
                bottom: 0,
            }},
        }});
        
        volumeSeries.setData({json.dumps(volumes)});
        
        // Fit content
        chart.timeScale().fitContent();
        
        // Handle resize
        window.addEventListener('resize', () => {{
            chart.applyOptions({{ width: chartContainer.clientWidth }});
        }});
    </script>
</body>
</html>'''
    
    return html


def generate_all_charts():
    """Generate charts for all symbols and intervals"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    intervals = ['1h', '4h', '1d', '1w', '1M']
    
    generated = []
    
    for symbol in symbols:
        for interval in intervals:
            print(f"Generating chart for {symbol} {interval}...")
            
            data = load_ohlcv_data(symbol, interval)
            
            if data:
                html = generate_chart_html(symbol, interval, data)
                
                # Save individual chart
                chart_file = OUTPUT_DIR / f"{symbol}_{interval}.html"
                with open(chart_file, 'w') as f:
                    f.write(html)
                
                generated.append({
                    'symbol': symbol,
                    'interval': interval,
                    'file': str(chart_file),
                    'candles': len(data)
                })
                
                print(f"  ✓ Saved {chart_file} ({len(data)} candles)")
            else:
                print(f"  ✗ No data available")
    
    # Generate index page
    generate_index_page(generated)
    
    return generated


def generate_index_page(charts: List[Dict]):
    """Generate an index page with links to all charts"""
    
    html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Binance Charts</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            background: #131722; 
            color: #d1d4dc; 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            padding: 40px;
        }
        h1 { 
            font-size: 32px; 
            margin-bottom: 30px;
            text-align: center;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        .chart-card {
            background: #2a2e39;
            border-radius: 12px;
            padding: 20px;
            text-decoration: none;
            color: inherit;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .chart-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .symbol {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 5px;
        }
        .interval {
            font-size: 14px;
            color: #787b86;
            margin-bottom: 15px;
        }
        .preview {
            width: 100%;
            height: 150px;
            background: #131722;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 48px;
        }
        .candles-count {
            font-size: 12px;
            color: #787b86;
            margin-top: 10px;
            text-align: right;
        }
        .btc { color: #f7931a; }
        .eth { color: #627eea; }
        .bnb { color: #f3ba2f; }
    </style>
</head>
<body>
    <h1>📊 Binance Candlestick Charts</h1>
    <div class="grid">
'''
    
    for chart in charts:
        symbol_class = chart['symbol'][:3].lower()
        emoji = {'BTCUSDT': '₿', 'ETHUSDT': 'Ξ', 'BNBUSDT': '🔶'}.get(chart['symbol'], '📈')
        
        html += f'''
        <a href="{chart['symbol']}_{chart['interval']}.html" class="chart-card">
            <div class="symbol {symbol_class}">{chart['symbol']}</div>
            <div class="interval">{chart['interval']} Interval</div>
            <div class="preview {symbol_class}">{emoji}</div>
            <div class="candles-count">{chart['candles']} candles</div>
        </a>
'''
    
    html += '''
    </div>
</body>
</html>'''
    
    index_file = OUTPUT_DIR / 'index.html'
    with open(index_file, 'w') as f:
        f.write(html)
    
    print(f"\n✓ Index page saved: {index_file}")


def main():
    """Main execution"""
    print("=" * 60)
    print("BINANCE CANDLESTICK CHART GENERATOR")
    print("=" * 60)
    
    charts = generate_all_charts()
    
    print("\n" + "=" * 60)
    print(f"Generated {len(charts)} charts")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"View index: file://{OUTPUT_DIR}/index.html")
    print("=" * 60)


if __name__ == '__main__':
    main()
