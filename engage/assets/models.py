from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.text import slugify

from engage.utils.class_overrides import MonkeyPatcher

from temba.assets.models import BaseAssetStore, AssetAccessDenied, AssetFileNotFound


class BaseAssetStorePatcher(MonkeyPatcher):
    patch_class = BaseAssetStore

    def resolve(self: type(BaseAssetStore), user, pk) -> tuple:
        """
        Returns a tuple of the asset object, location and download filename of the identified asset. If user does not
        have access to the asset, an exception is raised.
        """
        asset = self.derive_asset(pk)

        if not user.has_org_perm(asset.org, self.permission):  # pragma: needs cover
            raise AssetAccessDenied()

        if not self.is_asset_ready(asset):
            raise AssetFileNotFound()

        path = self.derive_path(asset.org, asset.uuid)

        if not default_storage.exists(path):  # pragma: needs cover
            raise AssetFileNotFound()

        # create a more friendly download filename
        remainder, extension = path.rsplit(".", 1)
        filename = f"{self.key}_{pk}_{slugify(asset.org.name)}.{extension}"

        # if our storage backend is S3
        if settings.DEFAULT_FILE_STORAGE == "storages.backends.s3boto3.S3Boto3Storage":  # pragma: needs cover
            # using the "save/restore" route in case the default changes back to True
            save_val = default_storage.querystring_auth
            # force signed URL result to avoid error with using the 'response-content-disposition' header:
            # "Request specific response headers cannot be used for anonymous GET requests."
            default_storage.querystring_auth = True
            url = default_storage.url(
                path, parameters=dict(ResponseContentDisposition=f"attachment;filename={filename}"), http_method="GET"
            )
            default_storage.querystring_auth = save_val
        #endif using s3

        # otherwise, let the backend generate the URL
        else:
            url = default_storage.url(path)

        return asset, url, filename
    #enddef resolve

#endclass BaseAssetStorePatcher
