
from trackship import config

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class PhantomJS(object):

    USERAGENT_IOS = ("Mozilla/5.0 (iPhone; CPU iPhone OS 8_1_2 like Mac OS X) "
                     "AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 "
                     "Mobile/12B440 Safari/600.1.4")

    def __init__(self, user_agent=USERAGENT_IOS):
        """
        Initialize the phantom JS selenium driver
        :return:
        """
        self.conf = config
        self.cookies = None

        # http://phantomjs.org/api/webpage/property/settings.html
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        dcap["phantomjs.page.settings.loadImages"] = False
        dcap["phantomjs.page.settings.userAgent"] = user_agent
        dcap["phantomjs.page.settings.webSecurityEnabled"] = False
        dcap["phantomjs.page.settings.localToRemoteUrlAccessEnabled"] = True

        self.driver = webdriver.PhantomJS(
            desired_capabilities=dcap,
            executable_path=self.conf['general']['phantomjs']
        )

        self.driver.implicitly_wait(30)
        self.driver.set_window_size(1024, 768)

    @property
    def title(self):
        if self.driver:
            return self.driver.title.strip()

    @property
    def page_source(self):
        if self.driver:
            return self.driver.page_source

    def get(self, url):
        if self.driver:
            return self.driver.get(url)

    def find_element(self, xpath):
        element = None
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
        except Exception as e:
            print(e)

        return element

    def fill_form(self, *fields):
        """
        Fill in a form and press enter on last
        :param fields: list of tupules:
            (input_id, value),
            (input_id, value)
        :return:
        """
        elem = None
        for input_id, value in fields:
            elem = self.find_element("//input[@id='{id}']".format(id=input_id))
            elem.send_keys(value)

        self.screenshot('form_filled.png')
        if elem:
            elem.send_keys(Keys.ENTER)

    def screenshot(self, path):
        return self.driver.save_screenshot(path)
