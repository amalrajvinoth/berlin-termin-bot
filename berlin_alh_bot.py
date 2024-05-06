import logging
import os
import sys
import time
import traceback
from platform import system

import coloredlogs
from dotenv import load_dotenv
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

import custom_webdriver
import notifier
import sound

_sound_file = os.path.join(os.getcwd(), "alarm.wav")


def sleep(seconds=2):
    logging.info("Sleeping for %d seconds", seconds)
    time.sleep(seconds)


class BerlinBot:

    @staticmethod
    def check_exists_by_xpath(driver: webdriver.WebDriver, xpath: str):
        return BerlinBot.find_by_xpath(driver, xpath)

    @staticmethod
    def count_by_xpath(driver: webdriver.WebDriver, xpath: str):
        return driver.find_elements(By.XPATH, xpath)

    @staticmethod
    def find_by_xpath(driver: webdriver.WebDriver, xpath: str, retry=3):
        for i in range(retry):
            try:
                return driver.find_element(By.XPATH, xpath)
            except NoSuchElementException as exception:
                logging.warning("%s, retry=%d", str(exception.msg), i)

    @staticmethod
    def submit_form(driver: webdriver.WebDriver, element_name, selector_type, selector):
        logging.info(element_name)
        if BerlinBot.is_success(driver):
            BerlinBot._success()
        else:
            BerlinBot.click(driver, element_name, selector_type, selector)

    @staticmethod
    def is_success(driver: webdriver.WebDriver):
        return ("applicationForm:managedForm:proceed" not in custom_webdriver.get_page_source(driver)
                and BerlinBot.is_visa_extension_button_not_found(driver))

    @staticmethod
    def click(driver: webdriver.WebDriver, element_name, selector_type, selector):
        for i in range(3):
            try:
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((selector_type, selector))).click()
                break
            except ElementClickInterceptedException as ecie:
                logging.warning("%s, retry=%d, (%s)", str(ecie.msg), i, element_name)
            except TimeoutException as exception:
                logging.warning("%s, retry=%d, (%s)", str(exception.msg), i, element_name)

    @staticmethod
    def enter_start_page(driver: webdriver.WebDriver):
        logging.info("Visit start page")
        driver.get("https://otv.verwalt-berlin.de/ams/TerminBuchen")
        while BerlinBot.find_by_xpath(driver, "//*[contains(text(),'500 - Internal Server Error')]", 0):
            logging.error("Page error - 500 - Internal Server Error")
            sleep(1)
            driver.refresh()
        BerlinBot.click(driver, "Start page", By.XPATH,
                        '//*[@id="mainForm"]/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/a')

    @staticmethod
    def tick_off_agreement(driver: webdriver.WebDriver):
        logging.info("Ticking off agreement")
        BerlinBot.click(driver, "Select agreement", By.XPATH,
                        '//*[@id="xi-div-1"]/div[4]/label[2]/p')
        BerlinBot.click(driver, "Submit button", By.ID, 'applicationForm:managedForm:proceed')

    @staticmethod
    def enter_form(driver: webdriver.WebDriver):
        while "Angaben zum Anliegen" not in custom_webdriver.get_page_source(driver):
            sleep(1)
        logging.info("Fill out form")

        try:
            # Citizenship = Indien 
            BerlinBot.select_dropdown(driver, By.ID, 'xi-sel-400', "Indien")
            # number of person
            BerlinBot.select_dropdown(driver, By.ID, 'xi-sel-422', "drei Personen")
            # Living with family member?
            BerlinBot.select_dropdown(driver, By.ID, 'xi-sel-427', "ja")
            # Family member Citizenship = Indien
            BerlinBot.select_dropdown(driver, By.ID, 'xi-sel-428', "Indien")
            sleep(1)
            # extend residence permit
            BerlinBot.click(driver, "Selecting - extend residence permit", By.XPATH,
                            '//label[@for="SERVICEWAHL_DE3436-0-2"]')

            # family reasons
            BerlinBot.click(driver, "Clicking - family reasons", By.XPATH,
                            '//*[@id="inner-436-0-2"]/div/div[5]/label/p')

            # Residence permit for spouses, parents and children of foreign family members (§§ 29-34)
            BerlinBot.click(driver, "Selecting - Residence permit for spouses, "
                                    "parents and children of foreign family members (§§ 29-34)", By.XPATH,
                            '//*[@id="inner-436-0-2"]/div/div[6]/div/div[3]/label')

            # submit form
            BerlinBot.submit_form(driver, "Form Submit.", By.ID, 'applicationForm:managedForm:proceed')

        except TimeoutException as toe:
            logging.error("TimeoutException occurred - %s", toe.msg)
            #notifier.send_to_telegram("💀{0}".format(toe.msg))
            BerlinBot.restart(driver)
        except Exception as exp:
            #notifier.send_to_telegram("💀 Exception occurred - {0}".format(e))
            logging.error("Exception occurred - %s , trace=%s", exp, traceback.format_exc())
            BerlinBot.restart(driver)

    @staticmethod
    def restart(driver):
        driver.__exit__(None, None, None)
        BerlinBot().run_loop()

    @staticmethod
    def select_dropdown(driver: webdriver.WebDriver, selector_type, selector, value):
        for i in range(3):
            try:
                s = Select(driver.find_element(selector_type, selector))
                s.select_by_visible_text(value)
                break
            except Exception as exception:
                logging.warning("%s, retry=%d (%s)", str(exception.__cause__), i, value)

    @staticmethod
    def is_visa_extension_button_not_found(driver: webdriver.WebDriver):
        return len(BerlinBot.count_by_xpath(driver, '//label[@for="SERVICEWAHL_DE3436-0-2"]')) == 0

    @staticmethod
    def visa_extension_button_count(driver):
        return len(BerlinBot.count_by_xpath(driver, '//*[contains(text(),"Aufenthaltstitel - verlängern")]'))

    @staticmethod
    def _success():
        logging.info("!!!SUCCESS - do not close the window!!!!")
        notifier.send_to_telegram("✅ POSSIBLE *AUSLANDERHORDE* APPOINTMENT FOUND.")
        while True:
            sound.play_sound_osx(_sound_file)
            sleep(300)

    @staticmethod
    def run_once(rounds=0):
        with (custom_webdriver.WebDriver() as driver):
            driver.maximize_window()
            logging.info("Round - # %d, SessionId=%s", rounds, driver.session_id)
            #notifier.send_to_telegram("Round - {0}, SessionId={1}".format(rounds, driver.session_id))
            try:
                BerlinBot.enter_start_page(driver)
                BerlinBot.tick_off_agreement(driver)
                BerlinBot.enter_form(driver)

                # retry submit
                for i in range(10):
                    sleep(2)

                    count = BerlinBot.visa_extension_button_count(driver)
                    if count > 3:
                        logging.error("Duplicate button found, count=%d, restarting..", count)
                        BerlinBot().restart(driver)
                        break
                    if BerlinBot.is_error_message(driver, "späteren Zeitpunkt"):
                        logging.warning("Got message - Try again later, retrying..")
                    elif BerlinBot.is_error_message(driver, "beendet"):
                        logging.warning("Session closed message found, retrying..")
                    elif BerlinBot.is_error_message(driver, "keine Termine frei"):
                        logging.warning("No appointment available, retrying..")
                    elif BerlinBot.is_success(driver):
                        BerlinBot._success()
                        break
                    logging.warning("Retry submitting form - # %d ", i)
                    BerlinBot.enter_form(driver)
            finally:
                driver.quit()

    @staticmethod
    def is_error_message(driver, message):
        try:
            return driver.find_element(By.XPATH, '//*[@id="messagesBox"]/ul/li[contains(text(), "'+message+'")]')
        except NoSuchElementException as exception:
            logging.warning("%s", str(exception.msg))
            return False

    def run_loop(self):
        # play sound to check if it works
        #notifier.send_to_telegram(" BOT Running for *VISA extension* APPOINTMENT")
        #sound.play_sound_osx(_sound_file)
        rounds = 0
        while True:
            rounds = rounds + 1
            self.run_once(rounds)
            sleep(2)


if __name__ == "__main__":
    try:
        sys.tracebacklimit = 0
        coloredlogs.install()
        system = system()
        load_dotenv()

        BerlinBot().run_loop()
    except BaseException as e:
        #notifier.send_to_telegram("💀 Exception occurred - {0}".format(e))
        logging.error("Exception occurred - %s , trace=%s", e, traceback.format_exc())
