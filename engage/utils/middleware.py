from django import shortcuts

class RedirectTo(Exception):
    def __init__(self, url):
        self.url = url

def redirect_to(url):
    raise RedirectTo(url)

class RedirectMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, ex):
        if isinstance(ex, RedirectTo):
            return shortcuts.redirect(ex.url)
        #endif
    #enddef process_exception

#endclass RedirectMiddleware
