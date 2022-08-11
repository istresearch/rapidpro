from datetime import datetime
from pythonjsonlogger.jsonlogger import JsonFormatter


class CustomJsonFormatter(JsonFormatter):
    """
    Specify our standard log fields.
    @see https://github.com/madzak/python-json-logger
    """

    def add_fields(self, log_record, record, message_dict) -> None:
        """
        ensure all log entries have a minimum set of fields like timestamp and level.
        :param log_record: the custom log structure about to be written out.
        :param record: the well-defined log structure in use.
        :param message_dict: extra map information given to log.
        :return: None
        """
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['name'] = record.name
        if not log_record.get('timestamp'):
            # this doesn't use record.created, so it is slightly off
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname
        log_record['app'] = 'webapp'
    #enddef add_fields

#endclass CustomJsonFormatter

class LogExtrasMixin:
    """
    Helper method to standardize adding extra fields to JSON logs.
    """

    def with_log_extras(self, more_extras: dict = None) -> dict:
        """
        dict.update() returns None, but we want something that returns a dict.
        :param more_extras: a dict with more key/value pairs to add to logs.
        :return: Returns the obj.log_extras + more_extras added to it.
        """
        result = self.log_extras.copy() if hasattr(self, 'log_extras') else {}
        if more_extras is not None and type(more_extras) is dict:
            result.update(more_extras)
        #endif
        return result
    #enddef with_log_extras

#endclass LogExtrasMixin

class OrgPermLogInfoMixin(LogExtrasMixin):
    """
    If the class has the OrgPermMixin, we can also include this Mixin to
    provide a standardized means for logging additional user/org info.
    """

    def withLogInfo(self, more_extras: dict = None) -> dict:
        """
        log messages should have standardized default args
        :param more_extras: non-standard extra keys to log
        :return: Returns all the key/values to log as a dict.
        """
        theLogInfo = self.with_log_extras(more_extras)

        theUser = self.get_user() if hasattr(self, 'get_user') and callable(self.get_user) else None
        if theUser is not None:
            theLogInfo.update({
                'user': theUser.email,
            })
        #endif user info available

        theOrg = self.derive_org() if hasattr(self, 'derive_org') and callable(self.derive_org) else None
        if theOrg is not None:
            theLogInfo.update({
                'org': theOrg,
                'org_id': theOrg.id,
                'org_uuid': theOrg.uuid,
            })
        #endif org info available

        return theLogInfo
    #enddef withLogInfo

#endclass OrgPermLogInfoMixin
