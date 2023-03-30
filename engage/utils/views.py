from django.core.paginator import InvalidPage
from django.http import Http404, QueryDict
from django.utils.translation import gettext_lazy as _
from django.views.generic.list import MultipleObjectMixin, BaseListView

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst


class MultipleObjectMixinOverrides(ClassOverrideMixinMustBeFirst, MultipleObjectMixin):

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

class BaseListViewOverrides(ClassOverrideMixinMustBeFirst, BaseListView):

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
