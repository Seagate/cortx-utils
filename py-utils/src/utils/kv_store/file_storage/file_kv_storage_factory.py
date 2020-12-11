

class FileKvStorageFactory:
    """
    Implements a common file_storage to represent Json, Toml, Yaml, Ini Doc.
    """

    def __init__(self, file_path):
        self._file_path = file_path
        # Mapping of file extensions and doc classes.
        self._MAP = {
            "json": Json, "toml": Toml, "yaml": Yaml,
            "ini": Ini, "yml": Yaml, "txt": Text
        }
        self._doc = self.get_doc_type()

    def get_doc_type(self):
        """
        Get mapped doc class object bases on file extension
        """
        try:
            extension = os.path.splitext(self._file_path)[1][1:].strip().lower()
            """
            The below if statement is just for temporary purpose to handle
            serial number fie that has no extension to it.
            In future the file will be moved to JSON with key, value pair and
            the below check will be removed.
            """
            if not extension:
                extension = "txt"
            doc_obj = self._MAP[extension]
            return doc_obj(self._file_path)
        except KeyError as error:
            raise KeyError(f"Unsupported file type:{error}")
        except Exception as e:
            raise Exception(f"Unable to read file {self._file_path}. {e}")

    def load(self):
        ''' Loads data from file of given format'''
        return self._doc._load()

    def dump(self, data):
        ''' Dump the data to desired file or to the source '''
        self._doc._dump(data)
