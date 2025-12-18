# test_base.py
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

TIMEOUT = 10
test_results = {
    "total": 0, "passed": 0, "failed": 0, "bugs": [], "test_cases": []
}

class TestBase:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.screenshot_folder = None

    def setup(self, headless=False):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--start-maximized')
            if headless:
                options.add_argument('--headless')
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, TIMEOUT)

            self.screenshot_folder = f"screenshots/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(self.screenshot_folder, exist_ok=True)

            logger.info("WebDriver initialized")
            return True
        except Exception as e:
            logger.error(f"WebDriver init failed: {e}")
            return False

    def teardown(self):
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")

    def log_test_result(self, test_name, status, message="", bug_details=None):
        test_results["total"] += 1

        if status != "PASS":
            safe_name = "".join(c if c.isalnum() or c in " _-()" else "_" for c in test_name)
            self.take_screenshot(f"{status}_{safe_name}")

        if status == "PASS":
            test_results["passed"] += 1
            logger.info(f"PASS {test_name}: {message}")
        else:
            test_results["failed"] += 1
            logger.error(f"FAIL {test_name}: {message}")
            if bug_details:
                test_results["bugs"].append({
                    "test_name": test_name,
                    "description": message,
                    "details": bug_details,
                    "timestamp": datetime.now().isoformat()
                })
        test_results["test_cases"].append({
            "name": test_name, "status": status, "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def take_screenshot(self, name):
        try:
            path = f"{self.screenshot_folder}/{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.driver.save_screenshot(path)
            logger.info(f"Screenshot saved: {path}")
        except Exception as e:      
            logger.error(f"Failed to take screenshot: {e}")

    def generate_report(self, final=False):
        if not final:
            return
        logger.info("\n" + "="*70)
        logger.info("           FINAL AUTOMATED TEST REPORT")
        logger.info("="*70)
        total = test_results["total"]
        passed = test_results["passed"]
        rate = (passed/total*100) if total else 0
        logger.info(f"Total Tests : {total}")
        logger.info(f"Passed      : {passed}")
        logger.info(f"Failed      : {total - passed}")
        logger.info(f"Pass Rate   : {rate:.2f}%")

        if test_results['bugs']:
            logger.warning(f"\nFound {len(test_results['bugs'])} BUG(s):")
            for i, bug in enumerate(test_results['bugs'], 1):
                sev = bug['details'].get('severity', 'UNKNOWN')
                logger.warning(f"  [{sev}] BUG #{i}: {bug['test_name']} → {bug['description']}")
        else:
            logger.info("\nAll tests PASSED! No critical bugs found!")

        report_file = f"FINAL_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"\nFinal report saved: {report_file}")
        logger.info("="*70)