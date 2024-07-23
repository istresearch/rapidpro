import itertools

from django.http import JsonResponse

from temba.campaigns.models import Campaign
from temba.flows.models import Flow
from temba.orgs.views import OrgCRUDL

from engage.utils.class_overrides import MonkeyPatcher


class ExportOverrides(MonkeyPatcher):
    patch_class = OrgCRUDL.Export

    def post(self: type(OrgCRUDL.Export), request, *args, **kwargs):
            org = self.get_object()

            flow_ids = [elt for elt in self.request.POST.getlist("flows") if elt]
            campaign_ids = [elt for elt in self.request.POST.getlist("campaigns") if elt]

            # fetch the selected flows and campaigns
            flows = Flow.objects.filter(id__in=flow_ids, org=org, is_active=True)
            campaigns = Campaign.objects.filter(id__in=campaign_ids, org=org, is_active=True)

            components = set(itertools.chain(flows, campaigns))

            # add triggers for the selected flows
            for flow in flows:
                components.update(flow.triggers.filter(is_active=True, is_archived=False))

            export = org.export_definitions(request.branding["link"], components)

            for f in export.get('flows',[]):
                f.pop('channels', None)
            #endfor

            response = JsonResponse(export, json_dumps_params=dict(indent=2))
            response["Content-Disposition"] = "attachment; filename=%s.json" % slugify(org.name)
            return response
    #enddef post

#endclass ExportOverrides
