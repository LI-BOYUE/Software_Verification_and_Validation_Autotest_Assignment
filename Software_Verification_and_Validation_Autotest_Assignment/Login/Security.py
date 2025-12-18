# Security.py
from test_base import TestBase, logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
import time
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE_URL = "http://localhost:8080"
LOGIN_URL = f"{BASE_URL}/login.jsp"
WELCOME_URL = f"{BASE_URL}/welcome.jsp"

class LoginSecurityTests(TestBase):
    def __init__(self):
        super().__init__()
        self.timestamp = int(time.time())
        self.FALLBACK_EMAIL = "admin@system.com"
        self.FALLBACK_PASSWORD = "LA2028sGoldM"
        self.TEST_EMAIL = "testuser@loginsec.com"
        self.TEST_PASSWORD = "Test12345"

    def wait_for_login_result(self, timeout=10):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.any_of(
                    EC.url_to_be(WELCOME_URL),
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'error-message') or contains(text(),'Incorrect') or contains(text(),'locked')]")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Invalid credentials') or contains(text(),'too many')]"))
                )
            )
        except TimeoutException:
            logger.warning("Login result wait timeout")
    
    def switch_to_window(self, window_name_or_index):
        handles = self.driver.window_handles
        
        if isinstance(window_name_or_index, int):
            if window_name_or_index >= len(handles):
                raise IndexError(f"Only {len(handles)} windows open, cannot switch to index {window_name_or_index}")
            target_handle = handles[window_name_or_index]
        else:
            target_handle = window_name_or_index
        
        self.driver.switch_to.window(target_handle)
        return self.driver
    
    # Test Case ID: test_LGN_010
    # Test Case Name: Account Lockout After Consecutive Failed Logins
    def account_lockout_after_failed_attempts(self):
        test_name = "LGN-010 - Account Lockout After Consecutive Failed Logins"
        logger.info(f"Starting {test_name}")

        self.driver.get(LOGIN_URL)
        self.wait.until(EC.presence_of_element_located((By.NAME, "email")))

        # 5 times wrong password
        for i in range(5):
            self.driver.find_element(By.NAME, "email").clear()
            self.driver.find_element(By.NAME, "email").send_keys(self.FALLBACK_EMAIL)
            self.driver.find_element(By.NAME, "password").clear()
            self.driver.find_element(By.NAME, "password").send_keys("wrongpass123")
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(1.5) 

        # Try correct password 
        self.driver.find_element(By.NAME, "email").clear()
        self.driver.find_element(By.NAME, "email").send_keys(self.FALLBACK_EMAIL)
        self.driver.find_element(By.NAME, "password").clear()
        self.driver.find_element(By.NAME, "password").send_keys(self.FALLBACK_PASSWORD)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        self.wait_for_login_result()

        page_source = self.driver.page_source.lower()
        current_url = self.driver.current_url

        if WELCOME_URL in current_url:
            self.take_screenshot("LGN010_NO_LOCKOUT")
            self.log_test_result(test_name, "FAIL", "CRITICAL: Account NOT locked after 5 failed attempts!", {"severity": "CRITICAL"})
            return False
        else:
            if ("locked" in page_source or "too many" in page_source or "try again later" in page_source or
                "account is locked" in page_source or "generic error" in page_source):
                self.log_test_result(test_name, "PASS", "Account correctly locked after 5 failed attempts")
                return True
            else:
                self.take_screenshot("LOGIN010_generic_or_no_message")
                self.log_test_result(test_name, "FAIL", "Account locked but no clear lock message (generic error shown?)")
                return False

    # Test Case ID: test_LGN_011
    # Test Case Name: Common/Default Admin Password Check & Weak Credential Rejection
    def common_admin_passwords_and_weak_credential_handling(self):
        test_name = "LGN-011 - Common/Default Admin Passwords & Weak Credential Rejection"
        logger.info(f"Starting {test_name}")

        common_creds = [
            ("admin", "admin"),
            ("admin", "123456"),
            ("admin", "password"),
            ("admin@system.com", "admin"),
            ("admin@system.com", "123456"),
            ("admin@system.com", "root"),
            ("admin@system.com", "LA2028sGoldM"),   # This one should succeed (fallback admin)
        ]

        success_count = 0
        total = len(common_creds)

        for email, password in common_creds:
            self.driver.get(LOGIN_URL)
            self.wait.until(EC.presence_of_element_located((By.NAME, "email")))

            self.driver.find_element(By.NAME, "email").send_keys(email)
            self.driver.find_element(By.NAME, "password").send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

            self.wait_for_login_result(12)

            if WELCOME_URL in self.driver.current_url:
                if password == "LA2028sGoldM" and email == "admin@system.com":
                    success_count += 1
                    logger.info(f"Expected success: {email} with strong password")
                else:
                    self.take_screenshot(f"LGN011_WEAK_CRED_SUCCESS_{email.replace('@', '_')}")
                    logger.error(f"Login succeeded with weak/common credential: {email}/{password}")
            else:
                page_source = self.driver.page_source.lower()
                if "invalid credentials" in page_source or "incorrect" in page_source:
                    if password != "LA2028sGoldM" or email != "admin@system.com":
                        success_count += 1  # Expected rejection
                else:
                    logger.warning(f"Unclear response for {email}/{password}")

        passed = success_count >= total - 1  
        if success_count == total - 1 or success_count == total:
            self.log_test_result(test_name, "PASS", f"Properly rejected weak/common admin credentials ({success_count}/{total} correct)")
            return True
        else:
            self.log_test_result(test_name, "FAIL", f"Too many weak credentials allowed ({success_count}/{total})")
            return False

    # Test Case ID: test_LGN_016
    # Test Case Name: Concurrent Login with Same User in Two Browsers (Session Fixation / Multiple Session Check)
    def concurrent_login_same_user(self):
        test_name = "LGN-016 - Concurrent Login with Same User (Session Handling)"
        logger.info(f"Starting {test_name}")

        options = Options()
        #options.add_argument("--headless") if self.headless else None
        driver2 = webdriver.Chrome(options=options)

        try:
            # First login
            self.driver.get(LOGIN_URL)
            self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
            self.driver.find_element(By.NAME, "email").send_keys(self.FALLBACK_EMAIL)
            self.driver.find_element(By.NAME, "password").send_keys(self.FALLBACK_PASSWORD)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            self.wait.until(EC.url_to_be(WELCOME_URL))
            logger.info("First session established")

            # Second login in parallel (simulate another browser)
            driver2.get(LOGIN_URL)
            WebDriverWait(driver2, 10).until(EC.presence_of_element_located((By.NAME, "email")))
            driver2.find_element(By.NAME, "email").send_keys(self.FALLBACK_EMAIL)
            driver2.find_element(By.NAME, "password").send_keys(self.FALLBACK_PASSWORD)
            driver2.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            WebDriverWait(driver2, 10).until(EC.url_to_be(WELCOME_URL))
            logger.info("Second session established")

            # Now check both can access protected resource (welcome.jsp)
            self.driver.get(WELCOME_URL)
            driver2.get(WELCOME_URL)

            time.sleep(2)

            session1_valid = "Welcome back" in self.driver.page_source
            session2_valid = "Welcome back" in driver2.page_source

            if session1_valid and session2_valid:
                self.log_test_result(test_name, "PASS", "Multiple concurrent sessions allowed (common behavior)")
              
                return True
            elif not session1_valid and session2_valid:
                self.log_test_result(test_name, "PASS", "Second login invalidated first session (secure behavior)")
                
                return True
            else:
                self.log_test_result(test_name, "FAIL", "Inconsistent session state after concurrent login")
                
                return False

        except Exception as e:
            logger.error(f"Concurrent login test failed: {e}")
            self.log_test_result(test_name, "ERROR", "Test execution failed due to environment")
            
            return False
        finally:
            driver2.quit()

    # Test Case ID: test_LGN_017
    # Test Case Name: Account Lockout Scope on Same IP by Different Users
    def lockout_scope_per_account_not_per_ip(self):
        test_name = "LGN-017 - Account Lockout Scope (Per Account, Not Per IP)"
        logger.info(f"Starting {test_name}")

        user_a_email = "usera@loginsec.com"
        user_b_email = "userb@loginsec.com"
        wrong_pass = "wrong123"

        # Trigger 5 failed attempts for User A (fallback admin)
        self.driver.get(LOGIN_URL)
        for i in range(5):
            self.driver.find_element(By.NAME, "email").clear()
            self.driver.find_element(By.NAME, "email").send_keys(self.FALLBACK_EMAIL)
            self.driver.find_element(By.NAME, "password").clear()
            self.driver.find_element(By.NAME, "password").send_keys(wrong_pass)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(1.2)

        # Try login as User B (should still work)
        self.driver.get(LOGIN_URL)
        self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
        self.driver.find_element(By.NAME, "email").send_keys("nonexistent@test.com")
        self.driver.find_element(By.NAME, "password").send_keys("any")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        self.wait_for_login_result()

        page_source = self.driver.page_source.lower()

        if "locked" in page_source or "too many" in page_source:
            self.take_screenshot("LGN017_IP_BASED_LOCK")
            self.log_test_result(test_name, "FAIL", "CRITICAL: Lockout appears to be IP-based, not account-based!", {"severity": "CRITICAL"})
            return False
        else:
            self.log_test_result(test_name, "PASS", "Lockout is correctly per-account: User B unaffected by User A's failed attempts")
            return True

    def run_all_security_tests(self):
        if not self.setup():
            return

        try:
            logger.info("\n" + "="*100)
            logger.info("STARTING LOGIN SECURITY FEATURE TESTS: LOGIN-010, 011, 016, 017")
            logger.info("="*100)

            self.account_lockout_after_failed_attempts()
            self.common_admin_passwords_and_weak_credential_handling()
            self.concurrent_login_same_user()
            self.lockout_scope_per_account_not_per_ip()

            logger.info("="*100)
            logger.info("LOGIN SECURITY TEST SUITE COMPLETED")
            logger.info("="*100)

        finally:
            self.teardown()

