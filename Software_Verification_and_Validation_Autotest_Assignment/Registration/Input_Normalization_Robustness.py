# Input_Normalization_Robustness.py
from test_base import TestBase, logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import time
import threading

BASE_URL = "http://localhost:8080"
REGISTER_URL = f"{BASE_URL}/register.jsp"
LOGIN_URL = f"{BASE_URL}/login.jsp"
RS_URL = "register=success"

class AdvancedInputCaseTests(TestBase):
    def __init__(self):
        super().__init__()
        self.timestamp = int(time.time())
        self.test_email = f"edge{self.timestamp}@test.com"
        self.test_password = "Test1234abcd"

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

    #Test Case ID: test_REG_060
    #Test Case Name: Email with Spaces
    def email_with_spaces(self):
        test_name = "REG-060 - Email with Leading/Trailing Spaces"
        logger.info(f"Starting {test_name}")

        spaced_emails = [
            f"  1{self.test_email} ",      # Spaces before and after
            f"\t2{self.test_email}\t",     # Tab
            f" 3{self.test_email}",        # Leading Space
            f"4{self.test_email}  ",       # Space After
        ]

        for email in spaced_emails:
            self.driver.get(REGISTER_URL)
            self.wait.until(EC.presence_of_element_located((By.NAME, "email")))

            self.driver.find_element(By.NAME, "username").send_keys(f"user070_{self.timestamp}")
            self.driver.find_element(By.NAME, "email").send_keys(email)
            self.driver.find_element(By.NAME, "password").send_keys(self.test_password)
            self.driver.find_element(By.NAME, "confirmPassword").send_keys(self.test_password)
            self.driver.find_element(By.ID, "form2Example3c").click()
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            self.wait_for_registration_result()
            page_source = self.driver.page_source.lower()
            if RS_URL in self.driver.current_url or "sign in" in page_source:
                logger.info(f"Email with spaces accepted (trimmed): {email.strip()}")
            else:
                self.take_screenshot("REG060_space_rejected")
                self.log_test_result(test_name, "FAIL", "Email with spaces was rejected (should trim)", {"severity": "MEDIUM"})
                return False

        self.log_test_result(test_name, "PASS", "Email spaces consistently trimmed and accepted")
        return True

    #Test Case ID: test_REG_061
    #Test Case Name: Email Case Handling
    def email_case_handling(self):
        test_name = "REG-061 - Email Case Insensitive Duplicate Handling"
        logger.info(f"Starting {test_name}")

        emails = [f"CaseTest{self.timestamp}@Gmail.com", f"casetest{self.timestamp}@gmail.com"]

        # First Scenario: Registration of the uppercase version
        self.driver.get(REGISTER_URL)
        self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
        self.driver.find_element(By.NAME, "username").send_keys("user071_first")
        self.driver.find_element(By.NAME, "email").send_keys(emails[0])
        self.driver.find_element(By.NAME, "password").send_keys(self.test_password)
        self.driver.find_element(By.NAME, "confirmPassword").send_keys(self.test_password)
        self.driver.find_element(By.ID, "form2Example3c").click()
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        self.wait_for_registration_result()
        page_source = self.driver.page_source.lower()
        if RS_URL not in self.driver.current_url or "sign in" not in page_source:
            self.log_test_result(test_name, "FAIL", "First registration failed")
            return False

        # Second Scenario: Attempt to register lowercase version → Should prompt for duplicate
        self.driver.get(REGISTER_URL)
        self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
        self.driver.find_element(By.NAME, "username").send_keys("user071_duplicate")
        self.driver.find_element(By.NAME, "email").send_keys(emails[1])
        self.driver.find_element(By.NAME, "password").send_keys(self.test_password)
        self.driver.find_element(By.NAME, "confirmPassword").send_keys(self.test_password)
        self.driver.find_element(By.ID, "form2Example3c").click()
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        self.wait_for_registration_result()

        page_source = self.driver.page_source.lower()
        if "already been registered" in page_source or "Warning" in page_source:
            self.log_test_result(test_name, "PASS", "Email case-insensitive duplicate correctly blocked")
            return True
        else:
            self.take_screenshot("REG061_case_bypass")
            self.log_test_result(test_name, "FAIL", "CRITICAL: Email case sensitivity bypass!", {"severity": "CRITICAL"})
            return False

    #Test Case ID: test_REG_062
    #Test Case Name: Bypass Frontend Validation
    def bypass_frontend_validation(self):
        test_name = "REG-062 - Bypass Frontend Validation with JS Injection"
        logger.info(f"Starting {test_name}")

        self.driver.get(REGISTER_URL)
        self.wait.until(EC.presence_of_element_located((By.NAME, "email")))

        # Directly setting invalid email addresses using JavaScript (bypassing frontend regular expressions)
        invalid_email = "bypass@evil.com"
        self.driver.execute_script(f"document.getElementsByName('email')[0].value = '{invalid_email}';")
        self.driver.execute_script("document.getElementsByName('email')[0].dispatchEvent(new Event('input'));")

        self.driver.find_element(By.NAME, "username").send_keys(f"bypass{self.timestamp}")
        self.driver.find_element(By.NAME, "password").send_keys("Weak1")
        self.driver.find_element(By.NAME, "confirmPassword").send_keys("Weak1")
        self.driver.find_element(By.ID, "form2Example3c").click()
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        self.wait_for_registration_result()
        page_source = self.driver.page_source.lower()
        if RS_URL in self.driver.current_url or "sign in" in page_source:
            self.take_screenshot("REG062_BYPASS_SUCCESS")
            self.log_test_result(test_name, "FAIL", "CRITICAL: Frontend validation bypassed AND backend accepted weak/invalid data!", {"severity": "CRITICAL"})
            return False
        else:
            self.log_test_result(test_name, "PASS", "Backend correctly rejected even when frontend was bypassed")
            return True
        
    #Test Case ID: test_REG_063
    #Test Case Name: Password With Leading/Trailing Spaces
    def password_with_spaces(self):
        test_name = "REG-063 - Password Leading/Trailing Spaces Handling"
        logger.info(f"Starting {test_name}")

        spaced_pwd = "  Test1234abcd  "
        self.driver.get(REGISTER_URL)
        self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
        self.driver.find_element(By.NAME, "username").send_keys(f"user073_{self.timestamp}")
        self.driver.find_element(By.NAME, "email").send_keys(f"pwdspace{self.timestamp}@test.com")
        self.driver.find_element(By.NAME, "password").send_keys(spaced_pwd)
        self.driver.find_element(By.NAME, "confirmPassword").send_keys(spaced_pwd)
        self.driver.find_element(By.ID, "form2Example3c").click()
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        self.wait_for_registration_result()
        page_source = self.driver.page_source.lower()
        if RS_URL not in self.driver.current_url or "sign in" not in page_source:
            self.log_test_result(test_name, "FAIL", "Registration failed with spaced password")
            return False

        # Attempting to log in with a password without spaces → Should succeed (indicating backend automatically trims spaces)
        self.driver.get(LOGIN_URL)
        self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
        self.driver.find_element(By.NAME, "email").send_keys(f"pwdspace{self.timestamp}@test.com")
        self.driver.find_element(By.NAME, "password").send_keys("Test1234abcd")  
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        self.wait_for_registration_result()
        page_source = self.driver.page_source.lower()
        if RS_URL in self.driver.current_url or "sign in" in page_source:
            self.log_test_result(test_name, "PASS", "Password spaces trimmed consistently (register & login)")
            return True
        else:
            self.take_screenshot("REG063_space_login_fail")
            self.log_test_result(test_name, "FAIL", "Password spaces NOT trimmed → login failed", {"severity": "HIGH"})
            return False
        
    #Test Case ID: test_REG_064
    #Test Case Name: Form State After Error
    def form_state_after_error(self):
        test_name = "REG-064 - Form State Retention After Validation Error"
        logger.info(f"Starting {test_name}")

        self.driver.get(REGISTER_URL)
        self.wait.until(EC.presence_of_element_located((By.NAME, "email")))

        username = f"user074_{self.timestamp}"
        email = f"state{self.timestamp}@test.com"

        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "email").send_keys(email)
        self.driver.find_element(By.NAME, "password").send_keys("weak")  
        self.driver.find_element(By.NAME, "confirmPassword").send_keys("weak")
        self.driver.find_element(By.ID, "form2Example3c").click()
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        self.wait_for_registration_result()

        # Resubmit after password reset
        self.driver.find_element(By.NAME, "password").clear()
        self.driver.find_element(By.NAME, "password").send_keys("again")
        self.driver.find_element(By.NAME, "confirmPassword").clear()
        self.driver.find_element(By.NAME, "confirmPassword").send_keys("again")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        self.wait_for_registration_result()

        # Check whether the username and email address are reserved.
        try:
            current_username = self.driver.find_element(By.NAME, "username").get_attribute("value")
            current_email = self.driver.find_element(By.NAME, "email").get_attribute("value")
        except:
            current_username = ""
            current_email = ""
            logger.warning("Username/email fields not found after validation error - likely page refreshed")

        if current_username == username and current_email == email:
            self.log_test_result(test_name, "PASS", "Form state correctly retained after error")
            return True
        else:
            self.take_screenshot("REG064_state_lost")
            self.log_test_result(test_name, "FAIL", "Form data lost after validation error")
            return False

    #Test Case ID: test_REG_066
    #Test Case Name: Double-Click Register
    def double_click_register_button(self):
        test_name = "REG-066 - Double-Click Register Button Protection"
        logger.info(f"Starting {test_name}")

        self.driver.get(REGISTER_URL)
        self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))

        email = f"double{self.timestamp}@test.com"
        self.driver.find_element(By.NAME, "username").send_keys(f"user076_{self.timestamp}")
        self.driver.find_element(By.NAME, "email").send_keys(email)
        self.driver.find_element(By.NAME, "password").send_keys(self.test_password)
        self.driver.find_element(By.NAME, "confirmPassword").send_keys(self.test_password)
        self.driver.find_element(By.ID, "form2Example3c").click()

        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

        # Double-click quickly
        ActionChains(self.driver).double_click(submit_btn).perform()
        self.wait_for_registration_result()

        # Verify that only one account has been created.
        self.driver.get(REGISTER_URL)
        self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
        self.driver.find_element(By.NAME, "email").send_keys(email)
        self.driver.find_element(By.NAME, "username").send_keys("duplicate_check")
        self.driver.find_element(By.NAME, "password").send_keys(self.test_password)
        self.driver.find_element(By.NAME, "confirmPassword").send_keys(self.test_password)
        self.driver.find_element(By.ID, "form2Example3c").click()
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        self.wait_for_registration_result()

        if "already been registered" in self.driver.page_source.lower():
            self.log_test_result(test_name, "PASS", "Double-click prevented → only one account created")
            return True
        else:
            self.take_screenshot("REG066_DOUBLE_SUCCESS")
            self.log_test_result(test_name, "FAIL", "CRITICAL: Double submission created duplicate account!", {"severity": "CRITICAL"})
            return False

    # Test Case ID: REG-067
    # Test Case Name: Concurrent registration with same email in two tabs
    def concurrent_same_email(self):
        test_name = "REG-067 - Concurrent registration with same email in two tabs"
        logger.info(f"Starting {test_name}")

        email = f"race{self.timestamp}@test.com"
        password = self.test_password

        # Open Tab A
        driver1 = self.driver
        driver1.get(REGISTER_URL)
        self.wait.until(EC.presence_of_element_located((By.NAME, "email")))

        # Open Tab B
        driver1.execute_script("window.open('');")
        self.switch_to_window(1)                     
        driver2 = self.driver                         
        driver2.get(REGISTER_URL)
        self.wait.until(EC.presence_of_element_located((By.NAME, "email")))

        # Fill both forms with same email
        driver1.find_element(By.NAME, "username").send_keys(f"user067A_{self.timestamp}")
        driver1.find_element(By.NAME, "email").send_keys(email)
        driver1.find_element(By.NAME, "password").send_keys(password)
        driver1.find_element(By.NAME, "confirmPassword").send_keys(password)
        driver1.find_element(By.ID, "form2Example3c").click()

        driver2.find_element(By.NAME, "username").send_keys(f"user067B_{self.timestamp}")
        driver2.find_element(By.NAME, "email").send_keys(email)
        driver2.find_element(By.NAME, "password").send_keys(password)
        driver2.find_element(By.NAME, "confirmPassword").send_keys(password)
        driver2.find_element(By.ID, "form2Example3c").click()

        # Click Register almost simultaneously
        def click_submit(d):
            d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        thread1 = threading.Thread(target=click_submit, args=(driver1,))
        thread2 = threading.Thread(target=click_submit, args=(driver2,))
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        self.wait_for_registration_result()

        # Count how many tabs show success
        success_tabs = 0
        if RS_URL in driver1.current_url or "sign in" in driver1.page_source.lower():
            success_tabs += 1
        
        self.switch_to_window(1)                     
        if RS_URL in self.driver.current_url or "sign in" in self.driver.page_source.lower():
            success_tabs += 1
        self.switch_to_window(0)                     

        # Expected: Only ONE tab succeeds
        if success_tabs != 1:
            self.take_screenshot("REG067_BOTH_SUCCESS_OR_NONE")   
            self.log_test_result(test_name, "FAIL", 
                                f"Race condition error: {success_tabs} tabs succeeded (expected exactly 1)", 
                                {"severity": "CRITICAL"})
            return False                                     

        # Final verification: Try registering the same email again → must be rejected
        self.driver.get(REGISTER_URL)
        self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
        self.driver.find_element(By.NAME, "email").send_keys(email)
        self.driver.find_element(By.NAME, "username").send_keys("check_duplicate")
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.NAME, "confirmPassword").send_keys(password)
        self.driver.find_element(By.ID, "form2Example3c").click()
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        self.wait_for_registration_result()

        if "already been registered" in self.driver.page_source.lower():
            self.log_test_result(test_name, "PASS", 
                                "Race condition handled correctly: only one account created despite concurrent requests")
            return True
        else:
            self.take_screenshot("REG067_DUPLICATE_ALLOWED")
            self.log_test_result(test_name, "FAIL", 
                                "CRITICAL: Duplicate account created due to race condition!", 
                                {"severity": "CRITICAL"})
            return False

    # Test Case ID: REG-068
    # Test Case Name: Concurrent registration of different accounts in parallel tabs
    def concurrent_different_accounts(self):
        test_name = "REG-068 - Concurrent registration of different accounts in parallel tabs"
        logger.info(f"Starting {test_name}")

        email_a = f"para{self.timestamp}a@test.com"
        email_b = f"para{self.timestamp}b@test.com"
        password = self.test_password

        driver1 = self.driver
        driver1.get(REGISTER_URL)
        self.wait.until(EC.presence_of_element_located((By.NAME, "email")))

        driver1.execute_script("window.open('');")
        self.switch_to_window(1)
        driver2 = self.driver
        driver2.get(REGISTER_URL)
        self.wait.until(EC.presence_of_element_located((By.NAME, "email")))

        # Fill Tab A
        driver1.find_element(By.NAME, "username").send_keys(f"user068A_{self.timestamp}")
        driver1.find_element(By.NAME, "email").send_keys(email_a)
        driver1.find_element(By.NAME, "password").send_keys(password)
        driver1.find_element(By.NAME, "confirmPassword").send_keys(password)
        driver1.find_element(By.ID, "form2Example3c").click()

        # Fill Tab B
        driver2.find_element(By.NAME, "username").send_keys(f"user068B_{self.timestamp}")
        driver2.find_element(By.NAME, "email").send_keys(email_b)
        driver2.find_element(By.NAME, "password").send_keys(password)
        driver2.find_element(By.NAME, "confirmPassword").send_keys(password)
        driver2.find_element(By.ID, "form2Example3c").click()

        # Click both at the same time
        def click_submit(d):
            d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        t1 = threading.Thread(target=click_submit, args=(driver1,))
        t2 = threading.Thread(target=click_submit, args=(driver2,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        time.sleep(3)
        self.wait_for_registration_result()

        self.switch_to_window(0)
        success_a = RS_URL in self.driver.current_url or "sign in" in self.driver.page_source.lower()
        self.switch_to_window(1)
        success_b = RS_URL in self.driver.current_url or "sign in" in self.driver.page_source.lower()
        self.switch_to_window(0)

        if not (success_a and success_b):
            self.take_screenshot("REG068_ONE_OR_BOTH_FAILED")
            self.log_test_result(test_name, "FAIL", 
                                "Concurrent registration of different accounts failed - at least one did not succeed")
            return False

        # Final verification: Both emails now exist → trying to register again should fail
        failed_count = 0

        for email in [email_a, email_b]:
            self.driver.get(REGISTER_URL)
            self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
            self.driver.find_element(By.NAME, "email").send_keys(email)
            self.driver.find_element(By.NAME, "username").send_keys("dup_check")
            self.driver.find_element(By.NAME, "password").send_keys(password)
            self.driver.find_element(By.NAME, "confirmPassword").send_keys(password)
            self.driver.find_element(By.ID, "form2Example3c").click()
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            self.wait_for_registration_result()

            if "already been registered" not in self.driver.page_source.lower():
                failed_count += 1

        if failed_count == 0:
            self.log_test_result(test_name, "PASS", 
                                "Two different accounts successfully registered concurrently, no interference")
            return True
        else:
            self.take_screenshot("REG068_ONE_NOT_PERSISTED")
            self.log_test_result(test_name, "FAIL", 
                                f"{failed_count} account(s) not actually persisted despite success message")
            return False
    def run_all_inputNR_tests(self):
        if not self.setup():
            return
        try:
            logger.info("\n" + "="*80)
            logger.info("STARTING ADVANCED EDGE CASE TESTS: REG-070 → REG-076")
            logger.info("="*80)

            self.email_with_spaces()
            self.email_case_handling()
            self.bypass_frontend_validation()
            self.password_with_spaces()
            self.form_state_after_error()
            self.double_click_register_button()
            self.concurrent_same_email()
            self.concurrent_different_accounts()

            logger.info("="*80)
            logger.info("ADVANCED EDGE CASE TEST SUITE COMPLETED")
            logger.info("="*80)

        finally:
            self.teardown()

