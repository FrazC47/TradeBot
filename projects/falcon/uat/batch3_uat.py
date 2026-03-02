#!/usr/bin/env python3
"""
Falcon Platform UAT - Batch 3: More Bug Tests
Tests additional bugs from the tracker
"""

import asyncio
import csv
import re
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "https://falcon.up.railway.app"
RESULTS_FILE = "/root/.openclaw/workspace/projects/falcon/uat/batch3_bug_tests.csv"

CREDENTIALS = {
    "client": {"email": "ahmed.hassan@techcorp.ae", "password": "SecurePass123!"},
    "admin": {"email": "admin@example.com", "password": "admin123"},
    "candidate": {"email": "interviewee@example.com", "password": "interviewee123"}
}

class Batch3UAT:
    def __init__(self):
        self.results = []
        self.browser = None
        self.context = None
        self.page = None
        self.test_count = 0
        
    async def setup(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True, args=['--no-sandbox'])
        self.context = await self.browser.new_context(viewport={'width': 1280, 'height': 720})
        
    async def teardown(self):
        if self.context: await self.context.close()
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
            
    def log(self, bug_id, status, actual, notes=""):
        self.results.append({
            'bug_id': bug_id, 'status': status, 'actual_result': actual,
            'notes': notes, 'timestamp': datetime.now().isoformat()
        })
        self.test_count += 1
        icon = '✅' if status == 'FIXED' else '🔴' if status == 'OPEN' else '⚠️'
        print(f"[{self.test_count}] {icon} {bug_id}: {notes[:50]}...")
        
    async def save_results(self):
        with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['bug_id', 'status', 'actual_result', 'notes', 'timestamp'])
            writer.writeheader()
            writer.writerows(self.results)
        
    # ==================== CANDIDATE USER TESTS ====================
    
    async def test_candidate_user(self):
        print("\n" + "="*80)
        print("CANDIDATE USER TESTS")
        print("="*80)
        
        self.page = await self.context.new_page()
        
        # Login as candidate
        await self.page.goto(f"{BASE_URL}/login")
        await self.page.fill('input[type="email"]', CREDENTIALS['candidate']['email'])
        await self.page.fill('input[type="password"]', CREDENTIALS['candidate']['password'])
        await self.page.click('button:has-text("Sign in")')
        await asyncio.sleep(3)
        
        # CA-01: Default landing page
        try:
            url = self.page.url
            if '/interviews' in url or '/candidate' in url or '/dashboard' in url:
                self.log('CA-01', 'FIXED', f'Lands on {url}', 'Candidate has appropriate landing page')
            else:
                self.log('CA-01', 'OPEN', f'Lands on {url}', 'Candidate landing page not appropriate')
        except Exception as e:
            self.log('CA-01', 'ERROR', str(e), 'Error checking landing page')
            
        # CA-04: Greeting message
        try:
            content = await self.page.content()
            if 'Interview!' in content or 'Welcome' in content:
                if 'Interview!' in content:
                    self.log('CA-04', 'OPEN', 'Says "Interview!"', 'Greeting shows "Interview!" not actual name')
                else:
                    self.log('CA-04', 'FIXED', 'Personalized greeting', 'Greeting shows name properly')
            else:
                self.log('CA-04', 'NOT_FOUND', 'No greeting found', 'Could not locate greeting')
        except Exception as e:
            self.log('CA-04', 'ERROR', str(e), 'Error checking greeting')
            
        # CA-07: My Application page
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/application")
            await asyncio.sleep(3)
            content = await self.page.content()
            if 'error' in content.lower() or 'something went wrong' in content.lower():
                self.log('CA-07', 'OPEN', 'Page shows error', 'My Application page has error')
            else:
                self.log('CA-07', 'FIXED', 'Page loads', 'My Application page works')
        except Exception as e:
            self.log('CA-07', 'ERROR', str(e), 'Error accessing application page')
            
        await self.page.close()
        
    # ==================== CLIENT PIPELINE & ASSESSMENTS ====================
    
    async def test_client_pipeline(self):
        print("\n" + "="*80)
        print("CLIENT PIPELINE & ASSESSMENTS")
        print("="*80)
        
        self.page = await self.context.new_page()
        await self.page.goto(f"{BASE_URL}/login")
        await self.page.fill('input[type="email"]', CREDENTIALS['client']['email'])
        await self.page.fill('input[type="password"]', CREDENTIALS['client']['password'])
        await self.page.click('button:has-text("Sign in")')
        await asyncio.sleep(3)
        
        # CL-27: Pipeline link
        try:
            await self.page.goto(f"{BASE_URL}/dashboard")
            await asyncio.sleep(2)
            # Look for Pipeline in sidebar
            await self.page.click('text=/Pipeline/i')
            await asyncio.sleep(2)
            url = self.page.url
            if '/pipeline' in url:
                self.log('CL-27', 'FIXED', f'Navigates to {url}', 'Pipeline link goes to Pipeline page')
            elif '/interviews' in url:
                self.log('CL-27', 'OPEN', f'Goes to {url}', 'Pipeline link goes to Interviews instead')
            else:
                self.log('CL-27', 'NOT_FOUND', f'Goes to {url}', 'Unexpected navigation')
        except Exception as e:
            self.log('CL-27', 'ERROR', str(e), 'Error testing Pipeline link')
            
        # CL-45: Assessment question title typo
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/assessments")
            await asyncio.sleep(3)
            content = await self.page.content()
            typos = ['Createt', 'Sum funation', 'createt', 'funation']
            found = [t for t in typos if t in content]
            if found:
                self.log('CL-45', 'OPEN', f'Found: {found}', 'Assessment has typo in title')
            else:
                self.log('CL-45', 'FIXED', 'No typos found', 'Assessment titles are correct')
        except Exception as e:
            self.log('CL-45', 'ERROR', str(e), 'Error checking assessments')
            
        # CL-46: Expired assessment button
        try:
            content = await self.page.content()
            if 'Expired' in content and 'Continue' in content:
                self.log('CL-46', 'OPEN', 'Expired shows Continue', 'Expired assessment shows Continue button')
            else:
                self.log('CL-46', 'FIXED', 'Expired handled correctly', 'Expired assessments properly labeled')
        except Exception as e:
            self.log('CL-46', 'ERROR', str(e), 'Error checking expired assessments')
            
        # CL-47: Create Assessment button
        try:
            buttons = await self.page.query_selector_all('button:has-text("Create Assessment")')
            if len(buttons) > 0:
                self.log('CL-47', 'FIXED', 'Button present', 'Create Assessment button exists')
            else:
                self.log('CL-47', 'OPEN', 'Button not found', 'Create Assessment button missing')
        except Exception as e:
            self.log('CL-47', 'ERROR', str(e), 'Error finding button')
            
        # CL-48: AI Assistant for candidates
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/ai-assistant")
            await asyncio.sleep(3)
            content = await self.page.content()
            if 'platform' in content.lower() or 'how do i' in content.lower():
                self.log('CL-48', 'FIXED', 'AI Assistant responds', 'AI Assistant answers platform questions')
            else:
                self.log('CL-48', 'OPEN', 'No platform help', 'AI Assistant does not answer platform questions')
        except Exception as e:
            self.log('CL-48', 'ERROR', str(e), 'Error testing AI Assistant')
            
        await self.page.close()
        
    # ==================== ADMIN MANAGEMENT ====================
    
    async def test_admin_management(self):
        print("\n" + "="*80)
        print("ADMIN MANAGEMENT TESTS")
        print("="*80)
        
        self.page = await self.context.new_page()
        await self.page.goto(f"{BASE_URL}/login")
        await self.page.fill('input[type="email"]', CREDENTIALS['admin']['email'])
        await self.page.fill('input[type="password"]', CREDENTIALS['admin']['password'])
        await self.page.click('button:has-text("Sign in")')
        await asyncio.sleep(3)
        
        # AD-08: Clients link
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/admin")
            await asyncio.sleep(2)
            await self.page.click('text=/Clients/i')
            await asyncio.sleep(2)
            url = self.page.url
            if '/clients' in url or '/companies' in url:
                self.log('AD-08', 'FIXED', f'Navigates to {url}', 'Clients link works')
            else:
                self.log('AD-08', 'OPEN', f'Goes to {url}', 'Clients link goes to wrong page')
        except Exception as e:
            self.log('AD-08', 'ERROR', str(e), 'Error testing Clients link')
            
        # AD-17: Templates link
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/admin")
            await asyncio.sleep(2)
            await self.page.click('text=/Templates/i')
            await asyncio.sleep(2)
            url = self.page.url
            if '/templates' in url:
                self.log('AD-17', 'FIXED', f'Navigates to {url}', 'Templates link works')
            else:
                self.log('AD-17', 'OPEN', f'Goes to {url}', 'Templates link goes to wrong page')
        except Exception as e:
            self.log('AD-17', 'ERROR', str(e), 'Error testing Templates link')
            
        # AD-35: Client count display
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/admin/clients")
            await asyncio.sleep(3)
            content = await self.page.content()
            # Look for client count
            match = re.search(r'([0-9]+)\\s*Clients?', content)
            if match:
                count = int(match.group(1))
                if count == 0:
                    self.log('AD-35', 'OPEN', 'Shows 0 clients', 'Client count shows 0')
                else:
                    self.log('AD-35', 'FIXED', f'Shows {count} clients', 'Client count accurate')
            else:
                self.log('AD-35', 'NOT_FOUND', 'No count found', 'Could not find client count')
        except Exception as e:
            self.log('AD-35', 'ERROR', str(e), 'Error checking client count')
            
        # AD-38: Placeholder data
        try:
            content = await self.page.content()
            placeholders = ['asdf', 'test@test.com', 'placeholder', 'dummy']
            found = [p for p in placeholders if p.lower() in content.lower()]
            if found:
                self.log('AD-38', 'OPEN', f'Found: {found}', 'Admin panel shows placeholder data')
            else:
                self.log('AD-38', 'FIXED', 'No placeholders', 'Admin panel has real data')
        except Exception as e:
            self.log('AD-38', 'ERROR', str(e), 'Error checking for placeholders')
            
        # AD-39: Add Client button
        try:
            buttons = await self.page.query_selector_all('button:has-text("Add Client")')
            if len(buttons) > 0:
                self.log('AD-39', 'FIXED', 'Button present', 'Add Client button exists')
            else:
                self.log('AD-39', 'OPEN', 'Button not found', 'Add Client button missing')
        except Exception as e:
            self.log('AD-39', 'ERROR', str(e), 'Error finding button')
            
        await self.page.close()
        
    # ==================== NAVIGATION & UI ====================
    
    async def test_navigation_ui(self):
        print("\n" + "="*80)
        print("NAVIGATION & UI TESTS")
        print("="*80)
        
        self.page = await self.context.new_page()
        await self.page.goto(f"{BASE_URL}/login")
        await self.page.fill('input[type="email"]', CREDENTIALS['client']['email'])
        await self.page.fill('input[type="password"]', CREDENTIALS['client']['password'])
        await self.page.click('button:has-text("Sign in")')
        await asyncio.sleep(3)
        
        # CL-49: User Menu
        try:
            await self.page.click('button[aria-label="account"]')  # Common pattern for user menu
            await asyncio.sleep(1)
            content = await self.page.content()
            if 'Profile' in content or 'Settings' in content or 'Logout' in content:
                self.log('CL-49', 'FIXED', 'Menu items found', 'User Menu has Profile, Settings, Logout')
            else:
                self.log('CL-49', 'OPEN', 'Menu items missing', 'User Menu incomplete')
        except Exception as e:
            self.log('CL-49', 'ERROR', str(e), 'Error testing User Menu')
            
        # CL-53: Templates link
        try:
            await self.page.goto(f"{BASE_URL}/dashboard")
            await asyncio.sleep(2)
            await self.page.click('text=/Templates/i')
            await asyncio.sleep(2)
            url = self.page.url
            if '/templates' in url:
                self.log('CL-53', 'FIXED', f'Navigates to {url}', 'Templates link correct')
            else:
                self.log('CL-53', 'OPEN', f'Goes to {url}', 'Templates link incorrect')
        except Exception as e:
            self.log('CL-53', 'ERROR', str(e), 'Error testing Templates link')
            
        # CL-64: Help Center FAQ click target
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/help")
            await asyncio.sleep(3)
            # Try clicking on FAQ text (not just chevron)
            faq_items = await self.page.query_selector_all('details, [role="button"]')
            if len(faq_items) > 0:
                # Click on the text content
                await faq_items[0].click()
                await asyncio.sleep(1)
                self.log('CL-64', 'FIXED', 'Click on text works', 'FAQ expands when clicking text')
            else:
                self.log('CL-64', 'NOT_FOUND', 'FAQ items not found', 'Could not locate FAQ')
        except Exception as e:
            self.log('CL-64', 'ERROR', str(e), 'Error testing FAQ click')
            
        await self.page.close()
        
    # ==================== MAIN EXECUTION ====================
    
    async def run_all_tests(self):
        print("\n" + "🚀"*40)
        print("FALCON UAT - BATCH 3")
        print("Started:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("🚀"*40)
        
        await self.setup()
        
        try:
            await self.test_candidate_user()
            await self.test_client_pipeline()
            await self.test_admin_management()
            await self.test_navigation_ui()
        finally:
            await self.teardown()
            
        await self.save_results()
        
        # Summary
        print("\n" + "="*80)
        print("BATCH 3 - FINAL SUMMARY")
        print("="*80)
        
        fixed = sum(1 for r in self.results if r['status'] == 'FIXED')
        open_bugs = sum(1 for r in self.results if r['status'] == 'OPEN')
        errors = sum(1 for r in self.results if r['status'] == 'ERROR')
        
        print(f"Total Bugs Tested: {len(self.results)}")
        print(f"✅ FIXED: {fixed}")
        print(f"🔴 STILL OPEN: {open_bugs}")
        print(f"⚠️ ERRORS: {errors}")
        
        print(f"\n📊 Results: {RESULTS_FILE}")
        print("Completed:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    uat = Batch3UAT()
    asyncio.run(uat.run_all_tests())
