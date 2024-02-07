import logging
import os
import time
import re
import traceback
from platform import system

from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
from dotenv import load_dotenv

import notifier
import sound
import customer_webdriver

system = system()

load_dotenv()

logging.basicConfig(
    format='%(asctime)s\t%(levelname)s\t%(message)s',
    level=logging.INFO,
)


def check_exists_by_xpath(driver: webdriver.WebDriver, xpath):
    try:
        driver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        return False
    return True


def click(driver, element_name, selector_type, selector):
    logging.info(element_name)
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((selector_type, selector))).click()
    except ElementClickInterceptedException:
        logging.warning("ElementClickInterceptedException.. retry")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((selector_type, selector))).click()


class BerlinBot:
    def __init__(self):
        self.wait_time = 2
        self._sound_file = os.path.join(os.getcwd(), "alarm.wav")
        self._error_message0 = """späteren Zeitpunkt"""
        self._error_message1 = """Für die gewählte Dienstleistung sind aktuell keine Termine frei! Bitte"""
        self._error_message2 = """Für die gewählte Dienstleistung sind aktuell keine Termine frei! Bitte versuchen Sie 
        es zu einem späteren Zeitpunkt erneut"""
        self._session_closed_message = """Sitzung wurde beendet"""

    @staticmethod
    def enter_start_page(driver: webdriver.WebDriver):
        logging.info("Visit start page")
        driver.get("https://otv.verwalt-berlin.de/ams/TerminBuchen")
        while check_exists_by_xpath(driver, "//*[contains(text(),'500 - Internal Server Error')]"):
            logging.info("Page error - 500 - Internal Server Error")
            time.sleep(1)
            driver.refresh()
        click(driver, "start page", By.XPATH,
              '//*[@id="mainForm"]/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/a')

    @staticmethod
    def tick_off_agreement(driver: webdriver.WebDriver):
        logging.info("Ticking off agreement")
        click(driver, "Select agreement", By.XPATH,
              '//*[@id="xi-div-1"]/div[4]/label[2]/p')
        click(driver, "Submit button", By.ID, 'applicationForm:managedForm:proceed')

    @staticmethod
    def enter_form(driver: webdriver.WebDriver):
        while "Angaben zum Anliegen" not in customer_webdriver.get_page_source(driver):
            time.sleep(5)
        logging.info("Fill out form")

        try:
            # select china
            s = Select(driver.find_element(By.ID, 'xi-sel-400'))
            s.select_by_visible_text("Indien")
            # number of person
            s = Select(driver.find_element(By.ID, 'xi-sel-422'))
            s.select_by_visible_text("drei Personen")
            # family
            s = Select(driver.find_element(By.ID, 'xi-sel-427'))
            s.select_by_visible_text("ja")
            # family nationality
            s = Select(driver.find_element(By.ID, 'xi-sel-428'))
            s.select_by_visible_text("Indien")

            # fix bug of repeated "extend residence permit"
            count = len(driver.find_elements(By.XPATH, '//label[@for="SERVICEWAHL_DE3436-0-2"]'))
            logging.error("Aufenthaltstitel - verlängern count = %d", count)
            if count > 1:
                s.select_by_visible_text("Pakistan")
                s.select_by_visible_text("Indien")

            # extend residence permit
            click(driver, "Selecting - extend residence permit", By.XPATH,
                  "//*[contains(text(),'Aufenthaltstitel - verlängern')]")

            # family reasons
            click(driver, "Clicking - family reasons", By.XPATH,
                  '//*[@id="inner-436-0-2"]/div/div[5]/label/p')

            # Residence permit for spouses, parents and children of foreign family members (§§ 29-34)
            click(driver, "Selecting - Residence permit for spouses, "
                          "parents and children of foreign family members (§§ 29-34)", By.XPATH,
                  '//*[@id="inner-436-0-2"]/div/div[6]/div/div[3]/label')

            # submit form
            click(driver, "Form Submit.", By.ID,
                  'applicationForm:managedForm:proceed')

        except TimeoutException as toe:
            logging.error("TimeoutException occurred - %s", toe)
            notifier.send_to_telegram("💀TimeoutException occurred - {0}".format(str(toe)))
            driver.__exit__(None, None, None)
            BerlinBot().run_loop()
        except Exception as e:
            logging.error("Exception occurred - %s", e)
            notifier.send_to_telegram("💀Exception occurred - {0}".format(str(e)))
            driver.__exit__(None, None, None)
            BerlinBot().run_loop()

    def _success(self):
        logging.info("!!!SUCCESS - do not close the window!!!!")
        notifier.send_to_telegram("✅ POSSIBLE *AUSLANDERHORDE* APPOINTMENT FOUND.")
        while True:
            sound.play_sound_osx(self._sound_file)
            time.sleep(60)
        # todo play something and block the browser

    def run_once(self):
        with customer_webdriver.WebDriver() as driver:
            self.enter_start_page(driver)
            self.tick_off_agreement(driver)
            self.enter_form(driver)

            # retry submit
            for i in range(10):
                time.sleep(10)
                msg = customer_webdriver.get_page_source(driver)
                if (
                        self._error_message0 in msg or
                        self._error_message1 in msg or
                        self._error_message2 in msg or
                        self._session_closed_message in msg
                ):
                    pass
                else:
                    self._success()
                time.sleep(10)
                logging.info("Retry submitting form - # %d ", i)
                click(driver, "Form Submit.", By.ID,
                      'applicationForm:managedForm:proceed')
                time.sleep(self.wait_time)

    def run_loop(self):
        # play sound to check if it works
        notifier.send_to_telegram(" BOT Running for *VISA extension* APPOINTMENT")
        sound.play_sound_osx(self._sound_file)
        rounds = 0
        while True:
            rounds = rounds + 1
            logging.info("One more round - # %d", rounds)
            notifier.send_to_telegram("Round - {0}".format(rounds))
            self.run_once()
            time.sleep(self.wait_time)


if __name__ == "__main__":
    try:
        BerlinBot().run_loop()
    except BaseException as e:
        notifier.send_to_telegram("💀 Exception occurred - {0}, Trace:{1}".format(e, traceback.format_exc()))
        logging.error("Exception occurred - %s , trace=%s", e, traceback.format_exc())
