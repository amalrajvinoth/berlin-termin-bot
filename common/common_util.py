import logging
import os
import time

from selenium.common import NoSuchElementException, ElementClickInterceptedException, TimeoutException
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import notifier
import sound

_sound_file = os.path.join(os.getcwd(), "alarm.wav")


def sleep(seconds=2):
    logging.info("Sleeping for %d seconds", seconds)
    time.sleep(seconds)

def check_exists_by_xpath(driver: webdriver.WebDriver, xpath: str):
    return find_by_xpath(driver, xpath)

def count_by_xpath(driver: webdriver.WebDriver, xpath: str):
    return driver.find_elements(By.XPATH, xpath)

def find_by_xpath(driver: webdriver.WebDriver, xpath: str, retry=3):
    for i in range(retry):
        try:
            return driver.find_element(By.XPATH, xpath)
        except NoSuchElementException as exception:
            logging.warning("%s, retry=%d", str(exception.msg), i)

def click_by_xpath(driver: webdriver.WebDriver, element_name, selector_type, selector):
    for i in range(3):
        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((selector_type, selector))).click()
            break
        except ElementClickInterceptedException as ecie:
            logging.warning("%s, retry=%d, (%s)", str(ecie.msg), i, element_name)
        except TimeoutException as exception:
            logging.warning("%s, retry=%d, (%s)", str(exception.msg), i, element_name)

def select_dropdown(driver: webdriver.WebDriver, selector_type, selector, value):
    for i in range(3):
        try:
            s = Select(driver.find_element(selector_type, selector))
            s.select_by_visible_text(value)
            break
        except Exception as exception:
            logging.warning("%s, retry=%d (%s)", str(exception.__cause__), i, value)

def send_success_message(message):
    logging.info("!!!SUCCESS - do not close the window!!!!")
    notifier.send_to_telegram(message)
    while True:
        sound.play_sound_osx(_sound_file)
        sleep(300)

def wait_and_click_next(time_message, driver, i):
    if time_message in get_page_source(driver):
        driver.back()
        time.sleep(2)
    #logging.info("Try Search - # %d ", i)
    time_to_wait_in_sec = get_wait_time(driver)
    while time_to_wait_in_sec > 0:
        if time_message in get_page_source(driver):
            driver.back()
            time.sleep(2)
        time_to_wait_in_sec = get_wait_time(driver)
        logging.info("# %d - Wait for %d sec", i, time_to_wait_in_sec)
        time.sleep(time_to_wait_in_sec)
        if time_to_wait_in_sec == 0:
            logging.info("Click on Terminsuche wiederholen button")
            driver.find_element(By.XPATH, "//button[text()='Terminsuche wiederholen']").click()

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

def get_wait_time(driver):
    time_to_wait = driver.find_element(By.XPATH, "//*[@id='calculatedSecs']").text
    #logging.info("time_to_wait = %s", time_to_wait)
    time_to_wait_in_sec = int(time_to_wait.split(':')[1])
    return time_to_wait_in_sec
