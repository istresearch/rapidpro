from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.views.i18n import JavaScriptCatalog

from celery.signals import worker_process_init

from temba.channels.views import register, sync
from temba.utils.analytics import init_analytics

# javascript translation packages
js_info_dict = {"packages": ()}  # this is empty due to the fact that all translation are in one folder

# import our surgical overrides that required all Django apps and __init__.pys processed.
from engage.utils.overrides import EngageOverrides
EngageOverrides.RunEngageOverrides()

VHOST_NAME = ""
SUB_DIR = getattr(settings, 'SUB_DIR', None)
if SUB_DIR is not None and len(SUB_DIR) > 0:
    if settings.SUB_DIR[-1:] == "/":
        VHOST_NAME = SUB_DIR
    else:
        VHOST_NAME = SUB_DIR + "/"

urlpatterns = [
    url(r"^{}".format(VHOST_NAME), include("temba.airtime.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.api.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.apks.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.archives.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.campaigns.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.channels.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.classifiers.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.contacts.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.dashboard.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.flows.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.globals.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.ivr.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.locations.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.msgs.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.orgs.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.policies.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.public.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.request_logs.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.schedules.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.tickets.urls")),
    url(r"^{}".format(VHOST_NAME), include("temba.triggers.urls")),
    url(r"^{}relayers/relayer/sync/(\d+)/$".format(VHOST_NAME), sync, {}, "sync"),
    url(r"^{}relayers/relayer/register/$".format(VHOST_NAME), register, {}, "register"),
    url(r"^{}users/user/forget/".format(VHOST_NAME), RedirectView.as_view(pattern_name="orgs.user_forget", permanent=True)),
    url(r"^{}users/".format(VHOST_NAME), include("smartmin.users.urls")),
    url(r"^{}imports/".format(VHOST_NAME), include("smartmin.csv_imports.urls")),
    url(r"^{}assets/".format(VHOST_NAME), include("temba.assets.urls")),
    url(r"^{}jsi18n/$".format(VHOST_NAME), JavaScriptCatalog.as_view(), js_info_dict, name="django.views.i18n.javascript_catalog"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# import any additional urls
for app in settings.APP_URLS:  # pragma: needs cover
    urlpatterns.append(url(r"^{}".format(VHOST_NAME), include(app)))

# initialize our analytics (the signal below will initialize each worker)
init_analytics()


@worker_process_init.connect
def configure_workers(sender=None, **kwargs):
    init_analytics()  # pragma: needs cover


def handler500(request):
    """
    500 error handler which includes ``request`` in the context.

    Templates: `500.html`
    Context: None
    """
    from django.template import loader
    from django.http import HttpResponseServerError

    t = loader.get_template("500.html")
    return HttpResponseServerError(t.render({"request": request}))  # pragma: needs cover
