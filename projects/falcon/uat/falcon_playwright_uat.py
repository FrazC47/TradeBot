#!/usr/bin/env python3
"""
Falcon Platform UAT Testing with Playwright
Comprehensive test suite for all user roles
"""

import asyncio
import csv
import json
from datetime import datetime
from playwright.async_api import async_playwright, expect

# Configuration
BASE_URL = "https://falcon.up.railway.app"
RESULTS_FILE = "/root/.openclaw/workspace/projects/falcon/uat/playwright_uat_results.csv"

# Credentials
CREDENTIALS = {
    "client": {
        "email": "ahmed.hassan@techcorp.ae",
        "password": "SecurePass123!"
    },
    "admin": {
        "email": "admin@example.com",
        "password": "admin123"
    },
    "candidate": {
        "email": "interviewee@example.com",
        "password": "interviewee123"
    }
}

class FalconUAT:
    def __init__(self):
        self.results = []
        self.browser = None
        self.context = None
        
    async def setup(self):
        """Initialize browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-gpu']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        
    async def teardown(self):
        """Clean up browser"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
    def log_result(self, test_id, role, module, scenario, expected, actual, status, notes=""):
        """Log test result"""
        self.results.append({
            'test_id': test_id,
            'role': role,
            'module': module,
            'scenario': scenario,
            'expected': expected,
            'actual': actual,
            'status': status,
            'notes': notes,
            'timestamp': datetime.now().isoformat()
        })
        status_icon = "✅" if status == "PASS" else "🔴" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_id}: {scenario} - {status}")
        
    async def save_results(self):
        """Save results to CSV"""
        with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'test_id', 'role', 'module', 'scenario', 'expected', 
                'actual', 'status', 'notes', 'timestamp'
            ])
            writer.writeheader()
            writer.writerows(self.results)
        print(f"\n📊 Results saved to: {RESULTS_FILE}")
        
    # ==================== LANDING PAGE TESTS ====================
    
    async def test_landing_page(self):
        """Test landing page bugs"""
        print("\n" + "="*80)
        print("PHASE 1: LANDING PAGE TESTS")
        print("="*80)
        
        page = await self.context.new_page()
        
        # Navigate to landing page
        await page.goto(BASE_URL)
        await page.wait_for_load_state('networkidle')
        
        # LP-01: Start Free Trial CTA
        try:
            await page.click('button:has-text("Start Free Trial")')
            await asyncio.sleep(2)
            url = page.url
            if '/login' in url:
                self.log_result(
                    'LP-01', 'Anonymous', 'Landing Page',
                    '"Start Free Trial" CTA redirects to Login instead of Registration',
                    'Navigate to registration/signup page',
                    f'Redirects to {url}',
                    'FAIL',
                    'Still goes to login page, not registration'
                )
            else:
                self.log_result('LP-01', 'Anonymous', 'Landing Page', 
                    '"Start Free Trial" CTA', 'Registration page', url, 'PASS')
        except Exception as e:
            self.log_result('LP-01', 'Anonymous', 'Landing Page', 
                '"Start Free Trial" CTA', 'Registration page', str(e), 'ERROR')
                
        await page.close()
        
    # ==================== CLIENT USER TESTS ====================
    
    async def test_client_login(self):
        """Test client user login"""
        print("\n" + "="*80)
        print("PHASE 2: CLIENT USER TESTS")
        print("="*80)
        
        page = await self.context.new_page()
        
        # Navigate to login
        await page.goto(f"{BASE_URL}/login")
        await page.wait_for_load_state('networkidle')
        
        try:
            # Fill credentials
            await page.fill('input[type="email"]', CREDENTIALS['client']['email'])
            await page.fill('input[type="password"]', CREDENTIALS['client']['password'])
            
            # Click sign in
            await page.click('button:has-text("Sign in")')
            await asyncio.sleep(3)
            
            # Check if logged in
            url = page.url
            if '/dashboard' in url:
                self.log_result(
                    'AUTH-CLIENT', 'Client', 'Authentication',
                    'Client user login',
                    'Successful login, dashboard access',
                    f'Logged in, URL: {url}',
                    'PASS'
                )
                
                # Check for welcome message
                try:
                    welcome = await page.inner_text('text=/Welcome back/i')
                    self.log_result(
                        'CL-DASH-01', 'Client', 'Dashboard',
                        'Dashboard welcome message',
                        'Welcome message displayed',
                        welcome,
                        'PASS'
                    )
                except:
                    self.log_result(
                        'CL-DASH-01', 'Client', 'Dashboard',
                        'Dashboard welcome message',
                        'Welcome message displayed',
                        'Not found',
                        'FAIL'
                    )
                    
                # Check statistics
                try:
                    stats = await page.inner_text('text=/of 0 total/i')
                    self.log_result(
                        'CL-50', 'Client', 'Dashboard',
                        'Statistics Overview shows "of 0 total"',
                        'Should show actual counts',
                        stats,
                        'FAIL',
                        'Bug CL-50 confirmed - shows 0 counts'
                    )
                except:
                    self.log_result(
                        'CL-50', 'Client', 'Dashboard',
                        'Statistics Overview',
                        'Should show actual counts',
                        'Stats loaded (may be fixed)',
                        'PASS'
                    )
                    
            else:
                self.log_result(
                    'AUTH-CLIENT', 'Client', 'Authentication',
                    'Client user login',
                    'Successful login',
                    f'Login failed, URL: {url}',
                    'FAIL'
                )
                
        except Exception as e:
            self.log_result('AUTH-CLIENT', 'Client', 'Authentication', 
                'Client user login', 'Successful login', str(e), 'ERROR')
            
        await page.close()
        return True
        
    # ==================== ADMIN USER TESTS ====================
    
    async def test_admin_login(self):
        """Test admin user login"""
        print("\n" + "="*80)
        print("PHASE 3: ADMIN USER TESTS")
        print("="*80)
        
        page = await self.context.new_page()
        
        await page.goto(f"{BASE_URL}/login")
        await page.wait_for_load_state('networkidle')
        
        try:
            await page.fill('input[type="email"]', CREDENTIALS['admin']['email'])
            await page.fill('input[type="password"]', CREDENTIALS['admin']['password'])
            await page.click('button:has-text("Sign in")')
            await asyncio.sleep(3)
            
            url = page.url
            if '/dashboard' in url or '/admin' in url:
                self.log_result(
                    'AUTH-ADMIN', 'Admin', 'Authentication',
                    'Admin user login',
                    'Successful login',
                    f'Logged in, URL: {url}',
                    'PASS'
                )
            else:
                self.log_result(
                    'AUTH-ADMIN', 'Admin', 'Authentication',
                    'Admin user login',
                    'Successful login',
                    f'Login result: {url}',
                    'FAIL'
                )
                
        except Exception as e:
            self.log_result('AUTH-ADMIN', 'Admin', 'Authentication',
                'Admin user login', 'Successful login', str(e), 'ERROR')
            
        await page.close()
        
    # ==================== CANDIDATE USER TESTS ====================
    
    async def test_candidate_login(self):
        """Test candidate user login"""
        print("\n" + "="*80)
        print("PHASE 4: CANDIDATE USER TESTS")
        print("="*80)
        
        page = await self.context.new_page()
        
        await page.goto(f"{BASE_URL}/login")
        await page.wait_for_load_state('networkidle')
        
        try:
            await page.fill('input[type="email"]', CREDENTIALS['candidate']['email'])
            await page.fill('input[type="password"]', CREDENTIALS['candidate']['password'])
            await page.click('button:has-text("Sign in")')
            await asyncio.sleep(3)
            
            url = page.url
            self.log_result(
                'AUTH-CANDIDATE', 'Candidate', 'Authentication',
                'Candidate user login',
                'Successful login',
                f'Result: {url}',
                'PASS' if '/dashboard' in url or '/candidate' in url else 'FAIL'
            )
            
        except Exception as e:
            self.log_result('AUTH-CANDIDATE', 'Candidate', 'Authentication',
                'Candidate user login', 'Successful login', str(e), 'ERROR')
            
        await page.close()
        
    # ==================== MAIN EXECUTION ====================
    
    async def run_all_tests(self):
        """Execute all UAT tests"""
        print("\n" + "🚀"*40)
        print("FALCON PLATFORM UAT TESTING")
        print("Started:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("🚀"*40)
        
        await self.setup()
        
        try:
            # Run tests
            await self.test_landing_page()
            await self.test_client_login()
            await self.test_admin_login()
            await self.test_candidate_login()
            
        finally:
            await self.teardown()
            
        # Save results
        await self.save_results()
        
        # Print summary
        print("\n" + "="*80)
        print("UAT TEST SUMMARY")
        print("="*80)
        total = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        errors = sum(1 for r in self.results if r['status'] == 'ERROR')
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"🔴 Failed: {failed}")
        print(f"⚠️ Errors: {errors}")
        print(f"\nResults saved to: {RESULTS_FILE}")


# Run the tests
if __name__ == "__main__":
    uat = FalconUAT()
    asyncio.run(uat.run_all_tests())
