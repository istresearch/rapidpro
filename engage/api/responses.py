from django.http import HttpResponse
from rest_framework.status import HTTP_204_NO_CONTENT

class HttpResponseNoContent(HttpResponse):
    """
    Special HTTP response with no content, just headers.
    The content operations are ignored.
    @see https://stackoverflow.com/a/62835865/429728
    """

    def __init__(self, content="", mimetype=None, status=None, content_type=None, headers=None):
        super().__init__(status=HTTP_204_NO_CONTENT if status is None else status, headers=headers)

        if "Content-Type" in self._headers:
            del self._headers["Content-Type"]
        if "content-type" in self._headers:
            del self._headers["content-type"]
    #enddef init

    def _set_content(self, value):
        pass

    def _get_content(self, value):
        pass
