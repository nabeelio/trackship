#
from collections import namedtuple
from trackship.phantomjs import PhantomJS
from selenium.webdriver.support.ui import Select
from trackship.importers.base import BaseImporter

ReportRow = namedtuple('ReportRow', ['date',
                                     'type',
                                     'name',
                                     'status',
                                     'link'])


class Importer(BaseImporter):

    __ORDER_LINK__ = 'https://www.amazon.com/gp/b2b/reports'

    def __init__(self, pjs=None):
        super(Importer, self).__init__()

        if pjs:
            self.pjs = pjs
        else:
            self.pjs = PhantomJS(user_agent=PhantomJS.USERAGENT_IOS)

        self.email = self.conf['amazon']['email']
        self.password = self.conf['amazon']['password']

    def _need_sign_in(self):
        if any(('Amazon Sign In' in self.pjs.title,
                'Amazon.com Sign In' in self.pjs.title)):
            return True

        return False

    def _login(self):
        """ login to amazon """
        try:
            self.pjs.fill_form(
                ('ap_email', self.email),
                ('ap_password', self.password)
            )

            self.pjs.screenshot('post-enter.png')
            if self._need_sign_in():
                print('Well... looks like the login didn\'t work')

        except Exception as e:
            print(e)
            return False

        return True

    def _get(self, url):
        """ load up a URL"""
        self.pjs.get(url)
        if self._need_sign_in():
            self._login()

        self.pjs.screenshot('screen2.png')
        print('')

    def _get_report(self, report_date=None, report_name=None):
        try:
            table = self.pjs.find_element(
                # '//*[@id="divsinglecolumnminwidth"]/div[8]/div/div/table'
                '//*[@id="divsinglecolumnminwidth"]/div[8]/div/div/table/tbody'
            )

            # iterate through every row in the reports table
            tr = table.find_elements_by_tag_name('tr')
            if not tr:
                return

            for row in tr:
                # go through all the columns to figure out which report we wants
                cols = row.find_elements_by_tag_name('td')
                if not cols:
                    continue

                _, date, rpt_type, _, rpt_name, status, dl = cols

                date = date.text.strip()
                rpt_name = rpt_name.text.strip()

                if report_date and report_date != date:
                    return None

                if report_name and rpt_name != report_name:
                    return None

                return ReportRow(date=date.text.strip(),
                                 type=rpt_type.text.strip(),
                                 name=rpt_name.text.strip(),
                                 status=status.text.strip(),
                                 link=dl)
        except Exception as e:
            print(e)

    def list_orders(self):
        """
        generate and then download the order report. login with selenium,
        then fill out the order report form, and wait until it's been generated
        """
        try:
            self._get(self.__ORDER_LINK__)
            print(self.pjs.page_source)
        except Exception as e:
            print (e)

        # set the fields now to pull a report from the last 30 days...

        print('orders')
