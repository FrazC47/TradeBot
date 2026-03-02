#!/usr/bin/env python3
"""
Crypto Operations Monitor
Checks health of all crypto data pipelines and cron jobs
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Configuration
WORKSPACE = Path("/root/.openclaw/workspace/projects/crypto-analysis")
OPS_DIR = WORKSPACE / "analysis" / "ops"
CHARTS_DIR = WORKSPACE / "charts"
LOG_FILE = Path("/root/.openclaw/workspace/compass_alerts.log")

# Alert thresholds
WARNING_FAILURES = 3
CRITICAL_FAILURES = 5
DATA_GAP_MINUTES = 15

# Systems to monitor
SYSTEMS = {
    "binance_chart_generator": {
        "name": "Chart Generator",
        "schedule": "*/5 * * * *",
        "check_file": CHARTS_DIR / "BTCUSDT_1h.html"
    },
    "binance_kline_monitor": {
        "name": "Kline Monitor", 
        "schedule": "*/5 * * * *",
        "check_file": None
    },
    "compass_futures_data": {
        "name": "Futures Data Fetcher",
        "schedule": "*/5 * * * *",
        "check_file": None
    },
    "compass_analysis_alert": {
        "name": "COMPASS Analysis",
        "schedule": "*/10 * * * *",
        "check_file": LOG_FILE
    },
    "chart_cleanup": {
        "name": "Daily Cleanup",
        "schedule": "0 2 * * *",
        "check_file": None
    }
}

def get_file_mtime(filepath):
    """Get file modification time as datetime"""
    try:
        stat = os.stat(filepath)
        return datetime.fromtimestamp(stat.st_mtime, tz=timezone(timedelta(hours=8)))
    except (FileNotFoundError, OSError):
        return None

def get_log_last_entry(log_path):
    """Get timestamp of last log entry"""
    try:
        with open(log_path, 'r') as f:
            lines = f.readlines()
            if lines:
                last_line = lines[-1]
                # Parse timestamp from log line
                # Format: 2026-02-26T08:18:05.554813 | ...
                timestamp_str = last_line.split(' | ')[0]
                dt = datetime.fromisoformat(timestamp_str)
                # Ensure timezone-aware
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))
                return dt
    except (FileNotFoundError, IndexError, ValueError):
        pass
    return None

def calculate_staleness(last_time, current_time):
    """Calculate how stale data is in minutes"""
    if not last_time:
        return None
    diff = current_time - last_time
    return diff.total_seconds() / 60

def check_cron_status():
    """Check if cron jobs are configured"""
    import subprocess
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        return result.returncode == 0 and 'crypto' in result.stdout.lower()
    except:
        return False

def load_state():
    """Load previous monitor state"""
    state_file = OPS_DIR / "monitor_state.json"
    if state_file.exists():
        with open(state_file, 'r') as f:
            return json.load(f)
    return {"systems": {}}

def save_state(state):
    """Save monitor state"""
    state_file = OPS_DIR / "monitor_state.json"
    OPS_DIR.mkdir(parents=True, exist_ok=True)
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2, default=str)

def run_health_check():
    """Main health check function"""
    now = datetime.now(tz=timezone(timedelta(hours=8)))
    state = load_state()
    
    # Update check time
    state['last_check'] = now.isoformat()
    
    alerts = []
    
    # Check chart freshness
    chart_file = SYSTEMS['binance_chart_generator']['check_file']
    chart_mtime = get_file_mtime(chart_file)
    chart_stale = calculate_staleness(chart_mtime, now)
    
    # Check alert log freshness
    alert_last = get_log_last_entry(LOG_FILE)
    alert_stale = calculate_staleness(alert_last, now)
    
    state['data_freshness'] = {
        'charts_last_updated': chart_mtime.isoformat() if chart_mtime else None,
        'alerts_last_updated': alert_last.isoformat() if alert_last else None,
        'charts_stale_minutes': round(chart_stale, 1) if chart_stale else None,
        'alerts_stale_minutes': round(alert_stale, 1) if alert_stale else None
    }
    
    # Check each system
    for system_id, config in SYSTEMS.items():
        system_state = state.get('systems', {}).get(system_id, {})
        
        # Determine status based on data freshness
        if system_id == 'binance_chart_generator':
            if chart_stale and chart_stale > DATA_GAP_MINUTES:
                status = 'DOWN'
                alert_level = 'CRITICAL' if chart_stale > 60 else 'WARNING'
                failures = int(chart_stale / 5)  # Approximate missed runs
            else:
                status = 'HEALTHY'
                alert_level = 'INFO'
                failures = 0
                
        elif system_id == 'compass_analysis_alert':
            if alert_stale and alert_stale > DATA_GAP_MINUTES:
                status = 'DEGRADED'
                alert_level = 'WARNING'
                failures = int(alert_stale / 10)
            else:
                status = 'HEALTHY'
                alert_level = 'INFO'
                failures = 0
        else:
            status = 'UNKNOWN'
            alert_level = 'WARNING'
            failures = system_state.get('consecutive_failures', 0)
        
        # Update system state
        state.setdefault('systems', {})[system_id] = {
            'name': config['name'],
            'schedule': config['schedule'],
            'status': status,
            'alert_level': alert_level,
            'consecutive_failures': failures,
            'last_check': now.isoformat()
        }
        
        # Generate alerts
        if failures >= CRITICAL_FAILURES:
            alerts.append({
                'system': system_id,
                'level': 'CRITICAL',
                'message': f"{config['name']} has {failures} consecutive failures"
            })
        elif failures >= WARNING_FAILURES:
            alerts.append({
                'system': system_id,
                'level': 'WARNING',
                'message': f"{config['name']} has {failures} consecutive failures"
            })
    
    # Check cron configuration
    if not check_cron_status():
        alerts.append({
            'system': 'cron_configuration',
            'level': 'CRITICAL',
            'message': 'No crontab found for crypto jobs'
        })
    
    state['active_alerts'] = alerts
    state['alert_count'] = len(alerts)
    
    save_state(state)
    
    return state, alerts

def generate_report(state, alerts):
    """Generate human-readable report"""
    now = datetime.now(tz=timezone(timedelta(hours=8)))
    
    report = f"""# Crypto Operations Monitor - Status Report

