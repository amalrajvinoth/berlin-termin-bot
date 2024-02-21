# custom_webdriver.py
import logging

from selenium import webdriver

import notifier


def get_page_source(driver: webdriver.Chrome):
    for i in range(3):
        try:
            return driver.page_source
        except Exception as e:
            logging.error(f"failed to get page source", {e})
            alert_text = driver.switch_to.alert.text()
            if not alert_text:
                logging.error(f"failed and alert_text is ", {alert_text})
                driver.switch_to.alert.accept()


class WebDriver:
    def __init__(self):
        self._driver: webdriver.Chrome
        self._implicit_wait_time = 10

    def __enter__(self) -> webdriver.Chrome:
        logging.info("Open browser")
        # some stuff that prevents us from being locked out
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        self._driver = webdriver.Chrome(options=options)
        self._driver.implicitly_wait(self._implicit_wait_time)  # seconds
        self._driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self._driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/83.0.4103.53 Safari/537.36'})
        return self._driver

    def __exit__(self, exc_type, exc_value, exc_tb):
        logging.info("Close browser")
        if exc_type is not None:
            notifier.send_to_telegram(
                "💀Quiting program due to {0} = {1} at {2}".format(exc_type, exc_value, exc_tb))
        self._driver.quit()
