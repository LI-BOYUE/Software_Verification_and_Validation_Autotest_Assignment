# registration_tests.py
from .Email_Validation import EmailValidationTests
from .Input_Normalization_Robustness import AdvancedInputCaseTests
from .Password_Length_Boundary import PasswordLengthBoundaryTest
from .RF_BV import BoundaryAndSpecialInputTests
from test_base import TestBase, logger

class RegistrationTests(TestBase):
    def __init__(self):
        super().__init__()
        self.email_tests = EmailValidationTests()
        self.input_tests = AdvancedInputCaseTests()
        self.password_tests = PasswordLengthBoundaryTest()
        self.rf_bv_tests = BoundaryAndSpecialInputTests()

    def run_all_registration_tests(self):
        if not self.setup():
            return

        try:
            logger.info("\n" + "="*80)
            logger.info("STARTING FULL REGISTRATION TEST SUITE")
            logger.info("="*80)

            self.email_tests.run_all_email_tests()
            self.input_tests.run_all_inputNR_tests()
            self.password_tests.run_all_password_tests()
            self.rf_bv_tests.run_all_RF_BV_tests()

            logger.info("="*80)
            logger.info("FULL REGISTRATION TEST SUITE COMPLETED")
            logger.info("="*80)

        finally:
            self.teardown()