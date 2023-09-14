import logging

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from engage.utils.class_overrides import MonkeyPatcher

from temba.utils import on_transaction_commit

from temba.msgs.models import ExportMessagesTask
from temba.msgs.tasks import export_messages_task
from temba.msgs.views import MsgCRUDL


logger = logging.getLogger()

class MsgExporterOverrides(MonkeyPatcher):
    patch_class = MsgCRUDL.Export
    """
    Export messages override to allow for ASYNC/SYNC behavior.
    """

    def form_valid(self: MsgCRUDL.Export, form):
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
            logger.info("export msgs task created", extra={
                'context': 'export msgs',
                'is_async': 'on' if settings.ASYNC_MESSAGE_EXPORT else 'off',
            })
            if settings.ASYNC_MESSAGE_EXPORT:
                on_transaction_commit(lambda: export_messages_task.delay(export.id))

                if not getattr(settings, "CELERY_ALWAYS_EAGER", False):  # pragma: needs cover
                    logger.info("task running, email when done", extra={
                        'context': 'export msgs',
                        'is_async': 'on',
                    })
                    messages.info(
                        self.request,
                        _("We are preparing your export. We will e-mail you at %s when " "it is ready.")
                        % self.request.user.email,
                    )

                else:
                    logger.info("task complete, email sent, link provided", extra={
                        'context': 'export msgs',
                        'is_async': 'on',
                    })
                    dl_url = reverse("assets.download", kwargs=dict(type="message_export", pk=export.pk))
                    messages.info(
                        self.request,
                        mark_safe(_(f"Export complete, you can find it here: <a href=\"{dl_url}\">{dl_url}</a>"))
                    )
                #fi
            else:
                on_transaction_commit(lambda: export_messages_task.run(export.id))
                logger.info("task complete, link provided", extra={
                    'context': 'export msgs',
                    'is_async': 'off',
                })
                dl_url = reverse("assets.download", kwargs=dict(type="message_export", pk=export.pk))
                messages.info(
                    self.request,
                    mark_safe(_(f"Export complete, you can find it here: <a href=\"{dl_url}\">{dl_url}</a>"))
                )
            #fi
        #fi
        messages.success(self.request, self.derive_success_message())

        if "HTTP_X_PJAX" not in self.request.META:
            return HttpResponseRedirect(self.get_success_url())
        else:  # pragma: no cover
            response = self.render_modal_response(form)
            response["REDIRECT"] = self.get_success_url()
            return response
    #enddef form_valid

#endclass MsgExporterOverrides
