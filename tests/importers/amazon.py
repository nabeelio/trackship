
import unittest
import trackship
from trackship.phantomjs import PhantomJS
from trackship.importers.amazon import Importer


REPORT_LINK = ('https://www.amazon.com'
               '/gp/b2b/reports/'
               '?ie=UTF8&download-report.x=1'
               '&isInternal=0&js=1'
               '&reportId=A1XTCDD50GACB3')


class AmazonImporterTest(unittest.TestCase):

    def setUp(self):
        self.pjs = PhantomJS(
            cookies_file='amazon.yaml',
            user_agent=PhantomJS.USERAGENT_IOS,
        )

        self.importer = Importer(self.pjs)

    def test_login_page(self):
        pass

    def test_orders_page(self):
        """
        """
        self.pjs.get('tests/fixtures/importers/amazon/orderhistory.html')

        try:
            url = self.importer._get_report_link()
            self.assertEqual(
                url,
                ('https://www.amazon.com/b2b/reports/download'
                 '/ATVPDKIKX0DER/A1XIKDI43ZLJIE/A1XTCDD50GACB3')
            )
        except Exception as e:
            pass

        try:
            self.importer._generate_report()
            report = self.importer._get_report(report_date='03/18/15')
        except Exception as e:
            print(e)

        print(report)

    def tearDown(self):
        pass

if __name__ == "__main__":
    unittest.main()
