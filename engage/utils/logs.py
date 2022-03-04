

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
