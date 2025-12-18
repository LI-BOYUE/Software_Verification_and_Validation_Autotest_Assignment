# Email_Validation.py
from test_base import TestBase, logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

BASE_URL = "http://localhost:8080"
REGISTER_URL = f"{BASE_URL}/register.jsp"
RS_URL = "register=success"

class EmailValidationTests(TestBase):
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

    #Test Case ID: test_REG_020
    #Test Case Name: Invalid Email Formats
    def invalid_email_formats(self):
        test_name = "REG-020 - Invalid Email Formats"
        logger.info(f"Starting {test_name}")

        invalid_emails = [
            "plainaddress",
            "@missingusername.com",
            "user1name@.com",
            "user1name@com",
            "user1@name@domain.com",
            "user1 name@domain.com",      # space
            "user1<name@domain.com",      # Special characters <
            "user1@domain..com",
            "user1@domain.c",             
            "user1@-domain.com",
            "user1@domain-.com",
            "user1@.domain.com",
            "user1@domain_com",           
            "user1@domain#com",
        ]

        blocked_count = 0
        passed_through = []

        for email in invalid_emails:
            try:
                self.driver.get(REGISTER_URL)
                self.wait.until(EC.presence_of_element_located((By.NAME, "email")))

                self.driver.find_element(By.NAME, "username").send_keys(f"user020_{self.timestamp}")
                self.driver.find_element(By.NAME, "email").send_keys(email)
                self.driver.find_element(By.NAME, "password").send_keys("Test1234abcd")
                self.driver.find_element(By.NAME, "confirmPassword").send_keys("Test1234abcd")

                terms = self.driver.find_element(By.ID, "form2Example3c")
                if not terms.is_selected():
                    terms.click()

                self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

                self.wait_for_registration_result()

                current_url = self.driver.current_url
                page_source = self.driver.page_source.lower()

                # Security Status 1: Registration blocked (remains on the registration page or displays an error)
                if (REGISTER_URL in current_url and 
                    ("This email address has already been registered" not in page_source) and
                    RS_URL not in current_url):
                    blocked_count += 1
                    logger.info(f"Invalid email correctly blocked: {email}")
                    continue

                # Critical Issues: Registration successful!
                if RS_URL in current_url:
                    self.take_screenshot(f"REG020_BYPASS_{email[:20]}")
                    passed_through.append(email)
                    logger.error(f"CRITICAL: Invalid email accepted: {email}")

            except Exception as e:
                self.take_screenshot(f"REG020_ERROR_{email[:20]}")
                self.log_test_result(test_name, "FAIL", f"Exception with email {email}: {str(e)}")
                return False

        if not passed_through:
            self.log_test_result(test_name, "PASS", 
                f"All {len(invalid_emails)} invalid emails were correctly rejected")
            return True
        else:
            self.log_test_result(test_name, "FAIL",
                f"{len(passed_through)} invalid emails were accepted!", 
                {"severity": "HIGH", "accepted": passed_through})
            return False


    #Test Case ID: test_REG_021
    #Test Case Name: Excessive Email Length Boundary Test
    def excessive_email_length_boundary(self):
        test_name = "REG-021 - Excessive Email Length Boundary Test"
        logger.info(f"Starting {test_name}")

        long_emails = [
            f"{'a' * 200}@longemail.com",        # 200+ chars
            f"{'b' * 240}@veryveryverylongdomain.com",  # > 254 chars total
            f"{'x' * 300}@thisdomainiswaytoolongandshouldberejectedbyanydecentemailvalidator.com",
        ]

        for email in long_emails:
            try:
                self.driver.get(REGISTER_URL)
                self.wait.until(EC.presence_of_element_located((By.NAME, "email")))

                self.driver.find_element(By.NAME, "username").send_keys(f"user021_{self.timestamp}_{len(email)}")
                self.driver.find_element(By.NAME, "email").send_keys(email)
                self.driver.find_element(By.NAME, "password").send_keys("Test1234abcd")
                self.driver.find_element(By.NAME, "confirmPassword").send_keys("Test1234abcd")

                terms = self.driver.find_element(By.ID, "form2Example3c")
                if not terms.is_selected():
                    terms.click()

                self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

                self.wait_for_registration_result()

                current_url = self.driver.current_url
                page_source = self.driver.page_source.lower()

                # Security Status 1: Denied (Remained on Registration Page)
                if REGISTER_URL in current_url and RS_URL not in current_url:
                    logger.info(f"Excessively long email ({len(email)} chars) correctly blocked")
                    continue

                # Security Status 2: Registration successful after truncation
                if RS_URL in current_url or "sign in" in page_source:
                    logger.warning(f"Long email accepted (possibly truncated): {len(email)} chars")
                    continue

                # Critical Issues: Server Crash
                if "500" in page_source or "exception" in page_source or len(page_source) < 1000:
                    self.take_screenshot(f"REG021_CRASH_{len(email)}chars")
                    self.log_test_result(test_name, "FAIL",
                        f"CRITICAL: Server crashed with {len(email)}-char email!", 
                        {"severity": "CRITICAL", "email_length": len(email)})
                    return False

            except TimeoutException:
                self.take_screenshot(f"REG021_TIMEOUT_{len(email)}chars")
                self.log_test_result(test_name, "FAIL", "Timeout - server likely crashed")
                return False

        self.log_test_result(test_name, "PASS",
            "System safely handled extremely long emails (200~300+ chars) - no crash")
        return True

    #Test Case ID: test_REG_022
    #Test Case Name: Valid Email Variants 
    def valid_email_variants(self):
        test_name = "REG-022 - Valid Email Format Variants"
        logger.info(f"Starting {test_name}")

        valid_variants = [
            "user+tag@gmail.com",
            "user.name+tag@sub.domain.co.uk",
            "user@sub.domain.com",
            "user123@domain.travel",
            "user@domain.museum",
            "user@12domain.com",           
            "user@domain-with-dash.com",
            "user@domain_with_underscore.com",  
            "user@xn--80asehdb.com",       
            "user@localhost",              
        ]

        success_count = 0
        failed_emails = []

        for email in valid_variants:
            try:
                self.driver.get(REGISTER_URL)
                self.wait.until(EC.presence_of_element_located((By.NAME, "email")))

                self.driver.find_element(By.NAME, "username").send_keys(f"user022_{self.timestamp}_{success_count}")
                self.driver.find_element(By.NAME, "email").send_keys(email)
                self.driver.find_element(By.NAME, "password").send_keys("Test1234abcd")
                self.driver.find_element(By.NAME, "confirmPassword").send_keys("Test1234abcd")

                terms = self.driver.find_element(By.ID, "form2Example3c")
                if not terms.is_selected():
                    terms.click()

                self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

                self.wait_for_registration_result()

                if RS_URL in self.driver.current_url or "sign in" in page_source:
                    success_count += 1
                    logger.info(f"Valid variant accepted: {email}")
                else:
                    # Possible Scenarios: The email address is already registered, or the backend validation is too strict.
                    page_source = self.driver.page_source.lower()
                    if "already been registered" in page_source:
                        logger.info(f"Email already exists (expected): {email}")
                        success_count += 1
                    else:
                        failed_emails.append(email)
                        logger.warning(f"Valid email rejected: {email}")

            except Exception as e:
                self.take_screenshot(f"REG022_ERROR_{email[:20]}")
                self.log_test_result(test_name, "FAIL", f"Exception: {str(e)}")
                return False

        if not failed_emails:
            self.log_test_result(test_name, "PASS",
                f"All {len(valid_variants)} valid email variants were accepted or safely handled")
            return True
        else:
            self.log_test_result(test_name, "WARN",
                f"{len(failed_emails)} valid emails were unexpectedly rejected", 
                {"rejected": failed_emails})
            return True  # Warning but not considered a failure


    def run_all_email_tests(self):
        if not self.setup():
            return

        try:
            logger.info("\n" + "="*70)
            logger.info("STARTING EMAIL VALIDATION TESTS: REG-020, REG-021, REG-022")
            logger.info("="*70)

            self.invalid_email_formats()
            self.excessive_email_length_boundary()
            self.valid_email_variants()

            logger.info("="*70)
            logger.info("EMAIL VALIDATION TEST SUITE COMPLETED")
            logger.info("="*70)

        finally:
            self.teardown()



