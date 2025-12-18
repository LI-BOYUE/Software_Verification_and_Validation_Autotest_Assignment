# auto_test.py
from Registration.registration_tests import RegistrationTests
from Login.login_tests import LoginTests
from test_base import logger

def auto_test():
    logger.info("="*80)
    logger.info("Starting Full Test: Register to Login to Security")
    logger.info("="*80)

    reg = RegistrationTests()
    reg.run_all_registration_tests()

    login = LoginTests()
    login.run_all_login_tests()

    reg.generate_report(final=True)

if __name__ == "__main__":
    auto_test()