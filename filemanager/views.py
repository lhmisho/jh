from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import generic
from django.db.models import Q
from filer.models import Folder, Image, File


class BaseSearchView(generic.ListView):
    paginate_by = 20
    ordering = ('id',)

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(
            self.get_data(context),
            **response_kwargs
        )


class ImageSearchView(BaseSearchView):

    def get_queryset(self):
        q = self.request.GET.get('q', None)
        if q is None:
            return Image.objects.filter()
        else:
            return Image.objects.filter(Q(name__icontains=q) | Q(original_filename__icontains=q))

    def get_data(self, context):
        current_page = self.request.GET.get('page', 1)
        return {
            'total': context['paginator'].count,
            'num_pages': context['paginator'].num_pages,
            'per_page': context['paginator'].per_page,
            'current_page': current_page,
            'result': list(map(lambda x: {
                'title': x.name if x.name and x.name != '' else x.original_filename,
                'url': self.request.build_absolute_uri(x.url),
                'id': x.id
            }, context['image_list']))
        }


class BrowseIframeView(generic.TemplateView):
    template_name = 'dashboard/filemanager/browse_iframe.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['iframe_url'] = "%s?_popup" % reverse('admin:filer_folder_changelist')
        return context
