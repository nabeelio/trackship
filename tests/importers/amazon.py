
import unittest

import trackship
from trackship.phantomjs import PhantomJS
from trackship.importers.amazon import Importer


class AmazonImporterTest(unittest.TestCase):

    def setUp(self):
        self.pjs = PhantomJS()
        self.importer = Importer(self.pjs)

    def test_login_page(self):
        pass

    def test_orders_page(self):
        """
        """
        self.pjs.get('tests/fixtures/importers/amazon/orderhistory.html')

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
