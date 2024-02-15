import logging
import os
import time
from platform import system

import coloredlogs

import notifier

from selenium import webdriver
from selenium.webdriver.common.by import By
from dotenv import load_dotenv

import sound

system = system()
load_dotenv()
logging.basicConfig(
    format='%(asctime)s\t%(levelname)s\t%(message)s',
    level=logging.INFO,
)


class WebDriver:
    def __init__(self):
        self._driver: webdriver.Chrome
        self._implicit_wait_time = 20

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


def get_wait_time(driver):
    time_to_wait = driver.find_element(By.XPATH, "//*[@id='calculatedSecs']").text
    logging.info("time_to_wait = %s", time_to_wait)
    time_to_wait_in_sec = int(time_to_wait.split(':')[1])
    return time_to_wait_in_sec


def get_page_source(driver):
    try:
        return driver.page_source
    except Exception as e:
        logging.error("failed to get page source %s!", e)
        alert_text = driver.switch_to().alert().getText()
        if not alert_text:
            logging.error("failed and alert_text is %s!", alert_text)
            driver.switch_to().alert().accept()
            return driver.page_source


class BerlinBot:
    def __init__(self):
        self.wait_time = 3
        self._sound_file = os.path.join(os.getcwd(), "alarm.wav")
        self._error_message1 = """Leider sind aktuell keine Termine für ihre Auswahl verfügbar."""
        self._error_message2 = """Bitte entschuldigen Sie den Fehler"""
        self._error_message3 = """Zu viele Zugriffe"""
        self._time_message = """00:00 Minuten"""

    def wait_and_click_next(self, driver, i):
        if self._time_message in get_page_source(driver):
            driver.back()
            time.sleep(2)
        logging.info("Try Search - # %d ", i)
        time_to_wait_in_sec = get_wait_time(driver)
        while time_to_wait_in_sec > 0:
            if self._time_message in get_page_source(driver):
                driver.back()
                time.sleep(2)
            time_to_wait_in_sec = get_wait_time(driver)
            logging.info("Wait for %d sec", time_to_wait_in_sec)
            time.sleep(time_to_wait_in_sec)
            if time_to_wait_in_sec == 0:
                logging.info("Click on Terminsuche wiederholen button")
                driver.find_element(By.XPATH, "//button[text()='Terminsuche wiederholen']").click()

    def _success(self):
        logging.info("!!!SUCCESS - do not close the window!!!!")
        notifier.send_to_telegram("✅ *Commitment letter* Appointment found ")
        while True:
            sound.play_sound_osx(self._sound_file)
            time.sleep(15)
        # todo play something and block the browser

    def run_once(self):
        with (WebDriver() as driver):
            self.enter_start_page(driver)

            if self._error_message1 in get_page_source(driver) or self._error_message2 in get_page_source(
                    driver) or self._error_message3 in get_page_source(driver):
                pass
            else:
                self._success()

            logging.info("not found")
            driver.close()

    def run_loop(self):
        # play sound to check if it works
        notifier.send_to_telegram("➡️BOT Running for *Commitment letter* Appointment 💡")
        sound.play_sound_osx(self._sound_file)
        while True:
            logging.info("One more round")
            self.run_once()
            time.sleep(self.wait_time)

    @staticmethod
    def enter_start_page(driver: webdriver.Chrome):
        logging.info("Visit start page")
        driver.get("https://service.berlin.de/dienstleistung/120691/en/")
        driver.find_element(By.XPATH,
                            "//*[contains(text(),'Make an appointment')]").click()
        time.sleep(2)


if __name__ == "__main__":
    coloredlogs.install()
    BerlinBot().run_loop()
