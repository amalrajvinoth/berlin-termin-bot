import logging
import os
import sys
import traceback
from platform import system

import coloredlogs
from dotenv import load_dotenv
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from common import custom_webdriver
from common.common_util import sleep, click_by_xpath, send_success_message, wait_and_click_next, get_page_source, \
    init_logger

url = "https://service.berlin.de/dienstleistung/120686"
bot_name = "apartment_berlin_bot"
success_message = "✅ possible BERLIN APARTMENT appointment found. Please hurry to book your appointment by selecting first available time."
time_message = """00:00 Minuten"""


class BerlinBot:

    def run_loop(self):
        rounds = 0
        while True:
            rounds = rounds + 1
            self.find_appointment(rounds)
            sleep(2)

    @staticmethod
    def find_appointment(rounds=0):
        with (custom_webdriver.WebDriver(bot_name) as driver):
            driver.maximize_window()
            logging.info("Round - # %d, SessionId=%s", rounds, driver.session_id)
            try:
                BerlinBot.enter_start_page(driver)

                # retry submit
                for i in range(10):
                    if BerlinBot.is_success(driver):
                        send_success_message(driver, bot_name, success_message)
                        break
                    sleep(2)

                    if "keine Termine" in get_page_source(driver):
                        wait_and_click_next(time_message, driver, i)
                        logging.warning("Got message - Try again later, retrying..")
                    elif "Bitte entschuldigen Sie den Fehler" in get_page_source(driver):
                        logging.warning("Server error, retrying..")
                        BerlinBot.restart(driver)
                        break
                    logging.warning("Retry - # %d ", i)
            finally:
                driver.quit()

    @staticmethod
    def search_berlin_wide(driver: webdriver.WebDriver, element_name, selector_type, selector):
        logging.info(element_name)
        if BerlinBot.is_success(driver):
            send_success_message(driver, bot_name, success_message)
        else:
            click_by_xpath(driver, element_name, selector_type, selector)

    @staticmethod
    def is_success(driver: webdriver.WebDriver):
        return ("Terminvereinbarung" in custom_webdriver.get_page_source(driver) and
                "Bitte wählen Sie ein Datum:" in custom_webdriver.get_page_source(driver))

    @staticmethod
    def enter_start_page(driver: webdriver.ChromiumDriver):
        # logging.info("Visit start page")
        driver.get(url)
        elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Berlinweite Terminbuchung')]")
        for element in elements:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Berlinweite Terminbuchung')]")))
            driver.execute_script("arguments[0].click();", element)
        sleep(2)

    @staticmethod
    def restart(driver):
        driver.__exit__(None, None, None)
        BerlinBot().run_loop()

    @staticmethod
    def is_error_message(driver, message):
        try:
            return driver.find_element(By.XPATH, '//*[@id="messagesBox"]/ul/li[contains(text(), "' + message + '")]')
        except NoSuchElementException as exception:
            logging.warning("%s", str(exception.msg))
            return False


if __name__ == "__main__":
    try:
        # sys.tracebacklimit = 0
        system = system()
        load_dotenv()
        init_logger('APT')

        BerlinBot().run_loop()
    except BaseException as e:
        logging.error("Exception occurred - %s , trace=%s", e, traceback.format_exc())
