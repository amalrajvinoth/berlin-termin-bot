import logging
import os
import sys

from dotenv import load_dotenv
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from common.common_util import send_success_message, find_by_xpath, count_by_xpath, sleep, select_dropdown, \
    init_logger, is_page_contains_text, handle_unexpected_alert
from common.custom_webdriver import WebDriver

url = "https://otv.verwalt-berlin.de/ams/TerminBuchen"
bot_name = "lea_berlin_bot"
success_message = "✅ possible AUSLANDERHORDE APPOINTMENT found. Please hurry to book your appointment by selecting first available time and captcha."


class BerlinBot:
    def __init__(self):
        self._driver = WebDriver(bot_name).__enter__()
        self._bot_name = bot_name

    def find_appointment(self):
        rounds = 0
        while True:
            rounds = rounds + 1
            self.fill_search_form(rounds)
            sleep(2)

    def fill_search_form(self, rounds=0):
        logging.info("Round - # %d, SessionId=%s", rounds, self.driver.session_id)
        self.enter_start_page()
        self.tick_off_agreement()
        self.enter_form()

        # retry submit
        for i in range(1, 10):
            sleep(2)
            if self.is_loader_not_visible() and is_page_contains_text(self.driver, "Verbleibende Zeit:"):
                self.submit_form("Form Submit.", By.ID, 'applicationForm:managedForm:proceed')

            handle_unexpected_alert(self.driver)

            if self.is_error_message("späteren Zeitpunkt"):
                logging.warning("Got message - Try again later, retrying..")
            elif self.is_error_message("keine Termine frei"):
                logging.warning("No appointment available, retrying..")
            elif self.is_error_message("Zu viele Zugriffe"):
                logging.warning("Too many hits, restarting..")
                raise
            elif self.is_error_message("Fehler"):
                logging.warning("Fehler from berlin.de, restarting..")
                raise
            elif self.is_success():
                send_success_message(self.driver, bot_name, success_message)
                break

            if not is_page_contains_text(self.driver, "Verbleibende Zeit:"):
                self.restart_if_required()

    def is_loader_not_visible(self):
        try:
            # Wait for the loading overlay to disappear
            WebDriverWait(self._driver, 30).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "loading"))
            )
            return True
        except Exception:
            return False

    def enter_start_page(self):
        logging.info("Visit start page")
        self.driver.get(url)
        while find_by_xpath(self.driver, "//*[contains(text(),'500 - Internal Server Error')]", 0):
            logging.error("Page error - 500 - Internal Server Error")
            sleep(1)
            self.driver.refresh()
        self.click_by_xpath("Start page", By.XPATH,
                            '//*[@id="mainForm"]/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/a')

    def enter_form(self):
        self.wait_for_main_form()
        logging.info("Fill out form")
        nationality = os.environ.get("LEA_NATIONALITY")
        num_of_person = os.environ.get("LEA_NUMBER_OF_PERSON")
        family_living_in_berlin = os.environ.get("LEA_LIVING_IN_BERLIN")
        family_nationality = os.environ.get("LEA_NATIONALITY_OF_FAMILY_MEMBERS")
        visa_category = os.environ.get("LEA_CATEGORY")
        sub_category = os.environ.get("LEA_SUB_CATEGORY")
        visa_type = os.environ.get("LEA_VISA_TYPE")

        try:
            # Citizenship = Indien
            select_dropdown(self.driver, By.ID, 'xi-sel-400', nationality)
            # number of person
            select_dropdown(self.driver, By.ID, 'xi-sel-422', num_of_person)
            # Living with family member?
            select_dropdown(self.driver, By.ID, 'xi-sel-427', family_living_in_berlin)
            sleep(1)
            # Family member Citizenship = Indien
            select_dropdown(self.driver, By.ID, 'xi-sel-428', family_nationality)
            sleep(1)

            self.restart_if_required()

            # extend residence permit
            self.click_by_xpath("Selecting - visa category = " + visa_category, By.XPATH,
                                '//*[contains(text(),"' + visa_category + '")]')

            # family reasons
            if sub_category != "":
                self.click_by_xpath("Selecting - visa sub-category = " + sub_category, By.XPATH,
                                    '//*[contains(text(),"' + sub_category + '")]')

            # Residence permit for spouses, parents and children of foreign family members (§§ 29-34)
            self.click_by_xpath("Selecting - visa type = " + visa_type, By.XPATH,
                                '//*[contains(text(),"' + visa_type + '")]')

            self.restart_if_required()

        except TimeoutException as toe:
            raise Exception("TimeoutException - {0}".format(toe.msg))
        except Exception as exp:
            raise Exception(exp)

    def submit_form(self, element_name, selector_type, selector):
        if self.is_success():
            send_success_message(self.driver, bot_name, success_message)
        else:
            self.click_by_xpath(element_name, selector_type, selector)

    def wait_for_main_form(self):
        while not is_page_contains_text(self.driver, "Angaben zum Anliegen"):
            if self.is_session_closed():
                raise Exception("Session closed")
            sleep(1)

    def click_by_xpath(self, element_name, selector_type, selector):
        for i in range(10):
            try:
                #logging.info(element_name)
                element = WebDriverWait(self.driver, 60, 2).until(
                    EC.presence_of_element_located((selector_type, selector))
                )
                element.click()
                break
            except Exception as ex:
                logging.warning("%s, retry=%d, (%s)", str(ex), i, element_name)
                if i == 9:
                    raise

    def is_success(self):
        return (not is_page_contains_text(self._driver, "applicationForm:managedForm:proceed")
                and not is_page_contains_text(self._driver,"messagesBox")
                and self.is_visa_extension_button_not_found()
                and not is_page_contains_text(self.driver, "recaptcha"))

    def tick_off_agreement(self):
        logging.info("Ticking off agreement")
        self.click_by_xpath("Select agreement", By.XPATH,
                            '//*[@id="xi-div-1"]/div[4]/label[2]/p')
        self.click_by_xpath("Submit button", By.ID, 'applicationForm:managedForm:proceed')

    def is_visa_extension_button_not_found(self):
        return self.visa_extension_button_count() == 0

    def visa_extension_button_count(self):
        return len(count_by_xpath(self.driver, '//*[contains(text(),"' + os.environ.get("LEA_VISA_CATEGORY") + '")]'))

    def restart_if_required(self):
        self.restart_if_duplicate_buttons_found()
        self.restart_if_session_closed()

    def restart_if_duplicate_buttons_found(self):
        count = self.visa_extension_button_count()
        if count > 3:
            logging.error("Duplicate button found, count=%d, restarting..", count)
            raise Exception("Duplicate buttons found")

    def restart_if_session_closed(self):
        if self.is_session_closed():
            logging.warning("Session closed message found, retrying..")
            raise Exception("Session closed message found")

    def is_error_message(self, message, retry=1):
        return is_page_contains_text(self.driver, message)

    @property
    def driver(self):
        return self._driver

    def is_session_closed(self):
        return is_page_contains_text(self.driver, "Sitzungsende")

    def close(self, message):
        logging.exception("Close due to error= {0}".format(message))
        self.driver.quit()


if __name__ == "__main__":
    while True:
        berlin_bot = BerlinBot()
        try:
            #sys.tracebacklimit = 0
            load_dotenv()
            init_logger('LEA')
            berlin_bot.find_appointment()
        except BaseException as e:
            berlin_bot.close(str(e))
