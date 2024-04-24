from django.http import HttpRequest, JsonResponse
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.decorators import renderer_classes
from rest_framework.renderers import JSONRenderer


@renderer_classes((JSONRenderer,))
class PingEndpoint(View):

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    #enddef dispatch

    def get(self, request: HttpRequest):
        try:
            data = {'ping': 'pong'}
            return JsonResponse(data)
        except Exception as ex:
            data = {'error': str(ex)}
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

#endclass PingEndpoint
