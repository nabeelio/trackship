#
from trackship.phantomjs import PhantomJS
from trackship.importers.base import BaseImporter


class Importer(BaseImporter):

    def __init__(self):
        super(Importer, self).__init__()
        self.pjs = PhantomJS(user_agent=PhantomJS.USERAGENT_IOS)

    def _login(self):
        pass

    def _get(self):
        pass

    def list_orders(self):
        """
        generate and then download the order report. login with selenium,
        then fill out the order report form, and wait until it's been generated
        """
        pass
