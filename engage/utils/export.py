from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from engage.utils.class_overrides import MonkeyPatcher

from temba.utils.export import BaseExportTask

class BaseExportTaskOverrides(MonkeyPatcher):
    patch_class = BaseExportTask

    def get_recent_unfinished(cls: type[BaseExportTask], org):
        """
        Checks for unfinished exports created recently for this org, and returns the most recent
        """
        recent_hours = settings.EXPORT_TASK_CHECK_HOURS if hasattr(settings, 'EXPORT_TASK_CHECK_HOURS') else 4
        recent_past = timezone.now() - timedelta(hours=recent_hours)
        import logging
        logger = logging.getLogger()
        logger.debug('BaseExportTaskOverrides.get_recent_unfinished called', extra={
            'cls': cls,
        })
        return cls.get_unfinished().filter(org=org, created_on__gt=recent_past).order_by("created_on").last()
    #enddef get_recent_unfinished

#endclass BaseExportTaskOverrides
