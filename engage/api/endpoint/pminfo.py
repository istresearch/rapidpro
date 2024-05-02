from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.decorators import renderer_classes
from rest_framework.renderers import JSONRenderer

from engage.channels.types.postmaster.schemes import PM_CHANNEL_MODES


@renderer_classes((JSONRenderer,))
class PmInfoEndpoint(View):

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    #enddef dispatch

    def get(self, request: HttpRequest):
        try:
            mode_data = { mode: { 'scheme': x.scheme, 'name': x.urn_name, } for mode, x in PM_CHANNEL_MODES.items() }
            data = {
                'version': settings.DEFAULT_BRAND_OBJ['version'],
                'supported_modes': mode_data,
                'error': None,
            }
            return JsonResponse(data)
        except Exception as ex:
            data = {
                'version': settings.DEFAULT_BRAND_OBJ['version'],
                'error': str(ex),
            }
            return JsonResponse(data, status=status.HTTP_400_BAD_REQUEST)
        #endtry
    #enddef get

    def post(self, request: HttpRequest, *args, **kwargs):
        response = self.get(request)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = "application/json"
        response.renderer_context = {}
        return response
    #enddef post

#endclass PmSchemesEndpoint
