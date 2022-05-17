import logging

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.http import is_safe_url, urlquote_plus
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from engage.utils.logs import OrgPermLogInfoMixin

from smartmin.views import SmartFormView

from temba.orgs.views import ModalMixin, OrgPermsMixin
from temba.utils import json, on_transaction_commit

from temba.msgs.models import ExportMessagesTask, Label
from temba.msgs.tasks import export_messages_task
from temba.msgs.views import ExportForm

logger = logging.getLogger(__name__)

class Exporter(OrgPermLogInfoMixin, ModalMixin, OrgPermsMixin, SmartFormView):
    """
    Export messages override to allow for ASYNC/SYNC behavior.
    """

    form_class = ExportForm
    submit_button_name = "Export"
    success_url = "@msgs.msg_inbox"

    def derive_label(self):
        # label is either a UUID of a Label instance (36 chars) or a system label type code (1 char)
        label_id = self.request.GET["l"]
        if len(label_id) == 1:
            return label_id, None
        else:
            return None, Label.all_objects.get(org=self.request.user.get_org(), uuid=label_id)

    def get_success_url(self):
        redirect = self.request.GET.get("redirect")
        if redirect and not is_safe_url(redirect, self.request.get_host()):
            redirect = None

        return redirect or reverse("msgs.msg_inbox")

    def form_invalid(self, form):  # pragma: needs cover
        if "_format" in self.request.GET and self.request.GET["_format"] == "json":
            return HttpResponse(
                json.dumps(dict(status="error", errors=form.errors)), content_type="application/json", status=400
            )
        else:
            return super().form_invalid(form)

    def form_valid(self, form):
        user = self.request.user
        org = user.get_org()

        export_all = bool(int(form.cleaned_data["export_all"]))
        groups = form.cleaned_data["groups"]
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]

        system_label, label = (None, None) if export_all else self.derive_label()

        # is there already an export taking place?
        existing = ExportMessagesTask.get_recent_unfinished(org)
        if existing:
            messages.info(
                self.request,
                _(
                    "There is already an export in progress, started by %s. You must wait "
                    "for that export to complete before starting another." % existing.created_by.username
                ),
            )

        # otherwise, off we go
        else:
            export = ExportMessagesTask.create(
                org,
                user,
                system_label=system_label,
                label=label,
                groups=groups,
                start_date=start_date,
                end_date=end_date,
            )
            logger.info("export msgs task created", extra=self.withLogInfo({
                'context': 'export msgs',
                'is_async': 'on' if settings.ASYNC_MESSAGE_EXPORT else 'off',
            }))
            if settings.ASYNC_MESSAGE_EXPORT:
                on_transaction_commit(lambda: export_messages_task.delay(export.id))

                if not getattr(settings, "CELERY_ALWAYS_EAGER", False):  # pragma: needs cover
                    logger.info("task running, email when done", extra=self.withLogInfo({
                        'context': 'export msgs',
                        'is_async': 'on',
                    }))
                    messages.info(
                        self.request,
                        _("We are preparing your export. We will e-mail you at %s when " "it is ready.")
                        % self.request.user.email,
                    )

                else:
                    logger.info("task complete, email sent, link provided", extra=self.withLogInfo({
                        'context': 'export msgs',
                        'is_async': 'on',
                    }))
                    dl_url = reverse("assets.download", kwargs=dict(type="message_export", pk=export.pk))
                    messages.info(
                        self.request,
                        _("Export complete, you can find it here: %s (production users " "will get an email)")
                        % dl_url,
                    )

            else:
                on_transaction_commit(lambda: export_messages_task.run(export.id))
                logger.info("task complete, link provided", extra=self.withLogInfo({
                    'context': 'export msgs',
                    'is_async': 'off',
                }))
                dl_url = reverse("assets.download", kwargs=dict(type="message_export", pk=export.pk))
                messages.info(self.request,
                    mark_safe(_(f"Export complete, you can find it here: <a href=\"{dl_url}\">{dl_url}</a>"))
                )

        messages.success(self.request, self.derive_success_message())

        if "HTTP_X_PJAX" not in self.request.META:
            return HttpResponseRedirect(self.get_success_url())
        else:  # pragma: no cover
            response = self.render_to_response(
                self.get_context_data(
                    form=form,
                    success_url=self.get_success_url(),
                    success_script=getattr(self, "success_script", None),
                )
            )
            response["Temba-Success"] = self.get_success_url()
            response["REDIRECT"] = self.get_success_url()
            return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["label"] = self.derive_label()[1]
        return kwargs
