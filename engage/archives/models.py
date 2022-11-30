import boto3

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst, ignoreDjangoModelAttrs

from temba.archives.models import Archive


class ArchiveOverrides(ClassOverrideMixinMustBeFirst, Archive):
    override_ignore = ignoreDjangoModelAttrs(Archive)

    # we do not want Django to perform any magic inheritance
    class Meta:
        abstract = True

    @classmethod
    def s3_client(cls):
        # use same code as the currently working api/v2 s3 downloads
        return boto3.client("s3")
    #enddef s3_client

#endclass ArchiveOverrides
