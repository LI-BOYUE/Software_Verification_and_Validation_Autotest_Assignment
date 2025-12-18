# login_tests.py
from .Basic_Authentication import LoginValidationTests
from .Security import LoginSecurityTests
from test_base import TestBase, logger

class LoginTests(TestBase):
    def __init__(self):
        super().__init__()
        self.validation_tests = LoginValidationTests()
        self.security_tests = LoginSecurityTests()

    def run_all_login_tests(self):
        if not self.setup():
            return

        try:
            logger.info("\n" + "="*80)
            logger.info("STARTING FULL LOGIN TEST SUITE")
            logger.info("="*80)

            self.validation_tests.run_all_loginvalidation_tests()
            self.security_tests.run_all_security_tests()

            logger.info("="*80)
            logger.info("FULL LOGIN TEST SUITE COMPLETED")
            logger.info("="*80)

        finally:
            self.teardown()