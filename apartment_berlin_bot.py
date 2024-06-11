import logging
import os
import re
from datetime import datetime

from dotenv import load_dotenv
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from common.common_util import sleep, send_success_message, init_logger, is_page_contains_text, click_by_xpath, \
    get_wait_time
from common.custom_webdriver import WebDriver

page_url = "https://service.berlin.de/dienstleistung/120686"
bot_name = "apartment_berlin_bot"
success_message = ("💚possible BERLIN APARTMENT appointment found. Please hurry to book your appointment by selecting "
                   "first available time.")
time_message = """00:00 Minuten"""
date_pattern = re.compile(r'\d{2}\.\d{2}\.\d{4}')


def print_available_dates(links):
    result_string = ""
    for link in links:
        date_match = date_pattern.search(link.accessible_name)
        if date_match:
            date_str = date_match.group()
            result_string += date_str + ", "

    logging.warning("Available dates found: %s", result_string)


class BerlinBot:
    def __init__(self, url):
        self._url = url
        self._driver = WebDriver(bot_name).__enter__()
        self._bot_name = bot_name
        self._driver.get(self._url)
        self._driver.minimize_window()

    def find_appointment_indefinitely(self):
        rounds = 0
        while True:
            rounds = rounds + 1
            self.find_appointment(rounds)
            sleep(2)

    def find_appointment(self, rounds=0):
        self._driver.minimize_window()
        logging.info("Round - # %d, SessionId=%s", rounds, self._driver.session_id)
        try:
            self.enter_start_page()

            # retry submit
            while True:
                if self.is_success():
                    send_success_message(self._driver, bot_name, success_message)
                    break

                if self.is_error_message("Zu viele Zugriffe"):
                    logging.warning("Too many hits, restarting..")
                    raise
                elif is_page_contains_text(self._driver, "keine Termine"):
                    logging.warning("Got message - No appointment found, retrying..")
                    self.wait_and_click_next()
                elif is_page_contains_text(self._driver, "Bitte entschuldigen Sie den Fehler"):
                    raise Exception("Server error, retrying..")
        except Exception as ex:
            logging.warning(ex)
            raise

    def is_success(self):
        if (bool(os.environ.get("APT_DATE_RANGE_ENABLED"))
                and is_page_contains_text(self._driver, "Bitte wählen Sie ein Datum:")):
            if not self.expected_date_range_found():
                sleep(10)
                self.restart()
                logging.warning("No expected dates found in date range, restarting")
                return False
            else:
                return True
        else:
            return (is_page_contains_text(self._driver, "Terminvereinbarung")
                    and is_page_contains_text(self._driver, "Bitte wählen Sie ein Datum:"))

    def restart(self):
        self._driver.refresh()
        self.enter_start_page()

    def enter_start_page(self):
        click_by_xpath(self._driver, "Berlinweite Terminbuchung",
                       By.XPATH, "//*[contains(text(), 'Berlinweite Terminbuchung')]")
        sleep(2)

    def wait_and_click_next(self):
        if is_page_contains_text(self._driver, time_message):
            self._driver.back()

        try:
            time_to_wait_in_sec = get_wait_time(self._driver, By.XPATH, "//*[@id='calculatedSecs']")
            if time_to_wait_in_sec == 0:
                click_by_xpath(self._driver, "Terminsuche wiederholen button",
                               By.XPATH, "//button[text()='Terminsuche wiederholen']")
            elif time_to_wait_in_sec == -1:
                self.restart()
            else:
                logging.info("Wait for %s sec", time_to_wait_in_sec)
                sleep(time_to_wait_in_sec)
        except Exception as ex:
            logging.warning(ex)

    def close(self, message):
        logging.exception("Close due to error= {0}".format(message))
        self._driver.quit()

    def is_error_message(self, message):
        try:
            return self._driver.find_element(By.XPATH,
                                             '//*[@id="messagesBox"]/ul/li[contains(text(), "' + message + '")]')
        except NoSuchElementException as exception:
            return False

    def expected_date_range_found(self):
        # Define the date range
        start = "16.06.2024"
        #start = get_next_date()
        end = os.environ.get("APT_DATE_RANGE_END")
        start_date = datetime.strptime(start, "%d.%m.%Y")
        end_date = datetime.strptime(end, "%d.%m.%Y")

        # Find all available dates
        links = self._driver.find_elements(By.CSS_SELECTOR, 'td.buchbar > a')
        print_available_dates(links)
        matching_links = []

        for link in links:
            aria_label = link.get_attribute('aria-label')
            if aria_label:
                date_match = date_pattern.search(aria_label)
                if date_match:
                    date_str = date_match.group()
                    date_obj = datetime.strptime(date_str, "%d.%m.%Y")
                    if start_date <= date_obj <= end_date:
                        logging.info("FOUND : "+aria_label)
                        matching_links.append(aria_label)

        return len(matching_links) > 0


if __name__ == "__main__":
    while True:
        berlin_bot = BerlinBot(page_url)
        try:
            #sys.tracebacklimit = 0
            load_dotenv()
            init_logger('APT')
            berlin_bot.find_appointment_indefinitely()
        except BaseException as e:
            berlin_bot.close(str(e))
