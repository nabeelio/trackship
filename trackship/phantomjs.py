
import os
import yaml
import requests
from trackship import config, LOG
from requests.utils import RequestsCookieJar

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class PhantomJS(object):

    USERAGENT_IOS = ("Mozilla/5.0 (iPhone; CPU iPhone OS 8_1_2 like Mac OS X) "
                     "AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 "
                     "Mobile/12B440 Safari/600.1.4")

    USERAGENT_AMZ = ("Mozilla/4.0 (compatible; Linux 2.6.22) "
                     "NetFront/3.4 Kindle/2.0 (screen 600x800)")

    def __init__(self, user_agent=None, cookies_file=None):
        """
        Initialize the phantom JS selenium driver
        :return:
        """
        self.conf = config
        self.cookies_file = cookies_file

        # http://phantomjs.org/api/webpage/property/settings.html
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        dcap['phantomjs.page.settings.loadImages'] = False
        dcap['phantomjs.page.settings.webSecurityEnabled'] = False
        dcap['phantomjs.page.settings.localToRemoteUrlAccessEnabled'] = True

        if user_agent:
            dcap['phantomjs.page.settings.userAgent'] = user_agent

        self.driver = webdriver.PhantomJS(
            desired_capabilities=dcap,
            executable_path=self.conf['general']['phantomjs'],
        )

        self.load_cookies()

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

    @property
    def cookies(self):
        if self.driver:
            return self.driver.get_cookies()

    def get(self, url):
        if self.driver:
            return self.driver.get(url)

    def load_cookies(self):
        try:
            with open(self.cookies_file, 'r') as f:
                cookies = yaml.load(f)
                for c in cookies:
                    if c['name'] in ('csm-hit',):
                        continue

                    try:
                        self.driver.add_cookie(c)
                    except Exception as e:
                        LOG.exception(e)
                        continue

        except FileNotFoundError:
            pass

    def save_cookies(self):
        with open(self.cookies_file, 'w') as f:
            yaml.dump(self.cookies, f)

    def delete_cookie_file(self):
        try:
            os.remove(self.cookies_file)
        except FileNotFoundError:
            pass

    def download(self, url, file_path=None):
        """ download a file to a certain path """
        cookie_jar = RequestsCookieJar()
        for cookie in self.cookies:
            if 'httponly' in cookie:
                del cookie['httponly']

            if 'expiry' in cookie:
                del cookie['expiry']

            cookie_jar.set(name=cookie['name'],
                           value=cookie['value'],
                           **cookie)

        with requests.Session() as s:
            s.cookies = cookie_jar
            r = s.get(url=url, allow_redirects=True)
            if not file_path:
                return r.content

            # write it out to file...
            # TODO (nshahzad): error handling
            with open(file_path, 'w') as f:
                f.write(r.content)

    def find_element(self, xpath):
        element = None
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
        except Exception as e:
            print(e)

        return element

    def find_elements(self, xpath):
        element = None
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, xpath))
            )
        except Exception as e:
            print(e)

        return element

    def fill_form(self, fields=(), submit=True):
        """
        Fill in a form and press enter on last
        :param fields: list of tupules:
            (input_id, value),
            (input_id, value)
        :return:
        """
        elem = None
        for input_id, value in fields:
            if '//' in input_id:
                find = input_id
            else:
                find = "//input[@id='{id}']".format(id=input_id)

            elem = self.find_element(find)
            if elem.tag_name == 'select':
                select = Select(elem)
                select.select_by_visible_text(value)
            else:
                elem.send_keys(value)

        if elem and submit:
            elem.send_keys(Keys.ENTER)

    def screenshot(self, path):
        return self.driver.save_screenshot(path)
