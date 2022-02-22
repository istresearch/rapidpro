from whitenoise.storage import CompressedManifestStaticFilesStorage
from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
from urllib.parse import unquote, urlsplit


class WhiteNoiseStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """
    Library, framework, and ancestor assets in tests are malformed or missing.
    However, these assets are not used, so we need to ignore them during
    static file processing/compression. the `self.manifest_strict` set to False
    is supposed to handle that for us, however, due to a combination of older
    WhiteNoise middleware (required due to the Python 3.6 we use) and Django
    itself, we need to tweak a few of the methods to ignore malformed/missing
    files.
    """
    def __init__(self, *args, **kwargs):
        self.manifest_strict = False
        super().__init__(*args, **kwargs)

    def post_process(self, *args, **kwargs):
        files = super(ManifestStaticFilesStorage, self).post_process(*args, **kwargs)
        for name, hashed_name, processed in files:
            yield name, hashed_name, processed

    def hashed_name(self, name, content=None, filename=None):
        # `filename` is the name of file to hash if `content` isn't given.
        # `name` is the base name to construct the new hashed filename from.
        parsed_name = urlsplit(unquote(name))
        clean_name = parsed_name.path.strip()
        filename = (filename and urlsplit(unquote(filename)).path.strip()) or clean_name
        if content is None and not self.exists(filename):
            # Handle self.manifest_strict = False since ancestors apparently don't.
            return name
        else:
            return super().hashed_name(name, content, filename)
