"""
Alternative to overwriting a file with customizations/any is to provide 'surgical overrides' in
the form of methods put into specific classes "after initialization, but before handle-ization".

Import this file just after all the urls in the main urls.py and run its overrides.
"""
from django.conf import settings

def _TrackUser(self):  # pragma: no cover
    """
    Should the current user be tracked
    """
    # track if "is logged in" and not DEV instance
    if self.is_authenticated and not self.is_anonymous and settings.IS_PROD:
        return True
    else:
        return False

def RunEngageOverrides():
    from django.contrib.auth.models import AnonymousUser, User
    User.track_user = _TrackUser
    AnonymousUser.track_user = _TrackUser

    # overwrite a single method of a single class rather then stomp on the whole file
    #   change default behavior of API POST checks so that if an org is "out of credits"
    #   a http status of 451 is returned rather than the usual generic 400.
    #   Life for this override began as its own class for our own API endpoints, but
    #   it will make life simpler if this were just the way all API endpoints returned
    #   such errors.
    from temba.api.v2.serializers import WriteSerializer as TembaWriteSerializer
    from engage.api.serializers import WriteSerializer as EngageWriteSerializer
    setattr(TembaWriteSerializer, 'run_validation', EngageWriteSerializer.run_validation)

    from django.contrib.auth.models import User
    from engage.orgs.models import get_user_orgs
    User.get_user_orgs = get_user_orgs
