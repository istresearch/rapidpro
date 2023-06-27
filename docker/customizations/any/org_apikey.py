import sys, os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "temba.settings")

#for idx, arg in enumerate(sys.argv):
#    print("arg #{} is {}".format(idx, arg))

os.environ.setdefault("ADMIN_NAME", sys.argv[1])
os.environ.setdefault("FIRST_USERMAIL", sys.argv[2])
os.environ.setdefault("ORG_NAME", sys.argv[3])

import logging
logger = logging.getLogger()

import django
django.setup()

from temba.api.models import APIToken
from temba.orgs.models import Org

superuser_name = os.environ.get('ADMIN_NAME')
org_name = os.environ.get('ORG_NAME')

from django.contrib.auth.management.commands.createsuperuser import get_user_model
superuser = get_user_model().objects.filter(username=superuser_name)
if superuser:
    firstuser_name = os.environ.get('FIRST_USERMAIL')
    firstuser = get_user_model().objects.filter(email=firstuser_name).first()
    org = Org.objects.filter(name=org_name).first()
    if org and firstuser:
        token = APIToken.get_or_create(org, firstuser)
        logger.info("token retrieved", extra={
            'org_name': org_name,
            'token': token,
        })
        #print("ORG_APIKEY=" + str(token))
    elif not org:
        logger.error("org not found", extra={
            'org_name': org_name,
        })
    else:
        logger.error("user not found", extra={
            'user_name': firstuser_name,
        })
        #print("Org "+org_name+" or "+firstuser_name+" not found.")
    #endif org found

#endif superuser defined