**Generated:** {now.strftime('%Y-%m-%d %H:%M %Z')}  
**Status:** {'🔴 CRITICAL' if any(a['level'] == 'CRITICAL' for a in alerts) else '🟡 WARNING' if alerts else '🟢 HEALTHY'}

---

## Active Alerts ({len(alerts)})

"""
    
    for alert in alerts:
        emoji = '🔴' if alert['level'] == 'CRITICAL' else '🟡' if alert['level'] == 'WARNING' else 'ℹ️'
        report += f"### {emoji} {alert['system']}\n"
        report += f"- **Level:** {alert['level']}\n"
        report += f"- **Message:** {alert['message']}\n\n"
    
    report += "## System Status\n\n"
    report += "| System | Status | Last Update | Alert Level |\n"
    report += "|--------|--------|-------------|-------------|\n"
    
    for system_id, system in state.get('systems', {}).items():
        status_emoji = {'HEALTHY': '🟢', 'DEGRADED': '🟡', 'DOWN': '🔴', 'UNKNOWN': '⚪'}
        emoji = status_emoji.get(system['status'], '⚪')
        report += f"| {system['name']} | {emoji} {system['status']} | {system.get('last_check', 'N/A')[:16]} | {system['alert_level']} |\n"
    
    report += f"\n## Data Freshness\n\n"
    freshness = state.get('data_freshness', {})
    report += f"- **Charts Last Updated:** {freshness.get('charts_last_updated', 'N/A')}\n"
    report += f"- **Alerts Last Updated:** {freshness.get('alerts_last_updated', 'N/A')}\n"
    report += f"- **Charts Stale:** {freshness.get('charts_stale_minutes', 'N/A')} minutes\n"
    report += f"- **Alerts Stale:** {freshness.get('alerts_stale_minutes', 'N/A')} minutes\n"
    
    return report

if __name__ == '__main__':
    state, alerts = run_health_check()
    report = generate_report(state, alerts)
    
    # Save report
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    report_file = OPS_DIR / f"{timestamp}_status_report.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    # Print summary
    print(f"Health check complete. {len(alerts)} alerts active.")
    print(f"Report saved to: {report_file}")
    
    if alerts:
        print("\nActive Alerts:")
        for alert in alerts:
            print(f"  [{alert['level']}] {alert['system']}: {alert['message']}")
