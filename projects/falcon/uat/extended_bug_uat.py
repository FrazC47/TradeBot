#!/usr/bin/env python3
"""
Falcon Platform UAT - Extended Bug Testing
Tests more bugs from the tracker with periodic progress updates
"""

import asyncio
import csv
import re
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "https://falcon.up.railway.app"
RESULTS_FILE = "/root/.openclaw/workspace/projects/falcon/uat/extended_bug_tests.csv"

CREDENTIALS = {
    "client": {"email": "ahmed.hassan@techcorp.ae", "password": "SecurePass123!"},
    "admin": {"email": "admin@example.com", "password": "admin123"},
    "candidate": {"email": "interviewee@example.com", "password": "interviewee123"}
}

class ExtendedBugUAT:
    def __init__(self):
        self.results = []
        self.browser = None
        self.context = None
        self.page = None
        self.test_count = 0
        self.total_tests = 30  # Estimated
        
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
        progress = f"[{self.test_count}/{self.total_tests}]"
        print(f"{progress} {icon} {bug_id}: {notes[:60]}...")
        
    async def save_results(self):
        with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['bug_id', 'status', 'actual_result', 'notes', 'timestamp'])
            writer.writeheader()
            writer.writerows(self.results)
        
    def print_progress(self, section):
        """Print progress update"""
        fixed = sum(1 for r in self.results if r['status'] == 'FIXED')
        open_bugs = sum(1 for r in self.results if r['status'] == 'OPEN')
        print(f"\n📊 PROGRESS UPDATE - {section}")
        print(f"   Tests completed: {self.test_count}")
        print(f"   ✅ FIXED: {fixed} | 🔴 OPEN: {open_bugs}")
        print("="*60)
        
    # ==================== CLIENT DASHBOARD & JOBS ====================
    
    async def test_client_dashboard_extended(self):
        """Extended client dashboard tests"""
        print("\n" + "="*80)
        print("CLIENT DASHBOARD EXTENDED TESTS")
        print("="*80)
        
        self.page = await self.context.new_page()
        await self.page.goto(f"{BASE_URL}/login")
        await self.page.fill('input[type="email"]', CREDENTIALS['client']['email'])
        await self.page.fill('input[type="password"]', CREDENTIALS['client']['password'])
        await self.page.click('button:has-text("Sign in")')
        await asyncio.sleep(3)
        
        # CL-03: Statistics inconsistent after interaction
        try:
            await self.page.goto(f"{BASE_URL}/dashboard")
            await asyncio.sleep(2)
            # Get initial stats
            content1 = await self.page.content()
            # Click a quick action
            await self.page.click('text=/View Candidates/i')
            await asyncio.sleep(2)
            await self.page.goto(f"{BASE_URL}/dashboard")
            await asyncio.sleep(2)
            content2 = await self.page.content()
            
            # Compare stats
            int_match1 = re.search(r'Interviews.*?([0-9]+)', content1)
            int_match2 = re.search(r'Interviews.*?([0-9]+)', content2)
            int1 = int(int_match1.group(1)) if int_match1 else 0
            int2 = int(int_match2.group(1)) if int_match2 else 0
            
            if int1 != int2:
                self.log('CL-03', 'OPEN', f'Interviews changed from {int1} to {int2}', 
                    'Stats inconsistent after interaction')
            else:
                self.log('CL-03', 'FIXED', f'Stats stable: {int1}', 'Statistics remain consistent')
        except Exception as e:
            self.log('CL-03', 'ERROR', str(e), 'Error testing stat consistency')
            
        # CL-05, CL-07: Sidebar navigation
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/help")
            await asyncio.sleep(2)
            # Try clicking Jobs in sidebar
            await self.page.click('text=/Jobs/i')
            await asyncio.sleep(2)
            url = self.page.url
            if '/jobs' in url:
                self.log('CL-05/07', 'FIXED', f'Navigated to {url}', 'Sidebar navigation works correctly')
            else:
                self.log('CL-05/07', 'OPEN', f'Went to {url}', 'Sidebar navigation offset/incorrect')
        except Exception as e:
            self.log('CL-05/07', 'ERROR', str(e), 'Error testing sidebar')
            
        # CL-17: Jobs page loads consistently
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/jobs")
            await asyncio.sleep(3)
            content = await self.page.content()
            if '0 of 0' in content:
                self.log('CL-17', 'OPEN', 'Shows 0 jobs on load', 'Jobs page inconsistent - shows 0 initially')
            else:
                self.log('CL-17', 'FIXED', 'Jobs load immediately', 'Jobs page loads consistently')
        except Exception as e:
            self.log('CL-17', 'ERROR', str(e), 'Error testing jobs load')
            
        # CL-18: Job cards show raw CV text
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/jobs")
            await asyncio.sleep(3)
            content = await self.page.content()
            # Check for CV-like content (phone numbers, LinkedIn, etc.)
            if re.search(r'\\+\\d|linkedin\\.com|@gmail\\.com|\\d{3}-\\d{4}', content):
                self.log('CL-18', 'OPEN', 'Raw CV text in job cards', 'Job cards display candidate CV instead of description')
            else:
                self.log('CL-18', 'FIXED', 'Proper job descriptions', 'Job cards show correct descriptions')
        except Exception as e:
            self.log('CL-18', 'ERROR', str(e), 'Error checking job cards')
            
        # CL-19: Placeholder job titles
        try:
            content = await self.page.content()
            placeholders = ['asdf', 'adf', 'testing', 'test job', 'placeholder']
            found = [p for p in placeholders if p.lower() in content.lower()]
            if found:
                self.log('CL-19', 'OPEN', f'Found: {found}', 'Job cards have placeholder/test titles')
            else:
                self.log('CL-19', 'FIXED', 'Professional job titles', 'All job titles are proper')
        except Exception as e:
            self.log('CL-19', 'ERROR', str(e), 'Error checking titles')
            
        # CL-20: Status badge lowercase
        try:
            content = await self.page.content()
            if 'published' in content.lower() and 'Published' not in content:
                self.log('CL-20', 'OPEN', 'Lowercase status badge', 'Status shows "published" not "Published"')
            else:
                self.log('CL-20', 'FIXED', 'Proper case status', 'Status badges use title case')
        except Exception as e:
            self.log('CL-20', 'ERROR', str(e), 'Error checking status')
            
        await self.page.close()
        self.print_progress("Client Dashboard Extended")
        
    # ==================== JOB CREATION WIZARD ====================
    
    async def test_job_creation_wizard(self):
        """Test job creation wizard bugs"""
        print("\n" + "="*80)
        print("JOB CREATION WIZARD TESTS")
        print("="*80)
        
        self.page = await self.context.new_page()
        await self.page.goto(f"{BASE_URL}/login")
        await self.page.fill('input[type="email"]', CREDENTIALS['client']['email'])
        await self.page.fill('input[type="password"]', CREDENTIALS['client']['password'])
        await self.page.click('button:has-text("Sign in")')
        await asyncio.sleep(3)
        
        # Navigate to job creation
        await self.page.goto(f"{BASE_URL}/dashboard/jobs/new")
        await asyncio.sleep(3)
        
        # CL-10: Step 2 labeling
        try:
            content = await self.page.content()
            if 'Requirements' in content and ('Job Type' in content or 'Work Mode' in content):
                self.log('CL-10', 'OPEN', 'Step 2 says Requirements but shows Job Details', 
                    'Step 2 label misleading - should be Job Details not Requirements')
            else:
                self.log('CL-10', 'FIXED', 'Step labels match content', 'Wizard steps correctly labeled')
        except Exception as e:
            self.log('CL-10', 'ERROR', str(e), 'Error checking step labels')
            
        # CL-11: Seniority Level disappears
        try:
            # Try to open Work Mode dropdown
            await self.page.click('text=/Work Mode/i')
            await asyncio.sleep(1)
            content = await self.page.content()
            if 'Seniority Level' in content:
                self.log('CL-11', 'FIXED', 'Seniority Level visible', 'Field stays visible when dropdown opens')
            else:
                self.log('CL-11', 'OPEN', 'Seniority Level hidden', 'Field disappears when Work Mode dropdown opens')
        except Exception as e:
            self.log('CL-11', 'ERROR', str(e), 'Error checking Seniority Level')
            
        # CL-12: Location field missing from Step 3
        try:
            # Navigate to Step 3
            await self.page.fill('input[name="title"]', 'Test Job')
            await self.page.click('button:has-text("Next")')
            await asyncio.sleep(2)
            await self.page.click('button:has-text("Next")')
            await asyncio.sleep(2)
            
            content = await self.page.content()
            if 'Location' in content or 'City' in content or 'Country' in content:
                self.log('CL-12', 'FIXED', 'Location field present', 'Step 3 has location field')
            else:
                self.log('CL-12', 'OPEN', 'No Location field', 'Step 3 missing location field despite label')
        except Exception as e:
            self.log('CL-12', 'ERROR', str(e), 'Error checking location field')
            
        # CL-13: Engagement Length options
        try:
            content = await self.page.content()
            if 'Short Term' in content and 'Long Term' in content:
                if '3 months' not in content and '6 months' not in content:
                    self.log('CL-13', 'OPEN', 'Only Short/Long Term options', 
                        'Engagement Length too vague - needs specific durations')
                else:
                    self.log('CL-13', 'FIXED', 'Specific duration options', 'Engagement Length has detailed options')
            else:
                self.log('CL-13', 'NOT_FOUND', 'Engagement Length not found', 'Could not locate field')
        except Exception as e:
            self.log('CL-13', 'ERROR', str(e), 'Error checking engagement length')
            
        await self.page.close()
        self.print_progress("Job Creation Wizard")
        
    # ==================== INTERVIEWS & CANDIDATES ====================
    
    async def test_interviews_candidates(self):
        """Test interviews and candidates bugs"""
        print("\n" + "="*80)
        print("INTERVIEWS & CANDIDATES TESTS")
        print("="*80)
        
        self.page = await self.context.new_page()
        await self.page.goto(f"{BASE_URL}/login")
        await self.page.fill('input[type="email"]', CREDENTIALS['client']['email'])
        await self.page.fill('input[type="password"]', CREDENTIALS['client']['password'])
        await self.page.click('button:has-text("Sign in")')
        await asyncio.sleep(3)
        
        # CL-28: Checklist and Date columns
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/interviews")
            await asyncio.sleep(3)
            content = await self.page.content()
            
            checklist_empty = '—' in content or 'N/A' in content or content.count('—') > 3
            if checklist_empty:
                self.log('CL-28', 'OPEN', 'Columns show — or empty', 'Checklist and Date columns not populated')
            else:
                self.log('CL-28', 'FIXED', 'Columns have data', 'Interview columns display correctly')
        except Exception as e:
            self.log('CL-28', 'ERROR', str(e), 'Error checking interview columns')
            
        # CL-30: Pagination
        try:
            content = await self.page.content()
            if 'Next' in content or 'Previous' in content or re.search(r'\\d+\\s*of\\s*\\d+', content):
                self.log('CL-30', 'FIXED', 'Pagination present', 'Interviews page has pagination')
            else:
                self.log('CL-30', 'OPEN', 'No pagination controls', 'All interviews shown on one page')
        except Exception as e:
            self.log('CL-30', 'ERROR', str(e), 'Error checking pagination')
            
        # CL-33: Interview detail dates
        try:
            # Click first interview if available
            interview_links = await self.page.query_selector_all('a[href*="/interviews/"]')
            if interview_links:
                await interview_links[0].click()
                await asyncio.sleep(2)
                content = await self.page.content()
                if '—' in content or 'Scheduled' in content:
                    dashes = content.count('—')
                    if dashes > 2:
                        self.log('CL-33', 'OPEN', f'{dashes} fields show —', 'Interview detail missing dates')
                    else:
                        self.log('CL-33', 'FIXED', 'Dates populated', 'Interview detail shows scheduled/completed dates')
        except Exception as e:
            self.log('CL-33', 'ERROR', str(e), 'Error checking interview dates')
            
        # CL-34: AI summary
        try:
            content = await self.page.content()
            if 'No AI summary available' in content:
                self.log('CL-34', 'OPEN', 'No AI summary message', 'AI summary not generated for completed interview')
            else:
                self.log('CL-34', 'FIXED', 'AI summary present', 'Interview has AI summary')
        except Exception as e:
            self.log('CL-34', 'ERROR', str(e), 'Error checking AI summary')
            
        # CL-36: Analytics 0%
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/analytics")
            await asyncio.sleep(3)
            content = await self.page.content()
            zeros = content.count('0%') + content.count('0 ')
            if zeros > 5:
                self.log('CL-36', 'OPEN', f'{zeros} zero values', 'Analytics shows 0% for all metrics')
            else:
                self.log('CL-36', 'FIXED', 'Analytics have values', 'Dashboard shows real metrics')
        except Exception as e:
            self.log('CL-36', 'ERROR', str(e), 'Error checking analytics')
            
        await self.page.close()
        self.print_progress("Interviews & Candidates")
        
    # ==================== ADMIN PANEL ====================
    
    async def test_admin_panel(self):
        """Test admin panel bugs"""
        print("\n" + "="*80)
        print("ADMIN PANEL TESTS")
        print("="*80)
        
        self.page = await self.context.new_page()
        await self.page.goto(f"{BASE_URL}/login")
        await self.page.fill('input[type="email"]', CREDENTIALS['admin']['email'])
        await self.page.fill('input[type="password"]', CREDENTIALS['admin']['password'])
        await self.page.click('button:has-text("Sign in")')
        await asyncio.sleep(3)
        
        # AD-02: Getting Started checklist
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/admin")
            await asyncio.sleep(3)
            content = await self.page.content()
            if '0 of 4' in content or '0 of' in content:
                self.log('AD-02', 'OPEN', 'Shows 0 of 4 completed', 'Getting Started checklist not tracking progress')
            else:
                self.log('AD-02', 'FIXED', 'Checklist shows progress', 'Getting Started tracks completion')
        except Exception as e:
            self.log('AD-02', 'ERROR', str(e), 'Error checking checklist')
            
        # AD-04: Active Jobs count
        try:
            content = await self.page.content()
            jobs_match = re.search(r'Active Jobs.*?([0-9]+)', content)
            interviews_match = re.search(r'Interviews.*?([0-9]+)', content)
            jobs = int(jobs_match.group(1)) if jobs_match else 0
            interviews = int(interviews_match.group(1)) if interviews_match else 0
            
            if jobs == 0 and interviews > 0:
                self.log('AD-04', 'OPEN', f'Jobs: {jobs}, Interviews: {interviews}', 
                    'Admin shows 0 jobs despite platform having active jobs')
            else:
                self.log('AD-04', 'FIXED', f'Jobs: {jobs}', 'Admin panel shows correct job count')
        except Exception as e:
            self.log('AD-04', 'ERROR', str(e), 'Error checking job count')
            
        # AD-11: Admin Jobs page
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/admin/jobs")
            await asyncio.sleep(3)
            content = await self.page.content()
            if '0 jobs' in content or 'No jobs' in content:
                self.log('AD-11', 'OPEN', 'Shows 0 jobs', 'Admin Jobs page shows 0 despite platform activity')
            else:
                self.log('AD-11', 'FIXED', 'Jobs displayed', 'Admin Jobs page shows actual jobs')
        except Exception as e:
            self.log('AD-11', 'ERROR', str(e), 'Error checking admin jobs')
            
        # AD-13: Admin Interviews
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/admin/interviews")
            await asyncio.sleep(3)
            content = await self.page.content()
            if 'No interviews' in content or '0 interviews' in content:
                self.log('AD-13', 'OPEN', 'No interviews message', 'Admin Interviews empty despite platform activity')
            else:
                self.log('AD-13', 'FIXED', 'Interviews displayed', 'Admin Interviews shows data')
        except Exception as e:
            self.log('AD-13', 'ERROR', str(e), 'Error checking admin interviews')
            
        # AD-15: Analytics loading
        try:
            await self.page.goto(f"{BASE_URL}/dashboard/admin/analytics")
            await asyncio.sleep(5)
            content = await self.page.content()
            if 'skeleton' in content.lower() or 'loading' in content.lower():
                self.log('AD-15', 'OPEN', 'Still loading', 'Admin Analytics stuck in skeleton state')
            else:
                self.log('AD-15', 'FIXED', 'Analytics loaded', 'Admin Analytics displays content')
        except Exception as e:
            self.log('AD-15', 'ERROR', str(e), 'Error checking analytics')
            
        await self.page.close()
        self.print_progress("Admin Panel")
        
    # ==================== MAIN EXECUTION ====================
    
    async def run_all_tests(self):
        print("\n" + "🚀"*40)
        print("FALCON EXTENDED BUG TESTING")
        print("Started:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("🚀"*40)
        
        await self.setup()
        
        try:
            await self.test_client_dashboard_extended()
            await self.test_job_creation_wizard()
            await self.test_interviews_candidates()
            await self.test_admin_panel()
        finally:
            await self.teardown()
            
        await self.save_results()
        
        # Final Summary
        print("\n" + "="*80)
        print("EXTENDED BUG TESTING - FINAL SUMMARY")
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
    uat = ExtendedBugUAT()
    asyncio.run(uat.run_all_tests())
