import logging
import os
import sys
from platform import system

from dotenv import load_dotenv
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from common import custom_webdriver
from common.common_util import send_success_message, find_by_xpath, count_by_xpath, sleep, select_dropdown, \
    init_logger

url = "https://otv.verwalt-berlin.de/ams/TerminBuchen"
bot_name = "lea_berlin_bot"
success_message = "✅ possible AUSLANDERHORDE APPOINTMENT found. Please hurry to book your appointment by selecting first available time and captcha."


class BerlinBot:
    def __init__(self):
        self._driver = custom_webdriver.WebDriver(bot_name).__enter__()
        self._bot_name = bot_name

    def find_appointment(self):
        rounds = 0
        while True:
            rounds = rounds + 1
            self.fill_search_form(rounds)
            sleep(2)

    def fill_search_form(self, rounds=0):
        logging.info("Round - # %d, SessionId=%s", rounds, self._driver.session_id)
        self.enter_start_page()
        self.tick_off_agreement()
        self.enter_form()

        # retry submit
        for i in range(1,10):
            sleep(2)

            count = self.visa_extension_button_count()
            if count > 3:
                logging.error("Duplicate button found, count=%d, restarting..", count)
                raise Exception("Duplicate button found, count=%d", count)

            if self.is_error_message("späteren Zeitpunkt"):
                logging.warning("Got message - Try again later, retrying..")
            elif self.is_error_message("beendet") or self.is_page_contains_text():
                logging.warning("Session closed message found, retrying..")
                raise Exception("Session closed message found")
            elif self.is_error_message("keine Termine frei"):
                logging.warning("No appointment available, retrying..")
            elif self.is_success():
                send_success_message(self._driver, bot_name, success_message)
                break
            logging.warning("Retry submitting form - # %d ", i)
            self.enter_form()

    def enter_form(self):
        self.wait_for_mainform()
        logging.info("Fill out form")
        nationality = os.environ.get("LEA_NATIONALITY")
        num_of_person = os.environ.get("LEA_NUMBER_OF_PERSON")
        family_living_in_berlin = os.environ.get("LEA_LIVING_IN_BERLIN")
        family_nationality = os.environ.get("LEA_NATIONALITY_OF_FAMILY_MEMBERS")
        visa_category = os.environ.get("LEA_VISA_CATEGORY")
        family_reason_category = os.environ.get("LEA_FAMILY_REASON_CATEGORY")
        family_reason = os.environ.get("LEA_FAMILY_REASON")

        try:
            # Citizenship = Indien
            select_dropdown(self._driver, By.ID, 'xi-sel-400', nationality)
            # number of person
            select_dropdown(self._driver, By.ID, 'xi-sel-422', num_of_person)
            # Living with family member?
            select_dropdown(self._driver, By.ID, 'xi-sel-427', family_living_in_berlin)
            # Family member Citizenship = Indien
            select_dropdown(self._driver, By.ID, 'xi-sel-428', family_nationality)
            sleep(1)

            self.restart_if_duplicate_buttons_found()

            # extend residence permit
            self.click_by_xpath("Selecting - visa category", By.XPATH,
                                '//*[contains(text(),"' + visa_category + '")]')

            # family reasons
            # driver.find_element(By.XPATH,
            #                     '//*[contains(text(), "'+family_reason_category+'")]/preceding-sibling::input').click()
            self.click_by_xpath("Clicking - family reasons", By.XPATH,
                                '//*[@id="inner-436-0-2"]/div/div[5]/label/p')

            # Residence permit for spouses, parents and children of foreign family members (§§ 29-34)
            # self.click_by_xpath(self._driver,"Selecting - family reason = "+family_reason, By.XPATH,
            #                 '//*[contains(text(),"'+family_reason+'")]')
            self.click_by_xpath("Selecting - Residence permit for spouses, "
                                "parents and children of foreign family members (§§ 29-34)", By.XPATH,
                                '//*[@id="inner-436-0-2"]/div/div[6]/div/div[3]/label')

            # submit form
            self.submit_form("Form Submit.", By.ID, 'applicationForm:managedForm:proceed')

        except TimeoutException as toe:
            raise Exception("TimeoutException occurred - {0}".format(toe.msg))
        except Exception as exp:
            raise Exception("Exception occurred - {0}".format(exp) )

    def wait_for_mainform(self):
        while not self.is_page_contains_text("Angaben zum Anliegen"):
            sleep(1)

    def click_by_xpath(self, element_name, selector_type, selector):
        for i in range(3):
            try:
                WebDriverWait(self._driver, 10).until(EC.element_to_be_clickable((selector_type, selector))).click()
                break
            except Exception as ex:
                logging.warning("%s, retry=%d, (%s)", str(ex.__cause__), i, element_name)

    def submit_form(self, element_name, selector_type, selector):
        logging.info(element_name)
        if self.is_success():
            send_success_message(self._driver, bot_name, success_message)
        else:
            self.click_by_xpath(element_name, selector_type, selector)

    def enter_start_page(self):
        logging.info("Visit start page")
        self._driver.get(url)
        while find_by_xpath(self._driver, "//*[contains(text(),'500 - Internal Server Error')]", 0):
            logging.error("Page error - 500 - Internal Server Error")
            sleep(1)
            self._driver.refresh()
        self.click_by_xpath("Start page", By.XPATH,
                            '//*[@id="mainForm"]/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/a')

    def is_success(self):
        return (not self.is_page_contains_text("applicationForm:managedForm:proceed")
                and not self.is_page_contains_text("messagesBox")
                and self.is_visa_extension_button_not_found()
                and not self.is_page_contains_text("recaptcha"))

    def tick_off_agreement(self):
        logging.info("Ticking off agreement")
        self.click_by_xpath("Select agreement", By.XPATH,
                            '//*[@id="xi-div-1"]/div[4]/label[2]/p')
        self.click_by_xpath("Submit button", By.ID, 'applicationForm:managedForm:proceed')

    def restart(self, reason):
        logging.warning("Driver exit for restart")
        self._driver.__exit__(None, None, None)
        raise Exception("restart due to: "+reason)

    def is_visa_extension_button_not_found(self):
        return self.visa_extension_button_count() == 0

    def visa_extension_button_count(self):
        return len(count_by_xpath(self._driver, '//*[contains(text(),"' + os.environ.get("LEA_VISA_CATEGORY") + '")]'))

    def restart_if_duplicate_buttons_found(self):
        if self.visa_extension_button_count() > 3:
            self.restart("duplicate buttons found")

    def is_error_message(self, message):
        try:
            return find_by_xpath(self._driver,
                                 '//*[@id="messagesBox"]/ul/li[contains(text(), "' + message + '")]')
        except NoSuchElementException as exception:
            logging.warning("%s", str(exception.msg))
            return False

    def is_page_contains_text(self, text):
        try:
            return text in custom_webdriver.get_page_source(self._driver)
        except Exception as ex:
            logging.warning("%s", str(ex))
            return False

    @property
    def driver(self):
        return self._driver


if __name__ == "__main__":
    try:
        sys.tracebacklimit = 0
        system = system()
        load_dotenv()
        init_logger('LEA')
        BerlinBot().find_appointment()
    except BaseException as e:
        logging.exception("Exception occurred, message= {0}".format(e))
        BerlinBot().find_appointment()
