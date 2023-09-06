import logging

from django.core.paginator import InvalidPage
from django.forms import forms
from django.http import Http404, QueryDict, HttpResponseForbidden
from django.utils.translation import gettext_lazy as _
from django.views import defaults
from django.views.generic.list import MultipleObjectMixin, BaseListView

from temba.utils.views import BulkActionMixin

from engage.utils.class_overrides import MonkeyPatcher


def permission_denied(request, exception=None):
    """
    403 error
    :param request: the request
    :param exception: the exception, if any
    :return: the rendered page
    """
    # if temba-modal, return plain error page
    if request.headers.get('X-Pjax') == "1":
        return defaults.permission_denied(request, exception, template_name=defaults.ERROR_403_TEMPLATE_NAME)
    else:  # else return frame-templated error page
        return defaults.permission_denied(request, exception, template_name='403_permission_denied.haml')
#enddef permission_denied

def page_not_found(request, exception=None):
    """
    404 error
    :param request: the request
    :param exception: the exception, if any
    :return: the rendered page
    """
    # if temba-modal, return plain error page
    if request.headers.get('X-Pjax') == "1":
        return defaults.page_not_found(request, exception, template_name='404.html')
    else:  # else return frame-templated error page
        return defaults.page_not_found(request, exception, template_name='404_not_found.haml')
#enddef page_not_found

def server_error(request):
    """
    500 error
    :param request: the request
    :return: the rendered page
    """
    # if temba-modal, return plain error page
    if request.headers.get('X-Pjax') == "1":
        return defaults.page_not_found(request, template_name='500.html')
    else:  # else return frame-templated error page
        try:
            return defaults.page_not_found(request, template_name='500_server_error.haml')
        except:  # else return plain error page
            return defaults.server_error(request, template_name='500.html')
        #endtry
    #endif
#enddif server_error

class MultipleObjectMixinOverrides(MonkeyPatcher):
    patch_class = MultipleObjectMixin

    def paginate_queryset(self, queryset, page_size):
        """
        Why do we need this override?: Django does not handle deleting items
        from the last page of a paginated queryset well at all.
        :param self: the user object
        :param queryset: the queryset to paginate
        :param page_size: the size of each page.
        :return: the list of ( paginator, page_number, object_list, more pages bool )
        """
        paginator = self.get_paginator(queryset, page_size,
            orphans=self.get_paginate_orphans(),
            allow_empty_first_page=self.get_allow_empty(),
        )
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                raise Http404(_("Page is not 'last', nor can it be converted to an int."))
            #endif
        #endtry

        changed = False
        if page_number > paginator.num_pages:
            page_number = paginator.num_pages
            changed = True
        #endif
        try:
            page = paginator.page(page_number)
            if changed:
                paginator.prev = page_number
                return (paginator, page_number, page.object_list, page.has_other_pages())
            else:
                return (paginator, page, page.object_list, page.has_other_pages())
            #endif
        except InvalidPage as e:
            raise Http404(_('Invalid page (%(page_number)s): %(message)s') % {
                'page_number': page_number,
                'message': str(e)
            })
        #endtry
    #enddef paginate_queryset

#endclass MultipleObjectMixinOverrides

class BaseListViewOverrides(MonkeyPatcher):
    patch_class = BaseListView

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        allow_empty = self.get_allow_empty()

        if not allow_empty:
            if self.get_paginate_by(self.object_list) is not None and hasattr(self.object_list, 'exists'):
                is_empty = not self.object_list.exists()
            else:
                is_empty = not self.object_list
            if is_empty:
                raise Http404(_("Empty list and '%(class_name)s.allow_empty' is False.") % {
                    'class_name': self.__class__.__name__,
                })
        context = self.get_context_data()
        response = self.render_to_response(context)
        if 'page' in self.request.GET and int(self.request.GET['page']) > context['paginator'].num_pages:
            import copy
            request_copy = copy.copy(self.request)
            query_params = QueryDict(request_copy.META['QUERY_STRING']).copy()
            query_params['page'] = context['paginator'].num_pages
            request_copy.META['QUERY_STRING'] = query_params.urlencode()
            response["REDIRECT"] = request_copy.get_full_path()
        return response
    #enddef get

#endclass BaseListViewOverrides

class BulkActionMixinOverrides(MonkeyPatcher):
    patch_class = BulkActionMixin

    def post(self, request, *args, **kwargs):
        """
        Handles a POSTed action form and returns a response
        """
        user = self.get_user()
        org = user.get_org()
        form = BulkActionMixin.Form(
            self.get_bulk_actions(), self.get_queryset(), self.get_bulk_action_labels(), data=self.request.POST
        )
        action_error = None

        if form.is_valid():
            action = form.cleaned_data["action"]
            objects = form.cleaned_data["objects"]
            all_objects = form.cleaned_data["all"]
            label = form.cleaned_data.get("label")

            if all_objects:
                objects = self.get_queryset()
            else:
                objects_ids = [o.id for o in objects]
                self.kwargs["bulk_action_ids"] = objects_ids  # include in kwargs so is accessible in get call below

                # convert objects queryset to one based only on org + ids
                objects = self.model._default_manager.filter(org=org, id__in=objects_ids)
            #endif
            # check we have the required permission for this action
            permission = self.get_bulk_action_permission(action)
            if not user.has_perm(permission) and not user.has_org_perm(org, permission):
                return HttpResponseForbidden()
            #endif
            try:
                self.apply_bulk_action(user, action, objects, label)
            except forms.ValidationError as e:
                action_error = ", ".join(e.messages)
            except Exception as ex:
                logger = logging.getLogger()
                logger.exception(f"error applying '{action}' to {self.model.__name__} objects", exc_info=ex, extra={
                    'user': user.email,
                    'model': self.model.__name__,
                    'action': action,
                    'ex': ex,
                })
                action_error = f"Failed: {ex}"
            #endtry
        #endif form is valid
        response = self.get(request, *args, **kwargs)
        if action_error:
            response["Temba-Toast"] = action_error
        elif hasattr(self, 'apply_bulk_action_toast') and self.apply_bulk_action_toast:
            response["Temba-Toast"] = self.apply_bulk_action_toast
        #endif
        return response
    #enddef post

#endclass BulkActionMixinOverrides
