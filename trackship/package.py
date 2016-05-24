#


class Package(object):

    def __init__(self,
                 source,
                 tracking_id,
                 name='',
                 order_status=None,
                 carrier=None):

        self.name = name
        self.source = source
        self.order_status = order_status

        self._trk_id = tracking_id
        self._carrier = carrier

    @property
    def id(self):
        return self._trk_id

    @property
    def service(self):
        return self._carrier
