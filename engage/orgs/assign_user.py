from django import forms
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from smartmin.views import (
    SmartFormView,
)

from temba.api.models import APIToken
from temba.orgs.models import Org


class AssignUserMixin:

    class AssignUser(SmartFormView):
        class ServiceForm(forms.Form):
            organization = forms.ModelChoiceField(queryset=Org.objects.all(), empty_label=None)
            user_group = forms.ChoiceField(
                choices=(("A", _("Administrators")), ("E", _("Editors")), ("V", _("Viewers")), ("S", _("Surveyors"))),
                required=True,
                initial="E",
                label=_("User group"),
            )
            username = forms.CharField(required=True, label=_("Username"))

        form_class = ServiceForm
        title = _("Assign User to Organization")
        fields = ("organization", "user_group", "username")

        # valid form means we set our org and redirect to their inbox
        def form_valid(self, form):
            org = form.cleaned_data["organization"]
            user_group = form.cleaned_data["user_group"]
            username = form.cleaned_data["username"]

            user = User.objects.filter(username__iexact=username).first()

            if org:
                if user_group == "A":
                    org.administrators.add(user)
                    org.editors.remove(user)
                    org.surveyors.remove(user)
                    org.viewers.remove(user)
                elif user_group == "E":
                    org.editors.add(user)
                    org.administrators.remove(user)
                    org.surveyors.remove(user)
                    org.viewers.remove(user)
                elif user_group == "S":
                    org.surveyors.add(user)
                    org.administrators.remove(user)
                    org.editors.remove(user)
                    org.viewers.remove(user)
                else:
                    org.viewers.add(user)
                    org.administrators.remove(user)
                    org.editors.remove(user)
                    org.surveyors.remove(user)

                # when a user's role changes, delete any API tokens they're no longer allowed to have
                api_roles = APIToken.get_allowed_roles(org, user)
                for token in APIToken.objects.filter(org=org, user=user).exclude(role__in=api_roles):
                    token.release()

                org.save()

            success_url = reverse("orgs.org_assign_user")
            return HttpResponseRedirect(success_url)
