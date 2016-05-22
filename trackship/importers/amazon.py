#
import time
import arrow
from collections import namedtuple
from trackship.phantomjs import PhantomJS
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

        self.pjs = pjs
        if not self.pjs:
            self.pjs = PhantomJS(cookies_file='amazon.yaml',
                                 user_agent=PhantomJS.USERAGENT_IOS)

        self.logged_in = False
        self.email = self.conf['amazon']['email']
        self.password = self.conf['amazon']['password']

    def _need_sign_in(self):
        """ check the page title to see if we're on a login page """
        if any(('Amazon Sign In' in self.pjs.title,
                'Amazon.com Sign In' in self.pjs.title)):
            return True

        return False

    def _login(self):
        """ login to amazon """
        try:
            self.pjs.fill_form(
                submit=True,
                fields=(('ap_email', self.email),
                        ('ap_password', self.password))
            )

            self.logged_in = True

            if self._need_sign_in():
                self.logged_in = False
                print('Well... looks like the login didn\'t work')

                self.pjs.screenshot('login_no_workie.png')
                return False

            # save the login information...
            else:
                self.pjs.save_cookies()

        except Exception as e:
            print(e)
            return False

        return True

    def _get(self, url):
        """ load up a URL"""
        self.pjs.get(url)
        if self._need_sign_in():
            self._login()

        print('')

    def _get_report(self, report_date=None, report_name=None):
        try:
            table = self.pjs.find_element(
                # '//*[@id="divsinglecolumnminwidth"]/div[8]/div/div/table'
                '//*[@id="divsinglecolumnminwidth"]/div[8]/div/div/table/tbody'
            )

            if not table:
                print('no table')

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

                # get the actual link to the csv report
                dl = dl.find_element_by_tag_name('a')
                if dl:
                    dl = dl.get_attribute('href')

                if report_date and report_date != date:
                    continue

                if report_name and rpt_name != report_name:
                    continue

                return ReportRow(date=date,
                                 name=rpt_name,
                                 type=rpt_type.text.strip(),
                                 status=status.text.strip(),
                                 link=dl,
                                 )
        except Exception as e:
            print(e)

    def _generate_report(self):

        dt = arrow.utcnow()
        dt_last_week = dt.replace(weeks=-1)

        report_name = dt.format()
        report_name_xp = '//*[@id="report-name"]'

        start_month_xp = '//*[@id="report-month-start"]'
        start_day_xp = '//*[@id="report-day-start"]'
        start_year_xp = '//*[@id="report-year-start"]'

        end_month_xp = '//*[@id="report-month-end"]'
        end_day_xp = '//*[@id="report-day-end"]'
        end_year_xp = '//*[@id="report-year-end"]'

        try:
            self.pjs.fill_form(
                submit=True,
                fields=(
                    # go back one week
                    (start_month_xp, dt_last_week.format('MMMM')),
                    (start_day_xp, dt_last_week.format('D')),
                    (start_year_xp, dt_last_week.format('YYYY')),

                    # and end with today
                    (end_month_xp, dt.format('MMMM')),
                    (end_day_xp, dt.format('D')),
                    (end_year_xp, dt.format('YYYY')),

                    # aaand the report name, just with dt
                    (report_name_xp, report_name)
                )
            )
        except Exception as e:
            print(e)

        print(self.pjs.cookies)

        # wait until the report is generated
        # TODO: Max retries
        while True:
            # time.sleep(15)
            self._get(self.__ORDER_LINK__)
            report_link = self._get_report(report_name=report_name)
            if not report_link:
                continue

            # report has finished generating
            if 'complete' in report_link.status.lower():
                self._get(report_link.link)
                print(self.pjs.page_source)
                break
            else:
                time.sleep(5)

            print(report_link)

    def list_orders(self):
        """
        generate and then download the order report. login with selenium,
        then fill out the order report form, and wait until it's been generated
        """
        try:
            self._get(self.__ORDER_LINK__)
            if not self.logged_in:
                print('Could not log in, skipping')
            else:
                report_name = self._generate_report()

            print(self.pjs.page_source)

        except Exception as e:
            print (e)

        # set the fields now to pull a report from the last 30 days...

        print('orders')
