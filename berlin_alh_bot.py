import os
import os
import sys
import time
import traceback
from platform import system

import coloredlogs
import logging
from dotenv import load_dotenv
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

import custom_webdriver
import notifier
import sound


def sleep(seconds=2):
    logging.info("Sleeping for %d seconds", seconds)
    time.sleep(seconds)


class BerlinBot:
    def __init__(self):
        self._sound_file = os.path.join(os.getcwd(), "alarm.wav")
        # Ihre Sitzung wird in 0 : 54 beendet. Möchten Sie die Sitzung verlängern?

    @staticmethod
    def check_exists_by_xpath(driver: webdriver.WebDriver, xpath):
        try:
            driver.find_element(By.XPATH, xpath)
        except NoSuchElementException:
            return False
        return True

    def submit_form(self, driver, element_name, selector_type, selector):
        logging.info(element_name)
        if self.is_success(driver):
            logging.error("Submit button not found.. retrying..")
            self._success()
        else:
            self.click(driver, element_name, selector_type, selector)

    def is_success(self, driver):
        return ("applicationForm:managedForm:proceed" not in custom_webdriver.get_page_source(driver)
                and self.visaExtensionButtonCount(driver) == 0)

    @staticmethod
    def click(driver, element_name, selector_type, selector):
        for i in range(3):
            try:
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((selector_type, selector))).click()
                break
            except Exception as exception:
                logging.warning(str(exception.__cause__) + ".. retry=" + str(i) + " (" + element_name + ")")

    @staticmethod
    def enter_start_page(self, driver: webdriver.WebDriver):
        logging.info("Visit start page")
        driver.get("https://otv.verwalt-berlin.de/ams/TerminBuchen")
        while self.check_exists_by_xpath(driver, "//*[contains(text(),'500 - Internal Server Error')]"):
            logging.error("Page error - 500 - Internal Server Error")
            sleep(1)
            driver.refresh()
        self.click(driver, "Start page", By.XPATH,
                   '//*[@id="mainForm"]/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/a')

    @staticmethod
    def tick_off_agreement(self, driver: webdriver.WebDriver):
        logging.info("Ticking off agreement")
        self.click(driver, "Select agreement", By.XPATH,
                   '//*[@id="xi-div-1"]/div[4]/label[2]/p')
        self.click(driver, "Submit button", By.ID, 'applicationForm:managedForm:proceed')

    @staticmethod
    def enter_form(self, driver: webdriver.WebDriver):
        while "Angaben zum Anliegen" not in custom_webdriver.get_page_source(driver):
            sleep(1)
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

            # extend residence permit
            self.click(driver, "Selecting - extend residence permit", By.XPATH,
                       '//label[@for="SERVICEWAHL_DE3436-0-2"]')

            # family reasons
            self.click(driver, "Clicking - family reasons", By.XPATH,
                       '//*[@id="inner-436-0-2"]/div/div[5]/label/p')

            # Residence permit for spouses, parents and children of foreign family members (§§ 29-34)
            self.click(driver, "Selecting - Residence permit for spouses, "
                               "parents and children of foreign family members (§§ 29-34)", By.XPATH,
                       '//*[@id="inner-436-0-2"]/div/div[6]/div/div[3]/label')

            # submit form
            self.submit_form(driver, "Form Submit.", By.ID, 'applicationForm:managedForm:proceed')

        except TimeoutException as toe:
            logging.error("TimeoutException occurred - %s", toe)
            notifier.send_to_telegram("💀TimeoutException occurred - {0}".format(str(toe)))
            driver.__exit__(None, None, None)
            BerlinBot().run_loop()
        except Exception as exp:
            logging.error("Exception occurred - %s", exp)
            notifier.send_to_telegram("💀Exception occurred - {0}".format(str(exp)))
            driver.__exit__(None, None, None)
            BerlinBot().run_loop()

    @staticmethod
    def visaExtensionButtonFound(driver):
        return len(driver.find_elements(By.XPATH, '//label[@for="SERVICEWAHL_DE3436-0-2"]')) == 0

    @staticmethod
    def visaExtensionButtonCount(driver):
        return len(driver.find_elements(By.XPATH, '//*[contains(text(),"Aufenthaltstitel - verlängern")]'))

    def _success(self):
        logging.info("!!!SUCCESS - do not close the window!!!!")
        notifier.send_to_telegram("✅ POSSIBLE *AUSLANDERHORDE* APPOINTMENT FOUND.")
        while True:
            sound.play_sound_osx(self._sound_file)
            sleep(300)

    def run_once(self):
        with custom_webdriver.WebDriver() as driver:
            driver.maximize_window()
            try:
                self.enter_start_page(self, driver)
                self.tick_off_agreement(self, driver)
                self.enter_form(self, driver)

                # retry submit
                for i in range(10):
                    sleep(2)

                    if self.check_exists_by_xpath(driver, "//*[contains(text(),'beendet')]"):
                        logging.warning("Session closed message found, retrying..")
                        self.enter_form(self, driver)
                    if self.check_exists_by_xpath(driver, "//*[contains(text(),'keine Termine frei')]"):
                        logging.warning("No appointment available, retrying..")
                        self.enter_form(self, driver)

                    count = self.visaExtensionButtonCount(driver)
                    if count > 3:
                        logging.error("Duplicate button found, count=%d, retrying..", count)
                        sleep(3)
                        self.run_once()
                    if self.is_success(driver):
                        self._success()

                    logging.warning("Retry submitting form - # %d ", i)
                    self.enter_form(self, driver)
            finally:
                driver.close()

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
            sleep(2)


if __name__ == "__main__":
    try:
        sys.tracebacklimit = 0
        coloredlogs.install()
        system = system()
        load_dotenv()

        BerlinBot().run_loop()
    except BaseException as e:
        notifier.send_to_telegram("💀 Exception occurred - {0}, Trace:{1}".format(e, traceback.format_exc()))
        logging.error("Exception occurred - %s , trace=%s", e, traceback.format_exc())
