#

from trackship import config


class BaseImporter(object):

    def __init__(self, importer_name=None):
        self.conf = config
        self.importer_name = importer_name or __name__

    def log(self, method, *args):
        """
        Format log messages with the importer name
        :param method:
        :param args:
        :return:
        """
        for msg in args:
            method('{importer}: {msg}'.format(
                importer=self.importer_name,
                msg=msg
            ))

    def list_orders(self):
        raise NotImplemented()
