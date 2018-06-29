from django.core.files.storage import DefaultStorage


class PublicFileStorage(DefaultStorage):
    default_acl = "public-read"
    file_overwrite = False


public_file_storage = PublicFileStorage()
public_file_storage.default_acl = "public-read"
