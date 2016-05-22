#


class Package(object):

    def __init__(self, name, tracking_id, tracking_service):
        self.name = name
        self._trk_id = tracking_id

        # TODO: Normalize this tracking service name?
        self._trk_svc = tracking_service

    @property
    def id(self):
        return self._trk_id

    @property
    def service(self):
        return self._trk_svc
