#
import os
import re
import csv
import time
import arrow

from trackship import LOG
from trackship.package import Package
from trackship.phantomjs import PhantomJS
from trackship.importers.base import BaseImporter

from collections import namedtuple


ReportRow = namedtuple('ReportRow', ['date',
                                     'type',
                                     'name',
                                     'status',
                                     'download'])


class Importer(BaseImporter):

    __ORDER_LINK__ = 'https://www.amazon.com/gp/b2b/reports'
    __CSV_TOKEN_URL__ = re.compile(
        '^.*window\.location\.href=\"(?P<url>.*)\".*',
        re.IGNORECASE | re.MULTILINE
    )

    __PACKAGE_ID__ = re.compile(
        '(?P<carrier>.*)\((?P<id>.*)\)',
        re.IGNORECASE
    )

    def __init__(self, pjs=None):

        super(Importer, self).__init__('Amazon')

        self.cookies_file = '{b}/amazon_cookies.yaml'.format(
            b=self.conf['general']['tmp_path']
        )

        self.csv_file = '{tmp}/amazon.csv'.format(
            tmp=self.conf['general']['tmp_path']
        )

        self.pjs = pjs
        if not self.pjs:
            self.pjs = PhantomJS(cookies_file=self.cookies_file,
                                 user_agent=PhantomJS.USERAGENT_IOS)

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

        def __try_login__():
            self.pjs.fill_form(
                submit=True,
                fields=(
                    ('ap_email', self.email),
                    ('ap_password', self.password)
                )
            )

        try:

            __try_login__()

            if self._need_sign_in():
                # delete the cookies file and then try logging in again
                self.log(LOG.info, 'Sign-in failed, trying to delete cookies and try again')

                # may be nothing there to delete
                self.pjs.delete_cookie_file()

                __try_login__()

                # still failed, bail out
                if self._need_sign_in():
                    self.log(LOG.error, 'Login failed (captcha?), going to skip this run...')
                    return False

            # save the login information... as cookies
            self.pjs.save_cookies()

        except Exception as e:
            print(e)
            return False

        return True

    def _get(self, url):
        """ load up a URL"""
        self.log(LOG.debug, 'Loading %s' % url)
        self.pjs.get(url)

        # check if we were redirected to a login page
        if self._need_sign_in():
            return self._login()

    def _get_report(self, report_date=None, report_name=None):
        try:
            self._get(self.__ORDER_LINK__)

            table = self.pjs.find_element(
                '//*[@id="divsinglecolumnminwidth"]/div[8]/div/div/table/tbody'
            )

            if not table:
                return

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

                self.log(LOG.debug, 'Checking report "{f}"...'.format(f=rpt_name))

                if report_name and rpt_name != report_name:
                    continue

                # get the actual link to the csv report
                try:
                    dl = dl.find_element_by_tag_name('a')
                except Exception as e:  # not generating yet
                    continue

                if report_date and report_date != date:
                    continue

                self.log(LOG.info, 'Report "%s" was found, yay!' % rpt_name)
                return ReportRow(date=date,
                                 name=rpt_name,
                                 type=rpt_type.text.strip(),
                                 status=status.text.strip(),
                                 download=dl)
        except Exception as e:
            print(e)

    def _get_report_link(self):
        """ we want to find the script that contains the above regex
            it'll be in a script that has the downloadReport fn
        """
        script_xpath = '//*[@id="divsinglecolumnminwidth"]/script'
        scripts = self.pjs.find_elements(script_xpath)
        for script in scripts:
            src = script.get_attribute('outerHTML')
            if 'function downloadReport(reportID)' not in src:
                continue

            lines = src.split('\n')
            for line in lines:
                line = line.strip()
                if not line:  # blank line
                    continue

                # see if the line in this script has the CSV url
                matches = self.__CSV_TOKEN_URL__.match(line)
                if not matches:
                    continue

                url = '{base_url}/{csv_path}'.format(
                    base_url=self.conf['amazon']['url'],
                    csv_path=matches.group('url')
                )

                self.log(LOG.info, 'CSV URL: %s' % url)

                return url

    def _generate_report(self):
        # title the report with the current date/time
        # just generate a report hourly
        dt = arrow.utcnow()
        report_name = dt.format('YYYYMMDD.HH')

        self.log(LOG.info, 'Report name: "%s"' % report_name)

        # ######################################################################
        def __request_report__():
            """ request that an order report be generated """
            # how many weeks back to request the order history
            num_weeks = self.conf['amazon']['order_history_weeks'] or 4

            dt_last_week = dt.replace(weeks=num_weeks * -1)
            report_name_xp = '//*[@id="report-name"]'
            report_type_xp = '//*[@id="report-type"]'

            start_month_xp = '//*[@id="report-month-start"]'
            start_day_xp = '//*[@id="report-day-start"]'
            start_year_xp = '//*[@id="report-year-start"]'

            end_month_xp = '//*[@id="report-month-end"]'
            end_day_xp = '//*[@id="report-day-end"]'
            end_year_xp = '//*[@id="report-year-end"]'

            fields = (
                # orders and shipments type...
                (report_type_xp, 'Orders and shipments'),

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

            self.log(LOG.debug, 'Filling in report fields', fields)

            self.pjs.fill_form(submit=True, fields=fields)

        # ######################################################################

        try:
            # see if the report already exists before trying to generate
            report_link = self._get_report(report_name=report_name)
            if not report_link:
                __request_report__()
        except Exception as e:
            LOG.exception(e)

        # wait until the report is generated
        tries = 0
        retries = 20
        while tries <= retries:

            tries += 1

            LOG.debug('Checking reports page for "{r}"'.format(
                r=report_name
            ))

            report = self._get_report(report_name=report_name)
            if not report:
                continue

            # report has finished generating
            self.log(LOG.debug, 'Amazon: Report "%s" status: "%s"' % (report.name, report.status))

            if 'complete' in report.status.lower():
                # reload the page by clicking on the download link
                # it'll set in JS the link to the actual CSV to forward to
                report.download.click()

                try:
                    # searches the javascript for the window.location and download it
                    csv_link = self._get_report_link()
                    csv = self.pjs.download(csv_link, self.csv_file)
                    return csv
                except Exception as e:
                    LOG.exception(e)
                    break
            else:
                time.sleep(5)

    def _parse_csv(self):
        """
        Parse the CSV file and return a bunch of package objects
        :return:
        """
        packages = []
        skip_first = False
        with open(self.csv_file, 'r') as fp:
            orders = csv.reader(fp)
            for order in orders:
                if not skip_first:
                    skip_first = True
                    continue

                order_id = order[1]
                status = order[13]
                shipping = self.__PACKAGE_ID__.match(order[14] or '')
                if not shipping:
                    continue

                pkg = Package(name=order_id,
                              source='Amazon',
                              order_status=status,
                              tracking_id=shipping.group('id'),
                              carrier=shipping.group('carrier'))

                packages.append(pkg)

        return packages


    def list_orders(self):
        """
        generate and then download the order report. login with selenium,
        then fill out the order report form, and wait until it's been generated
        """
        self.log(LOG.info, 'Listing orders...')

        try:
            if os.path.isfile(self.csv_file):
                mod_time = os.path.getmtime(self.csv_file)
                curr_time = int(time.time())

                # don't consider it stale if it's less than an hour old
                if curr_time - mod_time < (60 * 60):
                    return self._parse_csv()

                # delete the file if it's under an hour old
                else:
                    try:
                        os.remove(self.csv_file)
                    except FileNotFoundError:
                        pass

            if not self._get(self.__ORDER_LINK__):
                self.log(LOG.error, 'Error logging into or loading page')

            csv = self._generate_report()
            return self._parse_csv()
        except Exception as e:
            LOG.exception(e)

        LOG.info('Completed running Amazon importer')
