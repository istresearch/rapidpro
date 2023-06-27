from django.conf import settings as siteconfig
from django.db import transaction

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst, ignoreDjangoModelAttrs

from temba.orgs.models import Org


class OrgModelOverride(ClassOverrideMixinMustBeFirst, Org):
    override_ignore = ignoreDjangoModelAttrs(Org)

    # we do not want Django to perform any magic inheritance
    class Meta:
        abstract = True

    def get_brand_domain(self):
        if siteconfig.ALT_CALLBACK_DOMAIN:
            return siteconfig.ALT_CALLBACK_DOMAIN
        else:
            return self.getOrigClsAttr('get_brand_domain')(self)
    #enddef get_brand_domain

    def release(self, user, **kwargs):
        with transaction.atomic():
            self.getOrigClsAttr('release')(self, user, **kwargs)
        #endwith
    #enddef release

    # ensure old definition exists, so we can migrate to new schema
    from django.contrib.auth.models import User as OldUser
    from django.db import models
    Org.administrators = models.ManyToManyField(OldUser, related_name='org_admins')
    Org.editors = models.ManyToManyField(OldUser, related_name='org_editors')
    Org.viewers = models.ManyToManyField(OldUser, related_name='org_viewers')
    Org.agents = models.ManyToManyField(OldUser, related_name='org_agents')
    Org.surveyors = models.ManyToManyField(OldUser, related_name='org_surveyors')

#endclass OrgModelOverride
