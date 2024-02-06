import logging
import os
import time

import traceback

import notifier
from platform import system

from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

system = system()

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
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})
        return self._driver

    def __exit__(self, exc_type, exc_value, exc_tb):
        logging.info("Close browser")
        if exc_type is not None:
            notifier.send_to_telegram(
                "⬅️ 💀💀💀 Quiting program due to {0} = {1} at {2} 💀💀💀".format(exc_type, exc_value, exc_tb))
        self._driver.quit()


def check_exists_by_xpath(driver: webdriver.Chrome, xpath):
    try:
        driver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        return False
    return True


def click(driver, element_name, selector_type, selector):
    logging.info(element_name)
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((selector_type, selector))).click();
    except ElementClickInterceptedException:
        logging.info("ElementClickInterceptedException.. retry")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((selector_type, selector))).click();


class BerlinBot:
    def __init__(self):
        self.wait_time = 2
        self._sound_file = os.path.join(os.getcwd(), "alarm.wav")
        self._error_message = """Für die gewählte Dienstleistung sind aktuell keine Termine frei! Bitte"""
        self._session_closed_message = """Sitzung wurde beendet"""

    @staticmethod
    def enter_start_page(driver: webdriver.Chrome):
        logging.info("Visit start page")
        driver.get("https://otv.verwalt-berlin.de/ams/TerminBuchen")
        while check_exists_by_xpath(driver, "//*[contains(text(),'500 - Internal Server Error')]"):
            logging.info("Page error - 500 - Internal Server Error")
            time.sleep(2)
            driver.refresh()
        click(driver, "start page", By.XPATH,
              '//*[@id="mainForm"]/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/a')

    @staticmethod
    def tick_off_some_bullshit(driver: webdriver.Chrome):
        logging.info("Ticking off agreement")
        click(driver, "Select agreement", By.XPATH,
              '//*[@id="xi-div-1"]/div[4]/label[2]/p')
        click(driver, "Submit button", By.ID, 'applicationForm:managedForm:proceed')

    @staticmethod
    def enter_form(driver: webdriver.Chrome):
        while not "Angaben zum Anliegen" in driver.page_source:
            time.sleep(5)
        logging.info("Fill out form")
        # select china
        s = Select(driver.find_element(By.ID, 'xi-sel-400'))
        s.select_by_visible_text("Indien")
        # eine person
        s = Select(driver.find_element(By.ID, 'xi-sel-422'))
        s.select_by_visible_text("drei Personen")
        # family
        s = Select(driver.find_element(By.ID, 'xi-sel-427'))
        s.select_by_visible_text("ja")
        # family nationality
        s = Select(driver.find_element(By.ID, 'xi-sel-428'))
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

    def _success(self):
        logging.info("!!!SUCCESS - do not close the window!!!!")
        notifier.send_to_telegram("✅POSSIBLE *AUSLANDERHORDE* APPOINTMENT ✅")
        while True:
            self._play_sound_osx(self._sound_file)
            time.sleep(15)
        # todo play something and block the browser

    def run_once(self):
        with WebDriver() as driver:
            self.enter_start_page(driver)
            self.tick_off_some_bullshit(driver)
            self.enter_form(driver)

            # retry submit
            for i in range(10):
                time.sleep(10)
                if not (
                        self._error_message in driver.page_source or self._session_closed_message in driver.page_source):
                    self._success()
                time.sleep(10)
                logging.info("Retry submitting form - # %d ", i)
                click(driver, "Form Submit.", By.ID,
                      'applicationForm:managedForm:proceed')
                time.sleep(self.wait_time)

    def run_loop(self):
        # play sound to check if it works
        notifier.send_to_telegram("➡️BOT Running for *VISA extension* APPOINTMENT 💡")
        self._play_sound_osx(self._sound_file)
        rounds = 0
        while True:
            rounds = rounds + 1
            logging.info("One more round - # %d", rounds)
            notifier.send_to_telegram("Round - {0}".format(rounds))
            self.run_once()
            time.sleep(self.wait_time)

    # stolen from https://github.com/JaDogg/pydoro/blob/develop/pydoro/pydoro_core/sound.py
    @staticmethod
    def _play_sound_osx(sound, block=True):
        """
        Utilizes AppKit.NSSound. Tested and known to work with MP3 and WAVE on
        OS X 10.11 with Python 2.7. Probably works with anything QuickTime supports.
        Probably works on OS X 10.5 and newer. Probably works with all versions of
        Python.
        Inspired by (but not copied from) Aaron's Stack Overflow answer here:
        http://stackoverflow.com/a/34568298/901641
        I never would have tried using AppKit.NSSound without seeing his code.
        """
        from AppKit import NSSound
        from Foundation import NSURL
        from time import sleep

        logging.info("Play sound")
        if "://" not in sound:
            if not sound.startswith("/"):
                from os import getcwd

                sound = getcwd() + "/" + sound
            sound = "file://" + sound
        url = NSURL.URLWithString_(sound)
        ns_sound = NSSound.alloc().initWithContentsOfURL_byReference_(url, True)
        if not ns_sound:
            raise IOError("Unable to load sound named: " + sound)
        ns_sound.play()

        if block:
            sleep(ns_sound.duration())


if __name__ == "__main__":
    try:
        BerlinBot().run_loop()
    except BaseException as error:
        notifier.send_to_telegram("⬅️ 💀💀💀 Exception occurred - {0}".format(str(error)))
        logging.error("Exception occurred - %s , trace=%s", error, traceback.format_exc())
