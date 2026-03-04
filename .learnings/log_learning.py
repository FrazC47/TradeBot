#!/usr/bin/env python3
"""
Self-Improvement Learning Logger
Quick utility to add learnings to the log
"""

import sys
from datetime import datetime
from pathlib import Path

LEARNINGS_FILE = Path('/root/.openclaw/workspace/.learnings/LEARNINGS.md')

def add_learning(title, priority='medium', area='general', issue='', fix='', prevention=''):
    """Add a new learning entry"""
    
    date = datetime.now().strftime('%Y-%m-%d')
    
    entry = f"""
### [{date}] {title}

**Priority**: {priority}  
**Status**: pending  
**Area**: {area}

**Summary**: {issue}

**Context**:
{issue}

**Solution**:
{fix}

**Prevention**:
{prevention}

---
"""
    
    # Read current content
    if LEARNINGS_FILE.exists():
        content = LEARNINGS_FILE.read_text()
    else:
        content = "# Self-Improvement Learnings Log\n\n"
    
    # Find the right section based on priority
    sections = {
        'critical': '## Critical Learnings',
        'high': '## High Priority Learnings',
        'medium': '## Medium Priority Learnings',
        'low': '## Low Priority Learnings'
    }
    
    section_header = sections.get(priority, '## Medium Priority Learnings')
    
    # Insert after section header
    if section_header in content:
        parts = content.split(section_header, 1)
        new_content = parts[0] + section_header + entry + parts[1]
    else:
        new_content = content + entry
    
    # Write back
    LEARNINGS_FILE.write_text(new_content)
    print(f"✅ Learning added: {title}")

def review_learnings(priority=None):
    """Review existing learnings"""
    
    if not LEARNINGS_FILE.exists():
        print("No learnings file found.")
        return
    
    content = LEARNINGS_FILE.read_text()
    
    if priority:
        # Extract section for priority
        sections = content.split('## ')
        for section in sections:
            if section.startswith(priority.capitalize()):
                print(f"\n## {section}")
                return
    else:
        print(content)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 log_learning.py 'Title' [priority] [area] [issue] [fix] [prevention]")
        print("  python3 log_learning.py review [priority]")
        sys.exit(1)
    
    if sys.argv[1] == 'review':
        priority = sys.argv[2] if len(sys.argv) > 2 else None
        review_learnings(priority)
    else:
        title = sys.argv[1]
        priority = sys.argv[2] if len(sys.argv) > 2 else 'medium'
        area = sys.argv[3] if len(sys.argv) > 3 else 'general'
        issue = sys.argv[4] if len(sys.argv) > 4 else ''
        fix = sys.argv[5] if len(sys.argv) > 5 else ''
        prevention = sys.argv[6] if len(sys.argv) > 6 else ''
        
        add_learning(title, priority, area, issue, fix, prevention)
