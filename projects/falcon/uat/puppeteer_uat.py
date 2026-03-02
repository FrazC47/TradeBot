#!/usr/bin/env python3
"""
Direct Puppeteer-based UAT Testing for Falcon
Bypasses OpenClaw browser tool timeout issues
"""

import asyncio
from pyppeteer import launch

async def test_falcon():
    browser = await launch({
        'headless': True,
        'args': ['--no-sandbox', '--disable-gpu']
    })
    page = await browser.newPage()
    
    # Test landing page
    await page.goto('https://falcon.up.railway.app')
    print("✅ Landing page loaded")
    
    # Test LP-01: Start Free Trial
    await page.click('button:has-text("Start Free Trial")')
    await asyncio.sleep(2)
    url = page.url
    print(f"LP-01 Result: {url}")
    
    # More tests...
    
    await browser.close()

if __name__ == '__main__':
    asyncio.run(test_falcon())
