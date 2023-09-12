user_fname = "dev"
user_lname = "one"
user_email = "dev@twosixtech.com"
user_pass = "abc123"
superuser_name = "admin"
superuser_email = "admin@twosixtech.com"
superuser_pass = "admin"
org_name = "Dev"
org_topup = 100_000

import os, pytz

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "temba.settings")

import django
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone

from temba.api.models import APIToken
from temba.orgs.models import Org, OrgRole, User as TembaUser

# Create Super User (named admin)
superuser = User.objects.create_superuser(superuser_name, superuser_email, superuser_pass)

#Create and initialize Org
org = Org.objects.create(
    name=org_name,
    timezone=pytz.timezone("UTC"),
    brand="engage",
    created_on=timezone.now(),
    created_by=superuser,
    modified_by=superuser,
)
org.initialize(topup_size=org_topup)

#Create user and set as Org admin
user = TembaUser.create(user_email, user_fname, user_lname, user_pass)
org.add_user(user, OrgRole.ADMINISTRATOR)

token = APIToken.get_or_create(org, superuser)

print("PO_RAPIDPRO_APIKEY=" + str(token))
