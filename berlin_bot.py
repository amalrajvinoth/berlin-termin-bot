import logging
import os
import time
from platform import system
import notifier

from selenium import webdriver
from selenium.webdriver.common.by import By

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
      notifier.send_to_telegram("⬅️ 💀💀💀Quiting program due to {0} = {1} at {2}".format(exc_type, exc_value, exc_tb))
    self._driver.quit()


def get_wait_time(driver):
  time_to_wait = driver.find_element(By.XPATH, "//*[@id='calculatedSecs']").text
  logging.info("time_to_wait = %s", time_to_wait)
  time_to_wait_in_sec = int(time_to_wait.split(':')[1])
  return time_to_wait_in_sec
  
class BerlinBot:
  def __init__(self):
    self.wait_time = 3
    self._sound_file = os.path.join(os.getcwd(), "alarm.wav")
    self._error_message1 = """Leider sind aktuell keine Termine für ihre Auswahl verfügbar."""
    self._error_message2 = """Bitte entschuldigen Sie den Fehler"""
    self._error_message3 = """Zu viele Zugriffe"""
    self._time_message = """00:00 Minuten"""

  def get_page_source(self, driver):
    try:
      return driver.page_source
    except Exception as e:
      logging.error("failed to get page source %s!", e)
      alert_text = driver.switchTo().alert().getText()
      if not alert_text:
        logging.error("failed and alert_text is %s!", alert_text)
        driver.switchTo().alert().accept()
        return driver.page_source
  
  def wait_and_click_next(self, driver, i):
    if self._error_other in self.get_page_source(driver):
      driver.back()
      time.sleep(2)
    logging.info("Try Search - # %d ", i)
    timeToWaitInSec = get_wait_time(driver)
    while timeToWaitInSec > 0:
      if self._error_other in self.get_page_source(driver):
        driver.back()
        time.sleep(2)
      timeToWaitInSec = get_wait_time(driver)
      logging.info("Wait for %d sec", timeToWaitInSec)
      time.sleep(timeToWaitInSec)
      if timeToWaitInSec == 0:
        logging.info("Click on Terminsuche wiederholen button")
        driver.find_element(By.XPATH, "//button[text()='Terminsuche wiederholen']").click()
  
  def _success(self):
    logging.info("!!!SUCCESS - do not close the window!!!!")
    notifier.send_to_telegram("✅*Commitment letter* Appointment found ✅")
    while True:
      self._play_sound_osx(self._sound_file)
      time.sleep(15)
    # todo play something and block the browser
  
  def run_once(self):
    with WebDriver() as driver:
      self.enter_start_page(driver)

      if not self._error_message1 in self.get_page_source(driver) and not self._error_message2 in self.get_page_source(driver) and not self._error_message3 in self.get_page_source(driver):
        self._success()

      logging.info("not found")  
      driver.close()
      
      # # retry submit
      # for i in range(10):
      #   if not self._error_message in self.get_page_source(driver) and not self._error_other in self.get_page_source(driver):
      #     self._success()
      #   self.wait_and_click_next(driver, i)
      # 
  def run_loop(self):
    # play sound to check if it works
    notifier.send_to_telegram("➡️BOT Running for *Commitment letter* Appointment 💡")
    self._play_sound_osx(self._sound_file)
    while True:
      logging.info("One more round")
      self.run_once()
      time.sleep(self.wait_time)
    
  @staticmethod
  def enter_start_page(driver: webdriver.Chrome):
    logging.info("Visit start page")
    driver.get("https://service.berlin.de/dienstleistung/120691/en/")
    driver.find_element(By.XPATH,
                        "//*[contains(text(),'Make an appointment')]").click()
    time.sleep(2)
    
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
    nssound = NSSound.alloc().initWithContentsOfURL_byReference_(url, True)
    if not nssound:
      raise IOError("Unable to load sound named: " + sound)
    nssound.play()

    if block:
      sleep(nssound.duration())


if __name__ == "__main__":
  BerlinBot().run_loop()
