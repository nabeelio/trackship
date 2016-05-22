#

from trackship import config
from trackship.phantomjs import PhantomJS


class BaseImporter(object):
    def __init__(self):
        self.conf = config

    def list_orders(self):
        raise NotImplemented()
