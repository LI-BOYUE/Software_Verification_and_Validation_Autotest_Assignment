# RF_BV.py
from test_base import TestBase, logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
import time

BASE_URL = "http://localhost:8080"
REGISTER_URL = f"{BASE_URL}/register.jsp"
RS_URL = "register=success"

class BoundaryAndSpecialInputTests(TestBase):
    def __init__(self):
        super().__init__()
        self.timestamp = int(time.time())
    def wait_for_registration_result(self, timeout=10):
        try:
            self.wait.until(
                EC.any_of(
                    EC.url_contains("/login.jsp?register=success"),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'sign in')]")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'error')]")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'already been registered')]")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'⚠️')]"))
                )
            )
        except TimeoutException:
            logger.warning("Waiting for registration result timed out")

    #Test Case ID: test_REG_014
    #Test Case Name: Password Field Illegal & Special Characters Handling
    def password_illegal_special_characters(self):
        test_name = "REG-014 - Password Field Illegal & Special Characters Handling"
        logger.info(f"Starting {test_name}")

        # Dangerous Character Set
        dangerous_passwords = [
            "Test123中文",                  
            "Test123😈🔥",                  
            "Test123\n\r\t",                 
            "Test123' OR '1'='1",            
            "Test123\"; DROP TABLE users;--", 
            "Test123<script>alert(1)</script>",
            "Test123%$#&*()_+",             
            "Test123ａｂｃ１２３",             
            "Test123\u200B\u2060",          
        ]

        passed_count = 0
        failed_cases = []

        for pwd in dangerous_passwords:
            try:
                self.driver.get(REGISTER_URL)
                self.wait.until(EC.presence_of_element_located((By.NAME, "email")))

                self.driver.find_element(By.NAME, "username").send_keys(f"user_{self.timestamp}_{passed_count}")
                self.driver.find_element(By.NAME, "email").send_keys(f"reg014_{self.timestamp}_{passed_count}@test.com")
                self.driver.find_element(By.NAME, "password").send_keys(pwd)
                self.driver.find_element(By.NAME, "confirmPassword").send_keys(pwd)

                # Check the terms
                terms = self.driver.find_element(By.ID, "form2Example3c")
                if not terms.is_selected():
                    terms.click()

                self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

                self.wait_for_registration_result()

                current_url = self.driver.current_url
                page_source = self.driver.page_source.lower()

                # Scenario 1: Registration successful → Special characters permitted
                if RS_URL in current_url or "sign in" in page_source:
                    logger.info(f"Password with special chars accepted: {pwd.encode('unicode_escape')}")
                    passed_count += 1
                    continue

                # Scenario 2: Rejected by front-end JavaScript (password format mismatch)
                if "invalid password" in page_source or "password must include" in page_source:
                    logger.info(f"Password correctly blocked by frontend: {pwd.encode('unicode_escape')}")
                    passed_count += 1
                    continue

                # Scenario 3: Backend explicitly rejects
                if "already been registered" not in page_source and ("error" in current_url or "⚠️" in page_source):
                    logger.info(f"Password blocked by backend (safe): {pwd.encode('unicode_escape')}")
                    passed_count += 1
                    continue

                # Critical Issues: Page crashes, 500 errors, blank pages, unexpected redirects
                if "500" in page_source or "exception" in page_source or len(page_source) < 1000:
                    raise Exception("Server error or crash detected")

            except Exception as e:
                self.take_screenshot(f"REG014_CRITICAL_{pwd[:10]}")
                failed_cases.append({"password": pwd, "error": str(e)})
                self.log_test_result(test_name, "FAIL",
                    f"CRITICAL: System crashed or vulnerable with password: {pwd.encode('unicode_escape')}",
                    {"severity": "CRITICAL", "input": pwd})
                return False

        if not failed_cases:
            self.log_test_result(test_name, "PASS",
                f"All {len(dangerous_passwords)} dangerous passwords were safely handled (accepted or rejected cleanly)")
            return True
        else:
            self.log_test_result(test_name, "FAIL",
                f"{len(failed_cases)} cases caused crash/vulnerability", {"failed": failed_cases})
            return False

    # Test Case ID: test_REG_016
    # Test Case Name: Excessive Username Length Boundary 
    def excessive_username_length_boundary(self):
        test_name = "REG-016 - Excessive Username Length Boundary Test"
        logger.info(f"Starting {test_name}")

        long_usernames = [
            "A" * 200,   # 200 chars
            "B" * 500,   # 500 chars
            "C" * 1000,  # 1000 chars
            "X" * 2000,  # 2000 chars
        ]

        for username in long_usernames:
            try:
                self.driver.get(REGISTER_URL)
                self.wait.until(EC.presence_of_element_located((By.NAME, "username")))

                self.driver.find_element(By.NAME, "username").send_keys(username)
                self.driver.find_element(By.NAME, "email").send_keys(f"reg016_{self.timestamp}_{len(username)}@test.com")
                self.driver.find_element(By.NAME, "password").send_keys("Test1234abcd")
                self.driver.find_element(By.NAME, "confirmPassword").send_keys("Test1234abcd")

                terms = self.driver.find_element(By.ID, "form2Example3c")
                if not terms.is_selected():
                    terms.click()

                self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

                self.wait_for_registration_result()

                page_source = self.driver.page_source.lower()
                current_url = self.driver.current_url

                # Security Status 1: Legitimate Denial
                if REGISTER_URL in current_url and ("error" in current_url or "⚠️" in page_source):
                    logger.info(f"Long username ({len(username)} chars) correctly blocked")
                    continue

                # Security Status 2: Registration successful after being intercepted
                if RS_URL in current_url:
                    logger.warning(f"Long username ({len(username)} chars) accepted (possibly truncated)")
                    continue

                # Hazardous Conditions: Server Errors, Crashes, Abnormalities
                if "500" in page_source or "exception" in page_source or "sql" in page_source or len(page_source) < 1000:
                    self.take_screenshot(f"REG016_CRASH_{len(username)}chars")
                    self.log_test_result(test_name, "FAIL",
                        f"CRITICAL: Server crashed with {len(username)}-char username!",
                        {"severity": "CRITICAL", "length": len(username)})
                    return False

            except TimeoutException:
                self.take_screenshot(f"REG016_TIMEOUT_{len(username)}chars")
                self.log_test_result(test_name, "FAIL",
                    f"Timeout - likely server crashed with {len(username)}-char username", {"severity": "CRITICAL"})
                return False
            except Exception as e:
                self.take_screenshot(f"REG016_ERROR_{len(username)}chars")
                self.log_test_result(test_name, "FAIL", f"Exception with {len(username)} chars: {str(e)}")
                return False

        self.log_test_result(test_name, "PASS",
            "System safely handled extremely long usernames (200~2000 chars) - no crash or corruption")
        return True

    def run_all_RF_BV_tests(self):
        if not self.setup():
            return
        try:
            logger.info("\n" + "="*70)
            logger.info("STARTING REG-014 & REG-016 BOUNDARY & SECURITY TESTS")
            logger.info("="*70)

            self.password_illegal_special_characters()
            self.excessive_username_length_boundary()

        finally:
            self.teardown()