# let us use CLI args instead of ENV vars for password stuff
import logging
import sys, os, pytz

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "temba.settings")

#for idx, arg in enumerate(sys.argv):
#    print("arg #{} is {}".format(idx, arg))

os.environ.setdefault("ADMIN_NAME", sys.argv[1])
os.environ.setdefault("ADMIN_EMAIL", sys.argv[2])
os.environ.setdefault("ADMIN_PSWD", sys.argv[3])

os.environ.setdefault("ORG_ADMIN_NAME", sys.argv[4])
os.environ.setdefault("ORG_ADMIN_MAIL", sys.argv[5])
os.environ.setdefault("ORG_ADMIN_PSWD", sys.argv[6])

os.environ.setdefault("FIRST_USERNAME", sys.argv[7])
os.environ.setdefault("FIRST_USERMAIL", sys.argv[8])
os.environ.setdefault("FIRST_USERPSWD", sys.argv[9])

os.environ.setdefault("ORG_NAME", sys.argv[10])

import django
django.setup()

from django.contrib.auth.management.commands.createsuperuser import get_user_model
from django.utils import timezone

from temba.api.models import APIToken
from temba.orgs.models import Org, OrgRole, Group, User


def create_user(username, email, password, group_names=(), **kwargs):
    user = User.objects.create_user(username=username, email=email, **kwargs)
    user.set_password(password)
    user.save()
    for group in group_names:
        user.groups.add(Group.objects.get(name=group))
    return user
#enddef create_user


token_key = "PO_RAPIDPRO_APIKEY"
superuser_name = os.environ.get('ADMIN_NAME')
org_name = os.environ.get('ORG_NAME')
logger = logging.getLogger()

superuser = get_user_model().objects.filter(username=superuser_name).first()
if superuser:
    #print('Superuser already exists. SKIPPING.')
    org = Org.objects.filter(name=org_name).first()
    if org:
        token = APIToken.get_or_create(org, superuser)
        logger.debug("token retrieved", extra={
            'org_name': org_name,
            'token': token,
        })
        print(token_key + "=" + str(token))
    else:
        logger.error("org does not exist", extra={
            'org_name': org_name,
        })
        print("Org "+org_name+" not found.")
    #endif org exists
elif os.environ.get('ADMIN_NAME') and os.environ.get('ADMIN_EMAIL') and os.environ.get('ADMIN_PSWD'):
    #print('Creating superuser...')
    superuser = get_user_model()._default_manager.db_manager('default').create_superuser(
            username=superuser_name,
            email=os.environ.get('ADMIN_EMAIL'),
            password=os.environ.get('ADMIN_PSWD')
    )
    #print('Superuser created.')

    #print('Creating Engage Org...')
    org = Org.objects.create(
        name=org_name,
        timezone=pytz.timezone("UTC"),
        brand="engage",
        created_on=timezone.now(),
        created_by=superuser,
        modified_by=superuser,
        uses_topups=False,
    )
    org.initialize()
    #print('Engage Org created.')

    theName = os.environ.get('ORG_ADMIN_NAME')
    theMail = os.environ.get('ORG_ADMIN_MAIL')
    thePswd = os.environ.get('ORG_ADMIN_PSWD')
    org_admin = create_user(username=theName, email=theMail, password=thePswd)
    org.add_user(org_admin, OrgRole.ADMINISTRATOR)

    theName = os.environ.get('FIRST_USERNAME')
    theMail = os.environ.get('FIRST_USERMAIL')
    thePswd = os.environ.get('FIRST_USERPSWD')
    org_user = create_user(username=theName, email=theMail, password=thePswd)
    org.add_user(org_user, OrgRole.EDITOR)

    token = APIToken.get_or_create(org, superuser)
    logger.debug("token retrieved", extra={
        'org_name': org_name,
        'token': token,
    })
    print(token_key + "=" + str(token))
#endif org not exist
