# Basic_Authentication.py
from test_base import TestBase, logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
import time
from selenium.webdriver.common.keys import Keys

BASE_URL = "http://localhost:8080"
REGISTER_URL = f"{BASE_URL}/register.jsp"
LOGIN_URL = f"{BASE_URL}/login.jsp"
WELCOME_URL = f"{BASE_URL}/welcome.jsp"
RS_URL = "register=success"

class LoginValidationTests(TestBase):
    def __init__(self):
        super().__init__()
        self.timestamp = int(time.time())
        # self.register_test_user()   
        self.FALLBACK_EMAIL = "admin@system.com"          
        self.FALLBACK_PASSWORD = "LA2028sGoldM"

    def wait_for_sign_in_result(self, timeout=10):
    
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.any_of(
                    EC.url_contains("/welcome.jsp"),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'sign in')]")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'error')]")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'already been registered')]")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'⚠️')]"))
                )
            )
        except TimeoutException:
            logger.warning("Login/Registration result timeout")
            
    def register_test_user(self):
        logger.info("Attempting to register a fresh test user...")

        self.driver.get(REGISTER_URL)
        try:
            self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
        except TimeoutException:
            logger.error("Register page failed to load!")
            self.test_email = self.FALLBACK_EMAIL
            self.test_password = self.FALLBACK_PASSWORD
            return False

        safe_email = f"user{self.timestamp}@test.com"
        safe_username = f"User{self.timestamp}"
        safe_password = "Abc12345"

        try:
            self.driver.find_element(By.NAME, "username").clear()
            self.driver.find_element(By.NAME, "username").send_keys(safe_username[-20:])

            self.driver.find_element(By.NAME, "email").clear()
            self.driver.find_element(By.NAME, "email").send_keys(safe_email[-100:])

            self.driver.find_element(By.NAME, "password").clear()
            self.driver.find_element(By.NAME, "password").send_keys(safe_password)

            self.driver.find_element(By.NAME, "confirmPassword").clear()
            self.driver.find_element(By.NAME, "confirmPassword").send_keys(safe_password)

            # Agree to terms
            try:
                checkbox = self.driver.find_element(By.ID, "form2Example3c")
                if not checkbox.is_selected():
                    checkbox.click()
            except:
                pass  

            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

            # Proper waiting: Wait only once; if successful, return True.
            self.wait.until(EC.url_contains("login.jsp?register=success"))
            logger.info(f"Fresh test user registered successfully: {safe_email}")
            self.test_email = safe_email
            self.test_password = safe_password
            return True

        except TimeoutException:
            logger.error("Registration failed (timeout) → falling back to fixed safe account")
        except WebDriverException as e:
            logger.error(f"Registration crashed (WebDriver error): {e}")
        except Exception as e:
            logger.error(f"Unexpected error during registration: {e}")

        # All failure scenarios lead here → Use the fallback account
        current_url = self.driver.current_url
        logger.error(f"Registration failed. Current URL: {current_url} | Title: {self.driver.title}")
        self.take_screenshot("REGISTER_FAILURE_DEBUG")

        logger.warning("Using FALLBACK safe account for login tests")
        self.test_email = self.FALLBACK_EMAIL
        self.test_password = self.FALLBACK_PASSWORD
        return False
    
    # Test Case ID: test_LGN_002
    # Test Case Name: Missing Email 
    def missing_email(self):
        test_name = "LGN-002 - Missing Email (Submit Empty Email)"
        logger.info(f"Starting {test_name}")

        self.driver.get(LOGIN_URL)
        self.wait.until(EC.presence_of_element_located((By.NAME, "email")))

        # Intentionally leaving the email field blank and only filling in the password
        self.driver.find_element(By.NAME, "email").clear()
        self.driver.find_element(By.NAME, "password").send_keys("anything")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        self.wait_for_sign_in_result()

        page_source = self.driver.page_source.lower()
        current_url = self.driver.current_url

        # Expected Scenario：A prompt stating “Email is required” or similar must be displayed, and the page must not redirect.
        if ("email required" in page_source or 
            "enter a valid email" in page_source or 
            "email address" in page_source or
            "incorrect email or password" in page_source):  

            if WELCOME_URL not in current_url:
                self.log_test_result(test_name, "PASS", "Empty email correctly blocked with validation message")
                return True
            else:
                self.take_screenshot("LGN002_BYPASS_empty_email")
                self.log_test_result(test_name, "FAIL", "CRITICAL: Login succeeded with empty email!", {"severity": "CRITICAL"})
                return False
            
        # Critical Issues: No validation message shown for empty email
        else:
            self.take_screenshot("LGN002_no_error_message")
            self.log_test_result(test_name, "FAIL", "No validation message shown for empty email")
            return False

    # Test Case ID: test_LGN_006
    # Test Case Name: Email With Leading/Trailing Spaces
    def email_with_spaces(self):
        test_name = "LGN-006 - Email With Leading/Trailing Spaces"
        logger.info(f"Starting {test_name}")

        if not hasattr(self, 'test_email') or not self.test_email:
            self.log_test_result(test_name, "SKIP", "Test user not registered, skipping")
            return True

        spaced_variants = [
            f"  {self.test_email} ",
            f"\t{self.test_email}\t",
            f" {self.test_email}",
            f"{self.test_email}  ",
        ]

        trimmed_success = 0
        total_tests = len(spaced_variants)

        for spaced_email in spaced_variants:
            self.driver.get(LOGIN_URL)
            self.wait.until(EC.presence_of_element_located((By.NAME, "email")))

            self.driver.find_element(By.NAME, "email").send_keys(spaced_email)
            self.driver.find_element(By.NAME, "password").send_keys(self.test_password)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

            self.wait_for_sign_in_result()

            if WELCOME_URL in self.driver.current_url:
                logger.info(f"Login successful with spaced email (auto-trimmed): {spaced_email.strip()}")
                trimmed_success += 1
            else:
                page_source = self.driver.page_source.lower()
                if "incorrect email or password" in page_source:
                    logger.warning(f"Login rejected with spaced email: {spaced_email.strip()} (not trimmed)")
                else:
                    self.take_screenshot(f"LGN006_unexpected_behavior_{spaced_email[:10].replace(' ', '')}")

        if trimmed_success == total_tests:
            self.log_test_result(test_name, "PASS", "Email spaces automatically trimmed → login successful (Best UX)")
            return True
        elif trimmed_success == 0:
            self.log_test_result(test_name, "PASS", "Email spaces consistently rejected → behavior predictable")
            return True
        else:
            self.log_test_result(test_name, "WARN",
                                 f"Inconsistent behavior: {trimmed_success}/{total_tests} spaced emails allowed",
                                 {"note": "Partial trim → unpredictable UX, recommend full trim or full reject"})
            return True

    def run_all_loginvalidation_tests(self):
        if not self.setup():
            return

        try:
            logger.info("\n" + "="*80)
            logger.info("STARTING LOGIN VALIDATION TESTS: LGN-002 & LGN-006")
            logger.info("="*80)

            self.register_test_user()      
            self.missing_email()           
            self.email_with_spaces()      

            logger.info("="*80)
            logger.info("LOGIN VALIDATION TEST SUITE COMPLETED")
            logger.info("="*80)

        finally:
            self.teardown()

