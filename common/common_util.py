import logging
import os
import re
import time
from datetime import datetime, timedelta

import coloredlogs
from selenium.common import NoSuchElementException, ElementClickInterceptedException, TimeoutException
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from common import notifier, sound

_sound_file = os.path.join(os.getcwd(), "alarm.wav")
path = os.path.expanduser('~') + '/Downloads/'


def sleep(seconds=2):
    logging.info("Sleeping for %d seconds", seconds)
    time.sleep(seconds)


def is_page_contains_text(driver, text):
    try:
        return text in get_page_source(driver)
    except Exception as ex:
        logging.warning("%s", str(ex))
        return False


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


def click_by_xpath(driver: webdriver.WebDriver, element_name, selector_type, selector, retry=3):
    for i in range(retry):
        try:
            logging.info("Try Clicking on: %s", element_name)
            elements = driver.find_elements(selector_type, selector)
            for element in elements:
                WebDriverWait(driver, 60).until(
                    EC.element_to_be_clickable((selector_type, selector)))
                driver.execute_script("arguments[0].click();", element)
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


def send_success_message(driver, bot_name, message, wait=300):
    logging.info("!!!SUCCESS - do not close the window!!!!")
    driver.maximize_window()
    save_screenshot(driver, bot_name)
    # notifier.send_to_telegram(termin_name + ' : '+message)
    for _ in range(3):
        notifier.send_photo_to_telegram(message, photo_path=path + bot_name + '_' + driver.session_id + '.png')
    while True:
        sound.play_sound_osx(_sound_file)
        sleep(wait)


def send_error_message(driver, bot_name, message, wait=300):
    logging.error("!!!ERROR - = %s !!!!", message)
    # save_screenshot(driver, bot_name)
    # notifier.send_to_telegram(termin_name + ' : '+message)
    # notifier.send_photo_to_telegram(message, photo_path=path + bot_name + '_' + driver.session_id + '.png')
    sleep(wait)


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


def save_screenshot(driver, bot_name):
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.TAG_NAME, 'body').size['height'] > 0
        )

        element = WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.TAG_NAME, 'body')
        )
        element.screenshot(path + bot_name + '_' + driver.session_id + '.png')
    except Exception as ex:
        logging.warning(ex)
        pass


def init_logger(default_name):
    name = get_bot_name(default_name)
    logging.addLevelName(35, "SUCCESS")
    if not os.getenv('COLOREDLOGS_LOG_FORMAT'):
        styles = dict(
            spam=dict(color='green', faint=True),
            debug=dict(color='green'),
            verbose=dict(color='blue'),
            info=dict(),
            notice=dict(color='magenta'),
            warning=dict(color='yellow'),
            success=dict(background='green', color='white', bold=True),
            error=dict(background='red'),
            critical=dict(color='red', bold=True),
        )

        fields_styles = dict(
            levelname=dict(color='green', bold=True, faint=True),
            asctime=dict(color='green', faint=True),
            name=dict(color='green', bold=True)
        )
        coloredlogs.install(fmt='%(asctime)s.%(msecs)03d ' + name + ' - %(levelname)s %(message)s', level_styles=styles,
                            field_styles=fields_styles)
    else:
        coloredlogs.install()


def get_bot_name(default_name):
    pattern = re.compile(r'\(.+\)')
    visa_sub_category = os.environ.get("LEA_VISA_TYPE")
    if len(visa_sub_category) > 0:
        category = pattern.findall(visa_sub_category)[0]
        if not os.getenv('BOT_NAME'):
            return default_name + "|" + category
        return os.getenv('BOT_NAME') + category
    words = visa_sub_category.split()
    if not words:
        return None  # Handle empty sentence
    return words[-1]


def get_next_date(days_to_add=1):
    current_date = datetime.now()
    # Add one day to the current date
    next_day = current_date + timedelta(days_to_add)
    # Format the date as desired (e.g., DD-MM-YYYY)
    return next_day.strftime('%d.%m.%Y')


def handle_unexpected_alert(driver):
    try:
        # Wait for the alert to be present
        WebDriverWait(driver, 10).until(EC.alert_is_present())

        # Switch to the alert
        alert = driver.switch_to.alert

        # Print the alert text (optional)
        print(f"Alert text: {alert.text}")

        # Accept the alert
        alert.accept()

        # If you need to dismiss the alert, use:
        # alert.dismiss()

    except TimeoutException as e:
        pass
        # logging.warning(f"Unexpected alert present: {e}")
        # send_error_message(driver, "LEA"+get_bot_name('-'), str(e), 5)


def get_wait_time(driver, selector_type, selector):
    try:
        time_left = WebDriverWait(driver, 10).until(
            lambda d: d.find_element(selector_type, selector)
        )
        if time_left.is_displayed():
            time_to_wait = time_left.text
            if time_to_wait.strip() == "":
                return 0
            logging.info("Wait time displayed = %s Minutes", time_to_wait)
            time_to_wait_in_sec = int(time_to_wait.split(':')[0]) * 60 + int(time_to_wait.split(':')[1])
            return time_to_wait_in_sec
        else:
            return -1
    except Exception as ex:
        logging.warning(ex)
        return -1


if __name__ == "__main__":
    print(get_bot_name("D"))
