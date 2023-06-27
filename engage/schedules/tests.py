import datetime
import pytz

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst

from temba.schedules.models import Schedule
from temba.schedules.tests import ScheduleTest


class ScheduleTestOverrides(ClassOverrideMixinMustBeFirst, ScheduleTest):

    def create_schedule(self, user, repeat_period, repeat_days=(), start_date=None):
        if not start_date:
            # Test date is 10am on a Thursday, Jan 3rd
            start_date = datetime(2013, 1, 3, hour=10, minute=0).replace(tzinfo=pytz.utc)

        # create a bitmask from repeat_days
        bitmask = 0
        for day in repeat_days:
            bitmask += pow(2, (day + 1) % 7)

        return Schedule.create_schedule(start_date, repeat_period, user, bitmask)
    #enddef create_schedule

#endclass ScheduleTestOverrides
