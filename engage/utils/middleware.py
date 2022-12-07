from django import shortcuts

class RedirectTo(Exception):
    def __init__(self, url):
        self.url = url

def redirect_to(url):
    raise RedirectTo(url)

class RedirectMiddleware:

    def process_exception(self, request, exception):
        if isinstance(exception, RedirectTo):
            return shortcuts.redirect(exception.url)
        #endif
    #enddef process_exception

#endclass RedirectMiddleware
