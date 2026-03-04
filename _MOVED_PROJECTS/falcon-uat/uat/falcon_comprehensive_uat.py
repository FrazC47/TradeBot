#!/usr/bin/env python3
"""
Falcon Platform Comprehensive UAT Testing with Playwright
Tests: Functionality, UI/UX, Copywriting, Best Practices
Status: PASS (working), FAIL (not working), IMPROVE (working but can be better)
"""

import asyncio
import csv
import re
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "https://falcon.up.railway.app"
RESULTS_FILE = "/root/.openclaw/workspace/projects/falcon/uat/comprehensive_uat_results.csv"

CREDENTIALS = {
    "client": {"email": "ahmed.hassan@techcorp.ae", "password": "SecurePass123!"},
    "admin": {"email": "admin@example.com", "password": "admin123"},
    "candidate": {"email": "interviewee@example.com", "password": "interviewee123"}
}

class ComprehensiveUAT:
    def __init__(self):
        self.results = []
        self.browser = None
        self.context = None
        self.page = None
        
    async def setup(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True, args=['--no-sandbox', '--disable-gpu']
        )
        self.context = await self.browser.new_context(viewport={'width': 1280, 'height': 720})
        
    async def teardown(self):
        if self.context: await self.context.close()
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
            
    def log(self, test_id, role, category, module, test_name, expected, actual, status, severity="Medium", notes=""):
        """Log test result with detailed categorization"""
        self.results.append({
            'test_id': test_id, 'role': role, 'category': category, 'module': module,
            'test_name': test_name, 'expected': expected, 'actual': actual,
            'status': status, 'severity': severity, 'notes': notes,
            'timestamp': datetime.now().isoformat()
        })
        icons = {'PASS': '✅', 'FAIL': '🔴', 'IMPROVE': '💡'}
        print(f"{icons.get(status, '❓')} [{status}] {test_id}: {test_name}")
        
    async def save_results(self):
        with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'test_id', 'role', 'category', 'module', 'test_name', 'expected',
                'actual', 'status', 'severity', 'notes', 'timestamp'
            ])
            writer.writeheader()
            writer.writerows(self.results)
        print(f"\n📊 Results saved to: {RESULTS_FILE}")
        
    # ==================== LANDING PAGE TESTS ====================
    
    async def test_landing_page(self):
        print("\n" + "="*80)
        print("LANDING PAGE - FUNCTIONALITY & UI/UX TESTS")
        print("="*80)
        
        self.page = await self.context.new_page()
        await self.page.goto(BASE_URL)
        await self.page.wait_for_load_state('networkidle')
        
        # FUNCTIONALITY TESTS
        # LP-01: Start Free Trial
        try:
            await self.page.click('button:has-text("Start Free Trial")')
            await asyncio.sleep(2)
            url = self.page.url
            if '/login' in url:
                self.log('LP-01', 'Anonymous', 'Functionality', 'Landing Page',
                    'Start Free Trial CTA', 'Registration page', f'Login page ({url})',
                    'FAIL', 'High', 'Critical flow broken - new users see login instead of signup')
            else:
                self.log('LP-01', 'Anonymous', 'Functionality', 'Landing Page',
                    'Start Free Trial CTA', 'Registration page', url, 'PASS')
        except Exception as e:
            self.log('LP-01', 'Anonymous', 'Functionality', 'Landing Page',
                'Start Free Trial CTA', 'Registration page', str(e), 'FAIL', 'High')
                
        await self.page.goto(BASE_URL)
        await self.page.wait_for_load_state('networkidle')
        
        # LP-04: Watch Demo
        try:
            await self.page.click('button:has-text("Watch Demo")')
            await asyncio.sleep(2)
            url = self.page.url
            if '/login' in url:
                self.log('LP-04', 'Anonymous', 'Functionality', 'Landing Page',
                    'Watch Demo button', 'Demo video/modal', 'Login page',
                    'FAIL', 'Medium', 'Demo button has no actual demo functionality')
            else:
                self.log('LP-04', 'Anonymous', 'Functionality', 'Landing Page',
                    'Watch Demo button', 'Demo video/modal', url, 'PASS')
        except Exception as e:
            self.log('LP-04', 'Anonymous', 'Functionality', 'Landing Page',
                'Watch Demo button', 'Demo video/modal', str(e), 'FAIL', 'Medium')
                
        await self.page.goto(BASE_URL)
        await self.page.wait_for_load_state('networkidle')
        
        # LP-05: See it in action links
        try:
            links = await self.page.query_selector_all('button:has-text("See it in action")')
            if links:
                await links[0].click()
                await asyncio.sleep(2)
                url = self.page.url
                if '/login' in url or url == BASE_URL:
                    self.log('LP-05', 'Anonymous', 'Functionality', 'Landing Page',
                        'See it in action links', 'Feature demo pages', 'No navigation or login',
                        'FAIL', 'Medium', 'All 4 solution cards have non-functional links')
                else:
                    self.log('LP-05', 'Anonymous', 'Functionality', 'Landing Page',
                        'See it in action links', 'Feature demo pages', url, 'PASS')
        except Exception as e:
            self.log('LP-05', 'Anonymous', 'Functionality', 'Landing Page',
                'See it in action links', 'Feature demo pages', str(e), 'FAIL', 'Medium')
                
        await self.page.goto(BASE_URL)
        await self.page.wait_for_load_state('networkidle')
        
        # LP-07: Request Demo
        try:
            await self.page.click('button:has-text("Request Demo")')
            await asyncio.sleep(2)
            url = self.page.url
            if '/login' in url:
                self.log('LP-07', 'Anonymous', 'Functionality', 'Landing Page',
                    'Request Demo button', 'Demo request form', 'Login page',
                    'FAIL', 'Medium', 'No demo request functionality')
            else:
                self.log('LP-07', 'Anonymous', 'Functionality', 'Landing Page',
                    'Request Demo button', 'Demo request form', url, 'PASS')
        except Exception as e:
            self.log('LP-07', 'Anonymous', 'Functionality', 'Landing Page',
                'Request Demo button', 'Demo request form', str(e), 'FAIL', 'Medium')
        
        # UI/UX TESTS
        await self.page.goto(BASE_URL)
        await self.page.wait_for_load_state('networkidle')
        
        # LP-02: Favicon
        try:
            favicon = await self.page.query_selector('link[rel="icon"]')
            if favicon:
                href = await favicon.get_attribute('href')
                self.log('LP-02', 'Anonymous', 'UI/UX', 'Landing Page',
                    'Favicon present', 'Favicon loaded', f'Favicon: {href}', 'PASS')
            else:
                self.log('LP-02', 'Anonymous', 'UI/UX', 'Landing Page',
                    'Favicon present', 'Favicon loaded', 'Not found',
                    'FAIL', 'Low', 'Missing favicon affects brand perception')
        except Exception as e:
            self.log('LP-02', 'Anonymous', 'UI/UX', 'Landing Page',
                'Favicon present', 'Favicon loaded', str(e), 'FAIL', 'Low')
        
        # LP-03: Stats emoji
        try:
            content = await self.page.content()
            if '□' in content or '&#9633;' in content:
                self.log('LP-03', 'Anonymous', 'UI/UX', 'Landing Page',
                    'Stats bar emoji rendering', 'Proper emoji icons', 'Broken emoji character',
                    'FAIL', 'Low', 'Shows broken box character instead of emoji')
            else:
                self.log('LP-03', 'Anonymous', 'UI/UX', 'Landing Page',
                    'Stats bar emoji rendering', 'Proper emoji icons', 'Emojis render correctly', 'PASS')
        except Exception as e:
            self.log('LP-03', 'Anonymous', 'UI/UX', 'Landing Page',
                'Stats bar emoji rendering', 'Proper emoji icons', str(e), 'FAIL', 'Low')
        
        # LP-06: Testimonials
        try:
            testimonials = await self.page.query_selector_all('text=/HR Director|Talent Acquisition|VP of Engineering|Recruitment Manager/i')
            avatars = await self.page.query_selector_all('text=/^[H|T|V|R]$/')
            if len(avatars) >= 4:
                self.log('LP-06', 'Anonymous', 'UI/UX', 'Landing Page',
                    'Testimonial avatars', 'Real photos or full names', 'Single-letter placeholders (H, T, V, R)',
                    'FAIL', 'Medium', 'Anonymous avatars reduce credibility - should use real photos/names')
            else:
                self.log('LP-06', 'Anonymous', 'UI/UX', 'Landing Page',
                    'Testimonial avatars', 'Real photos or full names', 'Proper avatars found', 'PASS')
        except Exception as e:
            self.log('LP-06', 'Anonymous', 'UI/UX', 'Landing Page',
                'Testimonial avatars', 'Real photos or full names', str(e), 'FAIL', 'Medium')
        
        # COPYWRITING TESTS
        # Check for placeholder text
        content = await self.page.content()
        placeholders = ['asdf', 'lorem ipsum', 'placeholder', 'test@test.com']
        found_placeholders = [p for p in placeholders if p.lower() in content.lower()]
        if found_placeholders:
            self.log('COPY-01', 'Anonymous', 'Copywriting', 'Landing Page',
                'No placeholder text', 'Professional copy', f'Found: {found_placeholders}',
                'FAIL', 'High', 'Placeholder text visible to users')
        else:
            self.log('COPY-01', 'Anonymous', 'Copywriting', 'Landing Page',
                'No placeholder text', 'Professional copy', 'No placeholders found', 'PASS')
        
        # Check for consistent branding
        brand_mentions = content.lower().count('falcon')
        if brand_mentions < 3:
            self.log('COPY-02', 'Anonymous', 'Copywriting', 'Landing Page',
                'Brand consistency', 'Falcon mentioned throughout', f'Only {brand_mentions} mentions',
                'IMPROVE', 'Low', 'Could strengthen brand presence')
        else:
            self.log('COPY-02', 'Anonymous', 'Copywriting', 'Landing Page',
                'Brand consistency', 'Falcon mentioned throughout', f'{brand_mentions} mentions', 'PASS')
        
        await self.page.close()
        
    # ==================== CLIENT DASHBOARD TESTS ====================
    
    async def test_client_dashboard(self):
        print("\n" + "="*80)
        print("CLIENT DASHBOARD - FUNCTIONALITY & UI/UX TESTS")
        print("="*80)
        
        self.page = await self.context.new_page()
        
        # Login
        await self.page.goto(f"{BASE_URL}/login")
        await self.page.fill('input[type="email"]', CREDENTIALS['client']['email'])
        await self.page.fill('input[type="password"]', CREDENTIALS['client']['password'])
        await self.page.click('button:has-text("Sign in")')
        await asyncio.sleep(3)
        
        # AUTH-CLIENT: Login success
        if '/dashboard' in self.page.url:
            self.log('AUTH-CLIENT', 'Client', 'Functionality', 'Authentication',
                'Login with valid credentials', 'Dashboard access', f'URL: {self.page.url}', 'PASS')
        else:
            self.log('AUTH-CLIENT', 'Client', 'Functionality', 'Authentication',
                'Login with valid credentials', 'Dashboard access', f'URL: {self.page.url}',
                'FAIL', 'Critical', 'Cannot access dashboard')
            await self.page.close()
            return
            
        # CL-DASH-01: Welcome message
        try:
            welcome = await self.page.inner_text('text=/Welcome back/i')
            if 'Ahmed' in welcome:
                self.log('CL-DASH-01', 'Client', 'UI/UX', 'Dashboard',
                    'Personalized welcome message', 'Welcome back, [Name]!', welcome, 'PASS')
            else:
                self.log('CL-DASH-01', 'Client', 'UI/UX', 'Dashboard',
                    'Personalized welcome message', 'Welcome back, [Name]!', welcome,
                    'IMPROVE', 'Low', 'Could be more personalized')
        except:
            self.log('CL-DASH-01', 'Client', 'UI/UX', 'Dashboard',
                'Personalized welcome message', 'Welcome back, [Name]!', 'Not found',
                'FAIL', 'Low')
        
        # CL-01: Candidates stat vs Interviews
        try:
            stats_text = await self.page.content()
            candidates_match = re.search(r'Candidates.*?([0-9]+)', stats_text)
            interviews_match = re.search(r'Interviews.*?([0-9]+)', stats_text)
            
            candidates = int(candidates_match.group(1)) if candidates_match else 0
            interviews = int(interviews_match.group(1)) if interviews_match else 0
            
            if candidates == 0 and interviews > 0:
                self.log('CL-01', 'Client', 'Functionality', 'Dashboard',
                    'Candidates stat matches interviews', f'Candidates: {candidates}, Interviews: {interviews}',
                    f'0 candidates with {interviews} interviews',
                    'FAIL', 'High', 'Logical inconsistency - interviews require candidates')
            else:
                self.log('CL-01', 'Client', 'Functionality', 'Dashboard',
                    'Candidates stat matches interviews', f'Candidates: {candidates}, Interviews: {interviews}',
                    f'Candidates: {candidates}, Interviews: {interviews}', 'PASS')
        except Exception as e:
            self.log('CL-01', 'Client', 'Functionality', 'Dashboard',
                'Candidates stat matches interviews', 'Consistent data', str(e), 'FAIL', 'High')
        
        # CL-50: Statistics "of 0 total"
        try:
            stats = await self.page.inner_text('text=/of 0 total/i')
            self.log('CL-50', 'Client', 'Functionality', 'Dashboard',
                'Statistics show actual counts', 'Real data from system', 'Shows "of 0 total"',
                'FAIL', 'High', 'Data not loading - shows 0 for all stats')
        except:
            self.log('CL-50', 'Client', 'Functionality', 'Dashboard',
                'Statistics show actual counts', 'Real data from system', 'Stats loaded', 'PASS')
        
        # UI/UX: Quick Actions visibility
        try:
            quick_actions = await self.page.query_selector_all('text=/Create Job|View Candidates|Schedule Interview/i')
            if len(quick_actions) >= 3:
                self.log('CL-UI-01', 'Client', 'UI/UX', 'Dashboard',
                    'Quick Actions visible', 'All 3 actions present', f'{len(quick_actions)} actions found', 'PASS')
            else:
                self.log('CL-UI-01', 'Client', 'UI/UX', 'Dashboard',
                    'Quick Actions visible', 'All 3 actions present', f'Only {len(quick_actions)} found',
                    'FAIL', 'Medium')
        except Exception as e:
            self.log('CL-UI-01', 'Client', 'UI/UX', 'Dashboard',
                'Quick Actions visible', 'All 3 actions present', str(e), 'FAIL', 'Medium')
        
        # CL-02: Create Job navigation
        try:
            await self.page.click('text=/Create Job/i')
            await asyncio.sleep(2)
            url = self.page.url
            if '/jobs/new' in url or 'create' in url.lower():
                self.log('CL-02', 'Client', 'Functionality', 'Dashboard',
                    'Create Job navigates to job creation', 'Job creation form', url, 'PASS')
            else:
                self.log('CL-02', 'Client', 'Functionality', 'Dashboard',
                    'Create Job navigates to job creation', 'Job creation form', f'Stayed on {url}',
                    'FAIL', 'High', 'Quick action does not navigate properly')
        except Exception as e:
            self.log('CL-02', 'Client', 'Functionality', 'Dashboard',
                'Create Job navigates to job creation', 'Job creation form', str(e), 'FAIL', 'High')
        
        await self.page.close()
        
    # ==================== MAIN EXECUTION ====================
    
    async def run_all_tests(self):
        print("\n" + "🚀"*40)
        print("FALCON PLATFORM COMPREHENSIVE UAT")
        print("Testing: Functionality | UI/UX | Copywriting | Best Practices")
        print("Started:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("🚀"*40)
        
        await self.setup()
        
        try:
            await self.test_landing_page()
            await self.test_client_dashboard()
            
        finally:
            await self.teardown()
            
        await self.save_results()
        
        # Summary
        print("\n" + "="*80)
        print("COMPREHENSIVE UAT SUMMARY")
        print("="*80)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        improve = sum(1 for r in self.results if r['status'] == 'IMPROVE')
        
        print(f"Total Tests: {total}")
        print(f"✅ PASS (Working): {passed}")
        print(f"🔴 FAIL (Not Working): {failed}")
        print(f"💡 IMPROVE (Can be better): {improve}")
        
        # By category
        print("\nBy Category:")
        categories = {}
        for r in self.results:
            cat = r['category']
            categories[cat] = categories.get(cat, {'total': 0, 'pass': 0, 'fail': 0, 'improve': 0})
            categories[cat]['total'] += 1
            categories[cat][r['status'].lower()] += 1
            
        for cat, stats in categories.items():
            print(f"  {cat}: {stats['pass']}✅ {stats['fail']}🔴 {stats['improve']}💡 (Total: {stats['total']})")
        
        print(f"\n📊 Detailed results: {RESULTS_FILE}")

if __name__ == "__main__":
    uat = ComprehensiveUAT()
    asyncio.run(uat.run_all_tests())
