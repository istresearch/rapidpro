from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst, ignoreDjangoModelAttrs
from engage.utils.class_overrides import MonkeyPatcher

from temba.utils.export import BaseExportTask

# class BaseExportTaskOverrides(ClassOverrideMixinMustBeFirst, BaseExportTask):
#     override_ignore = ignoreDjangoModelAttrs(BaseExportTask)
#
#     # we do not want Django to perform any magic inheritance
#     class Meta:
#         abstract = True
#
#     @classmethod
#     def get_recent_unfinished(cls, org):
#         """
#         Checks for unfinished exports created recently for this org, and returns the most recent
#         """
#         recent_hours = settings.EXPORT_TASK_CHECK_HOURS if hasattr(settings, 'EXPORT_TASK_CHECK_HOURS') else 4
#         recent_past = timezone.now() - timedelta(hours=recent_hours)
#         return cls.getSuperClass().get_unfinished().filter(org=org, created_on__gt=recent_past).order_by("created_on").last()
#     #enddef get_recent_unfinished
#
# #endclass BaseExportTaskOverrides

class BaseExportTaskOverrides(MonkeyPatcher):
    _patch_class: BaseExportTask

    @classmethod
    def get_recent_unfinished(cls: type(BaseExportTask), org):
        """
        Checks for unfinished exports created recently for this org, and returns the most recent
        """
        recent_hours = settings.EXPORT_TASK_CHECK_HOURS if hasattr(settings, 'EXPORT_TASK_CHECK_HOURS') else 4
        recent_past = timezone.now() - timedelta(hours=recent_hours)
        return cls.get_unfinished().filter(org=org, created_on__gt=recent_past).order_by("created_on").last()
    #enddef get_recent_unfinished

#endclass BaseExportTaskOverrides
