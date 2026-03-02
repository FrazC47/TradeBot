#!/usr/bin/env python3
"""
Chart cleanup script - removes chart files older than 7 days
"""

import os
from datetime import datetime, timedelta
from pathlib import Path

CHARTS_DIR = Path('/root/.openclaw/workspace/charts')
CHARTS_PNG_DIR = Path('/root/.openclaw/workspace/charts_png')
MAX_AGE_DAYS = 7

def cleanup_old_files(directory: Path, max_age_days: int = 7):
    """Remove files older than max_age_days"""
    if not directory.exists():
        print(f"Directory {directory} does not exist")
        return 0, 0
    
    cutoff_time = datetime.now() - timedelta(days=max_age_days)
    removed_count = 0
    total_size_freed = 0
    
    for file_path in directory.iterdir():
        if file_path.is_file():
            # Get file modification time
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            if mtime < cutoff_time:
                file_size = file_path.stat().st_size
                try:
                    file_path.unlink()
                    removed_count += 1
                    total_size_freed += file_size
                    print(f"Removed: {file_path.name} (age: {(datetime.now() - mtime).days} days)")
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")
    
    return removed_count, total_size_freed

def main():
    print(f"Chart Cleanup - Removing files older than {MAX_AGE_DAYS} days")
    print("=" * 60)
    
    # Cleanup HTML charts
    print("\nCleaning HTML charts...")
    html_removed, html_size = cleanup_old_files(CHARTS_DIR, MAX_AGE_DAYS)
    
    # Cleanup PNG charts
    print("\nCleaning PNG charts...")
    png_removed, png_size = cleanup_old_files(CHARTS_PNG_DIR, MAX_AGE_DAYS)
    
    total_removed = html_removed + png_removed
    total_size_mb = (html_size + png_size) / (1024 * 1024)
    
    print("\n" + "=" * 60)
    print(f"Cleanup complete:")
    print(f"  HTML charts removed: {html_removed}")
    print(f"  PNG charts removed: {png_removed}")
    print(f"  Total files removed: {total_removed}")
    print(f"  Space freed: {total_size_mb:.2f} MB")
    print("=" * 60)

if __name__ == '__main__':
    main()
