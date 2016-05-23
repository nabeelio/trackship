#

from trackship import config


class BaseImporter(object):

    def __init__(self):
        self.conf = config

    def list_orders(self):
        raise NotImplemented()
