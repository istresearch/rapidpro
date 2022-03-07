from datetime import datetime
from pythonjsonlogger.jsonlogger import JsonFormatter

class CustomJsonFormatter(JsonFormatter):
    """
    Specify our standard log fields.
    @see https://github.com/madzak/python-json-logger
    """
    def add_fields(self, log_record, record, message_dict):
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

class OrgPermLogInfoMixin:
    """
    If the class has the OrgPermMixin, we can also include this Mixin to
    provide a standardized means for logging additional user/org info.
    """

    def withLogInfo(self, extras: dict = None) -> dict:
        """
        log messages should have standardized default args
        :param extras: non-standard extra keys to log
        :return: Returns all the key/values to log as a dict.
        """
        if extras is None:
            extras = {}
        theLogInfo = {}
        theUser = self.get_user()
        if theUser is not None:
            theLogInfo.update({
                'user': theUser.email,
            })
        theOrg = self.derive_org()
        theLogInfo.update({
            'org': theOrg,
            'org_id': theOrg.id,
            'org_uuid': theOrg.uuid,
        })
        if type(extras) is dict:
            theLogInfo.update(extras)
        return theLogInfo
