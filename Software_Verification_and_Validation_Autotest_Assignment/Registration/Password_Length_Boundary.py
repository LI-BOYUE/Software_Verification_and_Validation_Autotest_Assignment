# Password_Length_Boundary.py
from test_base import TestBase, logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
import time

BASE_URL = "http://localhost:8080"
REGISTER_URL = f"{BASE_URL}/register.jsp"
RS_URL = "register=success"

class PasswordLengthBoundaryTest(TestBase):
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

    #Test Case ID: test_REG_030
    #Test Case Name: Password Length Boundaries
    def password_length_boundaries(self):
        test_name = "REG-030 - Password Length Boundaries (MIN=3, MAX=25)"
        logger.info(f"Starting {test_name}")

        #Constructing Passwords
        def generate_valid_password(length):
            if length < 3:
                return "Ab1"[:length] if length > 0 else ""
            base = "Ab1"
            # Guaranteed to contain uppercase A, lowercase b, and the digit 1; all other positions filled with x.
            return base + "x" * (length - 3)  

        test_cases = [
            {"length": 2,  "desc": "MIN-1 (2 chars)",   "expected": "REJECT"},
            {"length": 3,  "desc": "MIN (3 chars)",     "expected": "ACCEPT"},
            {"length": 10, "desc": "Normal (10 chars)", "expected": "ACCEPT"},
            {"length": 25, "desc": "MAX (25 chars)",    "expected": "ACCEPT"},
            {"length": 26, "desc": "MAX+1 (26 chars)",  "expected": "REJECT"},
        ]

        passed_tests = []
        failed_tests = []

        for case in test_cases:
            length = case["length"]
            pwd = generate_valid_password(length)
            expected = case["expected"]

            try:
                self.driver.get(REGISTER_URL)
                self.wait.until(EC.presence_of_element_located((By.NAME, "email")))

                # Use unique usernames and email addresses to avoid conflicts.
                self.driver.find_element(By.NAME, "username").send_keys(f"user030_{self.timestamp}_{length}")
                self.driver.find_element(By.NAME, "email").send_keys(f"reg030_{self.timestamp}_{length}@test.com")
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

                # Determine the actual outcome
                is_accepted = RS_URL in current_url or "sign in" in page_source
                is_frontend_rejected = "invalid password" in page_source or "≤ 25 characters" in page_source
                is_still_on_register = REGISTER_URL in current_url and not is_accepted

                actual_result = "ACCEPT" if is_accepted else ("REJECT" if (is_frontend_rejected or is_still_on_register) else "UNKNOWN")

                # Critical Judgment
                if expected == "ACCEPT" and is_accepted:
                    passed_tests.append(f"{case['desc']} → ACCEPTED (PASS)")
                    logger.info(f"PASS: {case['desc']} → Correctly accepted")
                elif expected == "REJECT" and (is_frontend_rejected or (is_still_on_register and not is_accepted)):
                    passed_tests.append(f"{case['desc']} → REJECTED (PASS)")
                    logger.info(f"PASS: {case['desc']} → Correctly rejected")
                else:
                    # Failure Scenarios
                    self.take_screenshot(f"REG030_FAIL_length_{length}")
                    failed_tests.append({
                        "length": length,
                        "password": pwd,
                        "expected": expected,
                        "actual": actual_result,
                        "url": current_url,
                        "has_error_msg": "invalid password" in page_source
                    })
                    logger.error(f"FAIL: {case['desc']} | Expected: {expected} | Actual: {actual_result}")

            except TimeoutException:
                self.take_screenshot(f"REG030_TIMEOUT_length_{length}")
                failed_tests.append({"length": length, "error": "Timeout - server likely crashed"})
                logger.error(f"CRITICAL: Timeout on length {length} - possible server crash!")
            except Exception as e:
                self.take_screenshot(f"REG030_EXCEPTION_length_{length}")
                failed_tests.append({"length": length, "error": str(e)})
                logger.error(f"Exception on length {length}: {str(e)}")

        # Final Outcome Determination
        if not failed_tests:
            self.log_test_result(test_name, "PASS",
                f"All password length boundary tests passed | MIN=3, MAX=25 enforced correctly")
            logger.info("REG-030 PASSED - Password length boundaries are strictly enforced!")
            return True
        else:
            self.log_test_result(test_name, "FAIL",
                f"{len(failed_tests)}/{len(test_cases)} boundary tests failed!", 
                {"severity": "HIGH", "failed_cases": failed_tests})
            logger.error(f"REG-030 FAILED - See {len(failed_tests)} failed boundary conditions above")
            return False

    def run_all_password_tests(self):
        if not self.setup():
            return
        try:
            logger.info("\n" + "="*80)
            logger.info("STARTING REG-030: PASSWORD LENGTH BOUNDARY TEST (MIN=3, MAX=25)")
            logger.info("="*80)

            success = self.password_length_boundaries()

            if success:
                logger.info("REG-030 TEST SUITE COMPLETED SUCCESSFULLY")
            else:
                logger.error("REG-030 TEST SUITE FAILED - BOUNDARY VIOLATION DETECTED!")

            logger.info("="*80)

        finally:
            self.teardown()


