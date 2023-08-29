import boto3

from engage.utils.class_overrides import MonkeyPatcher

from temba.archives.models import Archive


class ArchiveOverrides(MonkeyPatcher):
    patch_class = Archive

    @classmethod
    def s3_client(cls):
        # use same code as the currently working api/v2 s3 downloads
        return boto3.client("s3")
    #enddef s3_client

#endclass ArchiveOverrides
