class Bundle:
    def __init__(self, bundle_id, bundle_path, comment):
        """Initialiases bundle object, which will have support bundle information."""
        self._bundle_id = bundle_id
        self._bundle_path = bundle_path
        self._comment = comment

    @property
    def bundle_id(self):
        return self._bundle_id

    @property
    def bundle_path(self):
        return self._bundle_path

    @property
    def comment(self):
        return self._comment
