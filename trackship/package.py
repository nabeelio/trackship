#


class Package(object):

    def __init__(self,
                 name,
                 source,
                 tracking_id,
                 tracking_service):

        self.name = name
        self.source = source

        self._trk_id = tracking_id
        self._trk_svc = tracking_service

    @property
    def id(self):
        return self._trk_id

    @property
    def service(self):
        return self._trk_svc
