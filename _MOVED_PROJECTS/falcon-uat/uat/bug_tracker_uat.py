#!/usr/bin/env python3
"""
Falcon Platform UAT - Bug Tracker Verification
Tests all bugs from Falcon_Bug_Tracker_v2_RETEST.xlsx
"""

import asyncio
import csv
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "https://falcon.up.railway.app"
RESULTS_FILE = "/root/.openclaw/workspace/projects/falcon/uat/bug_tracker_verification.csv"

CREDENTIALS = {
    "client": {"email": "ahmed.hassan@techcorp.ae", "password": "SecurePass123!"},
    "admin": {"email": "admin@example.com", "password": "admin123"},
    "candidate": {"email": "interviewee@example.com", "password": "interviewee123"}
}

class BugTrackerUAT:
    def __init__(self):
        self.results = []
        self.browser = None
        self.context = None
        self.page = None
        
    async def setup(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True, args=['--no-sandbox'])
        self.context = await self.browser.new_context(viewport={'width': 1280, 'height': 720})
        
    async def teardown(self):
        if self.context: await self.context.close()
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
            
    def log(self, bug_id, status, actual, notes=""):
        """Log bug verification result"""
        self.results.append({
            'bug_id': bug_id,
            'status': status,
            'actual_result': actual,
            'notes': notes,
            'timestamp': datetime.now().isoformat()
        })
        icon = '✅ FIXED' if status == 'FIXED' else '🔴 OPEN' if status == 'OPEN' else '⚠️ PARTIAL'
        print(f"{icon} {bug_id}: {notes[:80]}...")
        
    async def save_results(self):
        with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['bug_id', 'status', 'actual_result', 'notes', 'timestamp'])
            writer.writeheader()
            writer.writerows(self.results)
        print(f"\n📊 Results saved to: {RESULTS_FILE}")
        
    # ==================== LANDING PAGE BUGS ====================
    
    async def test_landing_page_bugs(self):
        print("\n" + "="*80)
        print("LANDING PAGE BUGS")
        print("="*80)
        
        self.page = await self.context.new_page()
        await self.page.goto(BASE_URL)
        await self.page.wait_for_load_state('networkidle')
        
        # LP-01: Start Free Trial CTA
        try:
            await self.page.click('button:has-text("Start Free Trial")')
            await asyncio.sleep(2)
            url = self.page.url
            if '/login' in url:
                self.log('LP-01', 'OPEN', f'Redirects to {url}', 
                    'Start Free Trial still goes to login page instead of registration')
            else:
                self.log('LP-01', 'FIXED', f'Redirects to {url}', 'Now goes to registration')
        except Exception as e:
            self.log('LP-01', 'ERROR', str(e), 'Error during test')
            
        await self.page.goto(BASE_URL)
        await asyncio.sleep(1)
        
        # LP-02: Missing favicon
        try:
            favicon = await self.page.query_selector('link[rel="icon"], link[rel="shortcut icon"]')
            if favicon:
                href = await favicon.get_attribute('href')
                self.log('LP-02', 'FIXED', f'Favicon found: {href}', 'Favicon is present')
            else:
                self.log('LP-02', 'OPEN', 'No favicon found', 'Missing favicon in browser tab')
        except Exception as e:
            self.log('LP-02', 'ERROR', str(e), 'Error checking favicon')
            
        # LP-03: Broken emoji in stats
        try:
            content = await self.page.content()
            # Check for broken emoji (replacement character or box)
            if '\\u25a1' in content or '\\u25a0' in content or '&#9633;' in content:
                self.log('LP-03', 'OPEN', 'Broken emoji character found', 'Stats show broken emoji')
            else:
                self.log('LP-03', 'FIXED', 'Emojis render correctly', 'Stats emojis display properly')
        except Exception as e:
            self.log('LP-03', 'ERROR', str(e), 'Error checking emojis')
            
        # LP-04: Watch Demo button
        try:
            await self.page.click('button:has-text("Watch Demo")')
            await asyncio.sleep(2)
            url = self.page.url
            if url == BASE_URL or '/login' in url:
                self.log('LP-04', 'OPEN', f'No action or goes to {url}', 'Watch Demo has no demo functionality')
            else:
                self.log('LP-04', 'FIXED', f'Opens demo at {url}', 'Demo video/modal works')
        except Exception as e:
            self.log('LP-04', 'ERROR', str(e), 'Error clicking Watch Demo')
            
        await self.page.goto(BASE_URL)
        await asyncio.sleep(1)
        
        # LP-05: See it in action links
        try:
            links = await self.page.query_selector_all('button:has-text("See it in action")')
            if links:
                await links[0].click()
                await asyncio.sleep(2)
                url = self.page.url
                if url == BASE_URL or '/login' in url:
                    self.log('LP-05', 'OPEN', f'No navigation (stays at {url})', 'See it in action links do not work')
                else:
                    self.log('LP-05', 'FIXED', f'Navigates to {url}', 'Links work correctly')
        except Exception as e:
            self.log('LP-05', 'ERROR', str(e), 'Error testing links')
            
        await self.page.goto(BASE_URL)
        await asyncio.sleep(1)
        
        # LP-06: Testimonials placeholder initials
        try:
            content = await self.page.content()
            # Check for single letter avatars pattern
            if '"H"' in content and '"T"' in content and '"V"' in content and '"R"' in content:
                self.log('LP-06', 'OPEN', 'Single-letter avatars (H, T, V, R)', 'Testimonials use placeholder initials')
            else:
                self.log('LP-06', 'FIXED', 'Real names/photos found', 'Testimonials show proper avatars')
        except Exception as e:
            self.log('LP-06', 'ERROR', str(e), 'Error checking testimonials')
            
        # LP-07: Request Demo button
        try:
            await self.page.click('button:has-text("Request Demo")')
            await asyncio.sleep(2)
            url = self.page.url
            if '/login' in url or url == BASE_URL:
                self.log('LP-07', 'OPEN', f'Goes to {url}', 'Request Demo does not open form')
            else:
                self.log('LP-07', 'FIXED', f'Opens form at {url}', 'Request Demo works')
        except Exception as e:
            self.log('LP-07', 'ERROR', str(e), 'Error clicking Request Demo')
            
        await self.page.close()
        
    # ==================== HELP CENTER BUGS ====================
    
    async def test_help_center_bugs(self):
        print("\n" + "="*80)
        print("HELP CENTER BUGS")
        print("="*80)
        
        self.page = await self.context.new_page()
        await self.page.goto(f"{BASE_URL}/help")
        await asyncio.sleep(2)
        
        # HC-01: FAQ items don't expand
        try:
            # Find FAQ items
            faq_items = await self.page.query_selector_all('details, [role="button"]')
            if len(faq_items) > 1:
                # Click second FAQ (first one reportedly works)
                await faq_items[1].click()
                await asyncio.sleep(1)
                # Check if content is visible
                content = await self.page.content()
                if 'open' in content or await faq_items[1].get_attribute('open'):
                    self.log('HC-01', 'FIXED', 'FAQ items expand correctly', 'All FAQs work')
                else:
                    self.log('HC-01', 'OPEN', 'FAQ does not expand/show content', 'Most FAQ items do not expand')
            else:
                self.log('HC-01', 'NOT_FOUND', 'FAQ items not found', 'Could not locate FAQ elements')
        except Exception as e:
            self.log('HC-01', 'ERROR', str(e), 'Error testing FAQ')
            
        await self.page.close()
        
    # ==================== CLIENT BUGS ====================
    
    async def test_client_bugs(self):
        print("\n" + "="*80)
        print("CLIENT USER BUGS")
        print("="*80)
        
        self.page = await self.context.new_page()
        
        # Login as client
        await self.page.goto(f"{BASE_URL}/login")
        await self.page.fill('input[type="email"]', CREDENTIALS['client']['email'])
        await self.page.fill('input[type="password"]', CREDENTIALS['client']['password'])
        await self.page.click('button:has-text("Sign in")')
        await asyncio.sleep(3)
        
        if '/dashboard' not in self.page.url:
            self.log('CLIENT-AUTH', 'ERROR', f'Login failed: {self.page.url}', 'Cannot test client bugs')
            await self.page.close()
            return
            
        # CL-01: Candidates stat shows 0 despite interviews
        try:
            content = await self.page.content()
            # Look for Candidates: 0 and Interviews: >0
            import re
            cand_match = re.search(r'Candidates.*?([0-9]+)', content)
            int_match = re.search(r'Interviews.*?([0-9]+)', content)
            
            cand_count = int(cand_match.group(1)) if cand_match else 0
            int_count = int(int_match.group(1)) if int_match else 0
            
            if cand_count == 0 and int_count > 0:
                self.log('CL-01', 'OPEN', f'Candidates: {cand_count}, Interviews: {int_count}', 
                    'Shows 0 candidates but has scheduled interviews')
            else:
                self.log('CL-01', 'FIXED', f'Candidates: {cand_count}, Interviews: {int_count}', 
                    'Stats are consistent')
        except Exception as e:
            self.log('CL-01', 'ERROR', str(e), 'Error checking stats')
            
        # CL-02: Create Job quick action
        try:
            await self.page.goto(f"{BASE_URL}/dashboard")
            await asyncio.sleep(2)
            await self.page.click('text=/Create Job/i')
            await asyncio.sleep(2)
            url = self.page.url
            if '/jobs/new' in url:
                self.log('CL-02', 'FIXED', f'Navigates to {url}', 'Create Job works correctly')
            else:
                self.log('CL-02', 'OPEN', f'Stays at {url}', 'Create Job does not navigate')
        except Exception as e:
            self.log('CL-02', 'ERROR', str(e), 'Error testing Create Job')
            
        # CL-04: Jobs page shows 0 jobs
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/jobs")
            await asyncio.sleep(3)
            content = await self.page.content()
            if '0 of 0 jobs' in content or 'Showing 0' in content:
                self.log('CL-04', 'OPEN', 'Shows 0 jobs', 'Jobs page shows 0 despite dashboard showing active jobs')
            else:
                self.log('CL-04', 'FIXED', 'Jobs display correctly', 'Jobs page shows actual jobs')
        except Exception as e:
            self.log('CL-04', 'ERROR', str(e), 'Error checking jobs')
            
        # CL-06: Interviews page loading
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/interviews")
            await asyncio.sleep(3)
            content = await self.page.content()
            if 'skeleton' in content.lower() or 'loading' in content.lower():
                self.log('CL-06', 'OPEN', 'Still loading/skeleton', 'Interviews page stuck in loading state')
            else:
                self.log('CL-06', 'FIXED', 'Interviews loaded', 'Interviews page displays data')
        except Exception as e:
            self.log('CL-06', 'ERROR', str(e), 'Error checking interviews')
            
        # CL-08: Candidates page shows 0
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/candidates")
            await asyncio.sleep(3)
            content = await self.page.content()
            if '0 of 0 candidates' in content or 'Showing 0' in content:
                self.log('CL-08', 'OPEN', 'Shows 0 candidates', 'Candidates page empty despite scheduled interviews')
            else:
                self.log('CL-08', 'FIXED', 'Candidates display', 'Candidates page shows data')
        except Exception as e:
            self.log('CL-08', 'ERROR', str(e), 'Error checking candidates')
            
        # CL-09: Generate with AI button
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/jobs/new")
            await asyncio.sleep(2)
            # Fill in job title
            await self.page.fill('input[name="title"]', 'Test Job')
            await self.page.fill('input[name="designation"]', 'Test Role')
            # Click Generate with AI
            await self.page.click('button:has-text("Generate with AI")')
            await asyncio.sleep(5)  # Wait for AI generation
            # Check if description field has content
            desc = await self.page.input_value('textarea[name="description"]')
            if desc and len(desc) > 10:
                self.log('CL-09', 'FIXED', 'Description generated', 'AI generation works')
            else:
                self.log('CL-09', 'OPEN', 'Description empty', 'Generate with AI does not populate field')
        except Exception as e:
            self.log('CL-09', 'ERROR', str(e), 'Error testing AI generation')
            
        await self.page.close()
        
    # ==================== ADMIN BUGS ====================
    
    async def test_admin_bugs(self):
        print("\n" + "="*80)
        print("ADMIN USER BUGS")
        print("="*80)
        
        self.page = await self.context.new_page()
        
        # Login as admin
        await self.page.goto(f"{BASE_URL}/login")
        await self.page.fill('input[type="email"]', CREDENTIALS['admin']['email'])
        await self.page.fill('input[type="password"]', CREDENTIALS['admin']['password'])
        await self.page.click('button:has-text("Sign in")')
        await asyncio.sleep(3)
        
        # AD-01: Admin dashboard shows 0
        try:
            content = await self.page.content()
            # Check if all stats are 0
            import re
            zeros = len(re.findall(r'>0<', content))
            if zeros > 5:
                self.log('AD-01', 'OPEN', f'Found {zeros} zero values', 'Admin dashboard shows 0 across all stats')
            else:
                self.log('AD-01', 'FIXED', 'Stats show values', 'Admin dashboard displays real data')
        except Exception as e:
            self.log('AD-01', 'ERROR', str(e), 'Error checking admin stats')
            
        # AD-09: Users page crash
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/admin/users")
            await asyncio.sleep(3)
            content = await self.page.content()
            if 'error' in content.lower() or 'crash' in content.lower() or 'something went wrong' in content.lower():
                self.log('AD-09', 'OPEN', 'Page shows error', 'Users page causes app crash')
            else:
                self.log('AD-09', 'FIXED', 'Page loads', 'Users page works correctly')
        except Exception as e:
            self.log('AD-09', 'ERROR', str(e), 'Error accessing users page')
            
        await self.page.close()
        
    # ==================== MAIN EXECUTION ====================
    
    async def run_all_tests(self):
        print("\n" + "🚀"*40)
        print("FALCON BUG TRACKER VERIFICATION")
        print("Testing all bugs from Excel tracker")
        print("Started:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("🚀"*40)
        
        await self.setup()
        
        try:
            await self.test_landing_page_bugs()
            await self.test_help_center_bugs()
            await self.test_client_bugs()
            await self.test_admin_bugs()
        finally:
            await self.teardown()
            
        await self.save_results()
        
        # Summary
        print("\n" + "="*80)
        print("BUG VERIFICATION SUMMARY")
        print("="*80)
        
        fixed = sum(1 for r in self.results if r['status'] == 'FIXED')
        open_bugs = sum(1 for r in self.results if r['status'] == 'OPEN')
        errors = sum(1 for r in self.results if r['status'] == 'ERROR')
        
        print(f"Total Bugs Tested: {len(self.results)}")
        print(f"✅ FIXED: {fixed}")
        print(f"🔴 STILL OPEN: {open_bugs}")
        print(f"⚠️ ERRORS: {errors}")
        
        print(f"\n📊 Detailed results: {RESULTS_FILE}")

if __name__ == "__main__":
    uat = BugTrackerUAT()
    asyncio.run(uat.run_all_tests())
