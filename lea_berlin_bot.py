import logging
import os
import traceback

from dotenv import load_dotenv
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from common.common_util import send_success_message, find_by_xpath, count_by_xpath, sleep, select_dropdown, \
    init_logger, is_page_contains_text, handle_unexpected_alert, click_by_xpath, send_error_message, get_wait_time
from common.custom_webdriver import WebDriver

page_url = "https://otv.verwalt-berlin.de/ams/TerminBuchen"
bot_name = "lea_berlin_bot"
success_message = ("✅ possible AUSLANDERHORDE APPOINTMENT found. Please hurry to book your appointment by selecting "
                   "first available time and captcha.")


class BerlinBot:
    def __init__(self):
        self._driver = WebDriver(bot_name).__enter__()
        self._bot_name = bot_name
        self.driver.get(page_url)
        self.driver.minimize_window()
        self.timeout_count = 0

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
        while True:
            sleep(2)
            if self.is_success():
                send_success_message(self.driver, bot_name, success_message)
                return
            elif (self.is_loader_not_visible()
                  and not is_page_contains_text(self.driver, "Auswahl Termin")
                  and is_page_contains_text(self.driver, "Verbleibende Zeit:")
                  and is_page_contains_text(self.driver, "applicationForm:managedForm:proceed")):
                self.submit_form("Form Submit.", By.ID, 'applicationForm:managedForm:proceed')

            handle_unexpected_alert(self.driver)

            self.close_if_additional_dialog_window_found()

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
                return

            if not is_page_contains_text(self.driver, "Verbleibende Zeit:"):
                self.restart_if_required()

            if (self.is_loader_not_visible()
                    and (self.is_error_message("späteren Zeitpunkt") or self.is_error_message("keine Termine frei"))
                    and is_page_contains_text(self.driver, "Verbleibende Zeit:")
                    and is_page_contains_text(self.driver, "applicationForm:managedForm:proceed")):
                self.submit_form("Form Submit.", By.ID, 'applicationForm:managedForm:proceed')

    def is_loader_not_visible(self):
        try:
            # Wait for the loading overlay to disappear
            WebDriverWait(self._driver, 30).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "loading"))
            )
            return True
        except TimeoutException:
            if self.timeout_count > 5:
                raise Exception("Restart due to more timeouts")
            self.timeout_count = self.timeout_count + 1
            return False
        except Exception:
            return False

    def enter_start_page(self):
        logging.info("Visit start page")
        self.driver.get(page_url)
        self.driver.minimize_window()
        while find_by_xpath(self.driver, "//*[contains(text(),'500 - Internal Server Error')]", 0):
            logging.error("Page error - 500 - Internal Server Error")
            sleep(1)
            self.driver.refresh()
        click_by_xpath(self.driver, "Start page", By.XPATH,
                       '//*[@id="mainForm"]/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/a')

    def enter_form(self):
        self.wait_for_main_form()
        logging.info("Fill out form")
        nationality = os.environ.get("LEA_NATIONALITY")
        num_of_person = os.environ.get("LEA_NUMBER_OF_PERSON")
        family_living_in_berlin = os.environ.get("LEA_LIVING_IN_BERLIN")
        family_nationality = os.environ.get("LEA_NATIONALITY_OF_FAMILY_MEMBERS")
        visa_category = os.environ.get("LEA_VISA_CATEGORY")
        sub_category = os.environ.get("LEA_VISA_SUB_CATEGORY")
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
            click_by_xpath(self.driver, "Selecting - Visa category = " + visa_category, By.XPATH,
                           '//*[contains(text(),"' + visa_category + '")]')

            # family reasons
            if sub_category != "":
                click_by_xpath(self.driver, "Selecting - Visa sub-category = " + sub_category, By.XPATH,
                               '//*[contains(text(),"' + sub_category + '")]')

            # Residence permit for spouses, parents and children of foreign family members (§§ 29-34)
            click_by_xpath(self.driver, "Selecting - Visa type = " + visa_type, By.XPATH,
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
            self.print_time_left()
            click_by_xpath(self.driver, element_name, selector_type, selector)

    def wait_for_main_form(self):
        while not is_page_contains_text(self.driver, "Angaben zum Anliegen"):
            self.restart_if_session_closed()
            sleep(3)

    def is_success(self):
        return (self.is_loader_not_visible()
                and is_page_contains_text(self.driver, "Ausgewählte Dienstleistung:")
                and is_page_contains_text(self.driver, "recaptcha")
                and self.is_valid_appointment_time_found())

    def tick_off_agreement(self):
        logging.info("Ticking off agreement")
        click_by_xpath(self.driver, "Select agreement", By.XPATH,
                       '//*[@id="xi-div-1"]/div[4]/label[2]/p')
        click_by_xpath(self.driver, "Submit button", By.ID, 'applicationForm:managedForm:proceed')

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
            send_error_message(self.driver, bot_name, "session closed", 20)
            raise Exception("Session closed message found")

    def is_error_message(self, message, retry=1):
        return is_page_contains_text(self.driver, message)

    def close_if_additional_dialog_window_found(self):
        try:
            # Wait for the form to be present
            additional_dialog_found = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, 'additionalTimeDialog'))
            )

            if additional_dialog_found.is_enabled():
                logging.warning("Got additional dialog: Session ended. Would you like to extend the session?, "
                                "retrying..")
                raise Exception("Got additional dialog: Session ended")
        except TimeoutException:
            pass
        except Exception:
            raise

    @property
    def driver(self):
        return self._driver

    def is_session_closed(self):
        return (is_page_contains_text(self.driver, "Sitzungsende")
                or is_page_contains_text(self.driver, "Fehler ist aufgetreten. Bitte versuchen Sie es zu einem "
                                                      "späteren Zeitpunkt nochmal."))

    def close(self, message):
        logging.exception("Close due to error= {0}".format(message))
        print(traceback.format_exc())
        self.driver.quit()

    def is_valid_appointment_time_found(self):
        try:
            # Wait for the dropdown options to be populated (other than the default option)
            WebDriverWait(self.driver, 10).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, '#xi-sel-3_1')) > 1
            )

            select_element = WebDriverWait(self.driver, 10).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, '#xi-sel-3_1')
            )
            time_value = select_element.get_attribute('value')
            logging.info("FOUND time : %s", time_value)
            return time_value != ""
        except Exception:
            print(traceback.format_exc())

    def print_time_left(self):
        time_to_wait_in_sec = get_wait_time(self._driver, By.XPATH, "//*[@id='progressBar']")
        logging.info("Session time left: %d sec", time_to_wait_in_sec)


if __name__ == "__main__":
    while True:
        berlin_bot = BerlinBot()
        try:
            # sys.tracebacklimit = 0
            load_dotenv()
            init_logger('LEA')
            berlin_bot.find_appointment()
        except BaseException as e:
            berlin_bot.close(str(e))
