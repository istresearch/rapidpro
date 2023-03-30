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

class SubdirMiddleware:
    """
    Add subdir info to response header
    """
    bUseSubDir = False
    subdir = None

    def __init__(self, get_response=None):
        self.get_response = get_response
        from django.conf import settings
        if hasattr(settings, 'SUB_DIR') and settings.SUB_DIR:
            self.bUseSubdir = True
            self.subdir = settings.SUB_DIR.replace("/", "").replace("\\", "")
        #endif
    #enddef __init__

    def __call__(self, request):
        if self.bUseSubdir:
            request.subdir = self.subdir
        #endif
        return self.get_response(request)
    #enddef __call__

#endclass SubdirMiddleware
