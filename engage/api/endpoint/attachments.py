import base64
import hashlib
import hmac
import json
import time

from boto3 import client as botoclient
from botocore.exceptions import ClientError

from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from django.conf import settings
from django.utils.encoding import force_bytes
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

from temba.channels.models import Channel


class AttachmentsEndpoint(View):
    """
    This endpoint allows you to request a signed S3 URL for attachment uploads.

    ## Requesting a Signed S3 URL

    Make a `POST` request to the endpoint with a `path` parameter specifying the file path, and an `acl` parameter specifying an S3 canned ACL (optional; default: `public-read`).
    """

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    #enddef dispatch

    def post(self, request, format=None, *args, **kwargs):
        response = self.handle(request)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = "application/json"
        response.renderer_context = {}
        return response
    #enddef post

    def handle(self, request):
        try:
            req_body = force_bytes(request.body)
            req_data = json.loads(req_body)

            path = req_data.get("path")
            acl = req_data.get("acl", "public-read")

            channel_id = request.GET.get("cid")
            channel_uuid = request.GET.get("uuid")
            request_time = request.GET.get("ts")
            request_signature = force_bytes(request.GET.get("signature"))

            bucket = settings.AWS_STORAGE_BUCKET_NAME
            expires = settings.AWS_SIGNED_URL_DURATION

            channels = None
            if channel_uuid is not None:
                channels = Channel.objects.filter(uuid=channel_uuid, is_active=True)
            elif channel_id is not None:
                channels = Channel.objects.filter(pk=channel_id, is_active=True)
            if not channels:
                raise Exception("Invalid channel")
            channel = channels[0]
            if not channel.secret or not channel.org:
                raise Exception("Invalid channel metadata")
            now = time.time()
            if abs(now - int(request_time)) > 60 * 15:
                raise Exception("Invalid timestamp")

            signature = hmac.new(key=force_bytes(str(channel.secret + request_time)), msg=req_body, digestmod=hashlib.sha256).digest()
            signature = base64.urlsafe_b64encode(signature).strip()

            if request_signature != signature:
                raise Exception("Invalid signature")

            if not path:
                raise Exception("Required attribute 'path' not specified")

        except Exception as e:
            data = {'error': str(e)}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = botoclient('s3')
            data = client.generate_presigned_post(bucket, path, Conditions=[{"acl": acl}], ExpiresIn=expires)
            return Response(data, status=status.HTTP_200_OK)
        except ClientError as e:
            data = {'error': str(e)}

        return Response(data, status=status.HTTP_400_BAD_REQUEST)
    #enddef handle

#endclass AttachmentsEndpoint
