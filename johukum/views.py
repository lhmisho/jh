import json
import os

import django_tables2 as tables
from bson.objectid import ObjectId
from django import forms as dforms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.core.files.storage import FileSystemStorage
# for pagination
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.http import (HttpResponseNotFound, HttpResponseRedirect,
                         JsonResponse, response)
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  TemplateView, UpdateView)
from django.views.generic import edit as editViews
from django.views.generic.list import ListView
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin, SingleTableView
from formtools.wizard.views import SessionWizardView
from hijack.decorators import hijack_decorator, hijack_require_http_methods
from hijack.helpers import login_user

from johukum import filters as j_filters
from johukum import forms, models
from johukum import tables as j_tables
from johukum.utils import BusinessInfoReportView, EditorInfoReportView
from zero_auth import forms as zero_auth_forms
from zero_auth import views as zero_auth_views
from zero_auth.decorators import otp_verify_required, password_verify_required


class TwoFactorLoginView(zero_auth_views.TwoFactorLoginView):
    verification_template='registration/otp_verify.html'


def index_view(request):
    return redirect(reverse('dashboard'))

@login_required
def dashboard_view(request):
    analytics = {}

    if request.user.is_admin:
        analytics['total_agents'] = Group.objects.filter(name=settings.AGENT_GROUP).first().user_set.count()
        analytics['total_gcos'] = Group.objects.filter(name=settings.GCO_GROUP).first().user_set.count()
        analytics['total_moderators'] = Group.objects.filter(name=settings.MODERATOR_GROUP).first().user_set.count()
        analytics['total_editors'] = Group.objects.filter(name=settings.EDITOR_GROUP).first().user_set.count()
        analytics['total_business_data'] = models.BusinessInfo.objects.all().count()
        analytics['total_pending_business_data'] = models.BusinessInfo.objects.filter(status=1).count()
        analytics['total_rejected_business_data'] = models.BusinessInfo.objects.filter(status=0).count()
        analytics['total_approved_business_data'] = models.BusinessInfo.objects.filter(status=3).count()
        analytics['totoal_mobile_data']  = models.MobileNumberData.objects.all().count()
    elif request.user.is_agent:
        analytics['total_added'] = models.BusinessInfo.objects.filter(added_by=request.user, deleted_at=None).count()
        analytics['total_pending'] = models.BusinessInfo.objects.filter(added_by=request.user, status=models.BusinessInfo.PENDING, deleted_at=None).count()
        analytics['total_approved'] = models.BusinessInfo.objects.filter(added_by=request.user, status=models.BusinessInfo.APPROVED, deleted_at=None).count()
        analytics['total_reviewed'] = models.BusinessInfo.objects.filter(added_by=request.user, status=models.BusinessInfo.REVIEWED, deleted_at=None).count()
        analytics['total_rejected'] = models.BusinessInfo.objects.filter(added_by=request.user, status=models.BusinessInfo.REJECTED, deleted_at=None).count()
        analytics['total_business_data'] = models.BusinessInfo.objects.filter(added_by=request.user, deleted_at=None).count()
        analytics['totoal_mobile_data'] = models.MobileNumberData.objects.filter(added_by=request.user, deleted_at=None).count()

    elif request.user.is_editor:
        analytics['total_added']  = models.BusinessInfo.objects.filter(added_by=request.user, deleted_at=None).count()
        analytics['total_reviewed'] = models.BusinessInfo.objects.filter(reviewed_by=request.user, status=models.BusinessInfo.REVIEWED, deleted_at=None).count()
        analytics['total_approved'] = models.BusinessInfo.objects.filter(approved_by=request.user, status=models.BusinessInfo.APPROVED, deleted_at=None).count()
        analytics['total_rejected'] = models.BusinessInfo.objects.filter(rejected_by=request.user, status=models.BusinessInfo.REJECTED, deleted_at=None).count()
        analytics['totoal_mobile_data'] = models.MobileNumberData.objects.filter(added_by=request.user, deleted_at=None).count()
        # analytics['total_pending'] = models.BusinessInfo.objects.filter(added_by__parent=request.user, status=models.BusinessInfo.PENDING, deleted_at=None).count()

    elif request.user.is_moderator:
        analytics['total_added'] = models.BusinessInfo.objects.filter(added_by__in=request.user.get_children, deleted_at=None).count()
        analytics['total_reviewed'] = models.BusinessInfo.objects.filter(reviewed_by=request.user,
                                                                         status=models.BusinessInfo.REVIEWED,
                                                                         deleted_at=None).count()
        analytics['total_approved'] = models.BusinessInfo.objects.filter(approved_by=request.user,
                                                                         status=models.BusinessInfo.APPROVED,
                                                                         deleted_at=None).count()
        analytics['total_rejected'] = models.BusinessInfo.objects.filter(rejected_by=request.user,
                                                                         status=models.BusinessInfo.REJECTED,
                                                                         deleted_at=None).count()
        analytics['totoal_mobile_data'] = models.MobileNumberData.objects.filter(added_by__in=request.user.get_children,
                                                                                 deleted_at=None).count()
        analytics['total_pending'] = {}

    elif request.user.is_gco:
        analytics['total_added'] = models.BusinessInfo.objects.filter(added_by=request.user, deleted_at=None).count()
        analytics['total_reviewed'] = models.BusinessInfo.objects.filter(reviewed_by=request.user,
                                                                         status=models.BusinessInfo.REVIEWED,
                                                                         deleted_at=None).count()
        analytics['total_rejected'] = models.BusinessInfo.objects.filter(rejected_by=request.user,
                                                                         status=models.BusinessInfo.REJECTED,
                                                                         deleted_at=None).count()
        analytics['totoal_mobile_data'] = models.MobileNumberData.objects.filter(added_by=request.user,
                                                                                 deleted_at=None).count()

    return render(request, 'dashboard/index.html', context=analytics)


FORMS = [
    ("location", forms.LocationInfoForm),
    ("contact", forms.ContactInfoForm),
    ("hoop", forms.OpenCloseFormSet),
    ('payment', forms.AcceptedPaymentForm),
    ("company", forms.CompanyInfoForm),
    ("categories", forms.CategorySelectForm),
    # ("verification", forms.ZHOTPValidationForm),
    ("files", forms.BusinessFileUploadForm),
]

TEMPLATES = {
    "location": "dashboard/manage_data/location_form.html",
    "contact": "dashboard/manage_data/contact_person_form.html",
    "hoop": "dashboard/manage_data/hour_of_operation_form.html",
    "payment": "dashboard/manage_data/accepted_payment_form.html",
    "company": "dashboard/manage_data/company_info_form.html",
    "categories": "dashboard/manage_data/category_form.html",
    # "verification": "dashboard/manage_data/verification_form.html",
    "files": "dashboard/manage_data/files_form.html"
}


@method_decorator(login_required, name='dispatch')
class BusinessInfoCreateView(TemplateView):
    template_name = 'dashboard/manage_data/create.html'


@method_decorator(login_required, name='dispatch')
class BusinessInfoEditView(TemplateView):
    template_name = 'dashboard/manage_data/update.html'

    def get_context_data(self, **kwargs):
        id = kwargs.pop('id')
        context = super().get_context_data(**kwargs)
        context['id'] = id
        return context

@method_decorator(login_required, name='dispatch')
class BusinessInfoView(TemplateView):
    template_name = 'dashboard/manage_data/show.html'

    def dispatch(self, request, id, *args, **kwargs):
        self.id = id
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = forms.ChangeStatusForm(request.POST)
        if form.is_valid():
            form.update_status(request)
        return super().get(request, *args, **kwargs)

    def get_context_data(self):
        context = super().get_context_data()
        context['business_info'] = models.BusinessInfo.objects.get(_id=self.id)
        context['change_status_form'] = forms.ChangeStatusForm()
        return context


def varify_contact(request, id, mni):
    business_info = models.BusinessInfo.objects.get(_id=id)
    mn = int(mni)
    business_info.contact.mobile_numbers[int(mn)].verified=True
    business_info.save()
    return redirect(reverse_lazy('manage_data.show', kwargs={'id': id}))


@method_decorator(login_required, name='dispatch')
class BusinessInfoVerifyMobileNumberView(editViews.FormView, zero_auth_views.MobileOTPMixin):
    form_class = zero_auth_forms.OTPValidationForm
    template_name = 'dashboard/manage_data/verify_mobile_number.html'

    def get_success_url(self):
        return reverse_lazy('manage_data.show', kwargs={'id': self.business_info.pk })

    def dispatch(self, request, id, mni, *args, **kwargs):
        self.id = id
        self.mni = int(mni)
        if self.mobile_number:
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponseNotFound()

    def get(self, request, *args, **kwargs):
        if not self.is_code_sent():
            self.send_code(str(self.mobile_number), force=True)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.POST.get('reset'):
            self.reset()
            return redirect(self.get_success_url())
        else:
            return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mobile_number"] = self.mobile_number
        return context

    @cached_property
    def business_info(self):
        try:
            return models.BusinessInfo.objects.get(_id=self.id)
        except Exception as e:
            print(e)
            return None

    @cached_property
    def mobile_number(self):
        try:
            contact_number = self.business_info.contact.mobile_numbers[self.mni]
            return contact_number.mobile_number if not contact_number.verified else None
        except Exception as e:
            print(e)
            return None

    def verified(self):
        self.business_info.contact.mobile_numbers[self.mni].verified = True
        self.business_info.save()

    def form_valid(self, form):
        if self.verify_code(form.cleaned_data['code']):
            self.verified()
            self.reset()
            messages.success(self.request, '%s is verified' % self.mobile_number)
            return super().form_valid(form)
        else:
            messages.error(self.request, 'Invalid OTP Code')
            return redirect(self.request.META.get('HTTP_REFERER'))


@method_decorator(login_required, name='dispatch')
class BusinessInfoEditLegacyView(editViews.FormView):

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['update'] = True
        return context

    def get_template_names(self):
        wizard = self.get_wizard()
        return [TEMPLATES.get(wizard)]

    def get_object(self):
        obj_id = self.request.GET.get('id')
        return models.BusinessInfo.objects.get(pk=obj_id)

    def get_wizard(self):
        return self.request.GET.get('wizard')

    def remove_and_add_helper(self, obj, attr_name, new_data_array):
        for item in getattr(obj, attr_name).all():
            getattr(obj, attr_name).remove(item)
        for item in new_data_array:
            getattr(obj, attr_name).add(item)

    def get_form(self, form_class=None):
        instance = self.get_object()
        wizard = self.get_wizard()
        form_kwargs = self.get_form_kwargs()
        for n, f in FORMS:
            if n == wizard:
                if issubclass(f, dforms.ModelForm):
                    if f == forms.LocationInfoForm:
                        form_kwargs['instance'] = instance.location

                    elif f == forms.CompanyInfoForm:
                        form_kwargs['instance'] = instance

                    elif f == forms.ContactInfoForm:
                        form_kwargs['instance'] = instance.contact
                else:
                    if f == forms.CategorySelectForm:
                        form_kwargs['initial'] = {
                            'categories': instance.keywords.all()
                        }
                    elif f == forms.AcceptedPaymentForm:
                        form_kwargs['initial'] = {
                            'accepted_payment_methods': instance.accepted_payment_methods.all()
                        }
                    elif f == forms.OpenCloseFormSet:
                        form_kwargs['initial'] = [item for _, item in instance.hours_of_operation.to_dict().items()]
                    elif f == forms.BusinessFileUploadForm:
                        initials = {
                            'logo': instance.logo,
                            'cover_photo': instance.cover_photo,
                            'embed_video': instance.embed_video
                        }
                        try:
                            initials['video'] = instance.videos.first().video
                        except Exception as e:
                            pass
                        for index, item in enumerate(instance.photos.all()):
                            initials['photo%d' % (index+1)] = item.image
                        form_kwargs['initial'] = initials
                return f(**form_kwargs)

    def form_valid(self, form):
        obj = self.get_object()

        if isinstance(form, forms.LocationInfoForm):
            obj.location = form.save(commit=False)

        elif isinstance(form, forms.CompanyInfoForm):
            obj.no_of_employees = form.cleaned_data['no_of_employees']
            obj.year_of_establishment = form.cleaned_data['year_of_establishment']
            obj.annual_turnover = form.cleaned_data['annual_turnover']
            obj.description = form.cleaned_data['description']
            self.remove_and_add_helper(obj, 'professional_associations', form.cleaned_data['professional_associations'])
            self.remove_and_add_helper(obj, 'certifications', form.cleaned_data['certifications'])

        elif isinstance(form, forms.ContactInfoForm):
            obj.contact = form.save(commit=False)

        elif isinstance(form, forms.CategorySelectForm):
            self.remove_and_add_helper(obj, 'keywords', form.cleaned_data['categories'])

        elif isinstance(form, forms.AcceptedPaymentForm):
            self.remove_and_add_helper(obj, 'accepted_payment_methods', form.cleaned_data['accepted_payment_methods'])

        elif isinstance(form, forms.OpenCloseFormSet):
            obj.hours_of_operation = form.save(commit=False)

        elif isinstance(form, forms.BusinessFileUploadForm):
            form.save(obj, update=True)

        obj.save()
        return redirect(reverse_lazy('manage_data.show', kwargs={'id': obj.pk}))


def transform_for_display(item):
    item['id'] = str(item['_id'])
    #print(item['status'])
    if item['status'] == 1:
        item['status'] = 'PENDING'
    elif item['status'] == 2:
        item['status'] = 'REVIEWED'
    elif item['status'] == 3:
        item['status'] = 'APPROVED'
    else:
        item['status'] = 'REJECTED'
    return item


@method_decorator(login_required, name='dispatch')
class BusinessInfoListView(TemplateView):
    template_name = 'dashboard/manage_data/businessinfo_list.html'


@method_decorator(login_required, name='dispatch')
class BusinessDataFileUploadView(TemplateView):
    template_name = 'dashboard/manage_data/businessinfo_file_upload.html'

    def dispatch(self, request, *args, **kwargs):
        self.pk = kwargs.pop('pk')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pk'] = self.pk
        return context


@method_decorator(login_required, name='dispatch')
class MobileNumberListView(TemplateView):
    template_name = 'dashboard/mobile_number_data/list.html'



@login_required
@otp_verify_required
def business_info_delete_view(request, id):
    try:
        models.BusinessInfo.objects.get(pk=id).delete()
        return redirect(reverse('manage_data.index'))
    except Exception as e:
        return response.HttpResponseNotFound()

@method_decorator(login_required, name='dispatch')
class CategoryListView(ListView):
    model = models.Category
    template_name = 'dashboard/categories/index.html'
    paginate_by = 20

    def get_queryset(self):
        parent = self.request.GET.get('parent')
        if parent:
            parent = models.Category.objects.filter(pk=parent).first()
            return parent.get_children()
        else:
            return models.Category.objects.filter(parent=None)

@login_required
def category_delete_view(request, id):
    try:
        models.Category.objects.filter(pk=id).delete()
        return redirect(reverse('categories.index'))
    except Exception as e:
        return response.HttpResponseNotFound()


@method_decorator(login_required, name='dispatch')
class CategoryFormView(editViews.CreateView):
    form_class = forms.CategoryForm
    template_name = 'dashboard/categories/create.html'
    success_url = reverse_lazy('categories.index')


########### edit by misho #########
@method_decorator(login_required, name='dispatch')
class CategoryUpdateView(UpdateView):
    #form_class = forms.CategoryForm
    model = models.Category
    template_name = 'dashboard/categories/update.html'
    fields = ['name', 'parent', 'icon', 'banner', 'order', 'show_as_slider']

    def get_object(self, queryset=None):
        id = self.kwargs['id']
        return self.model.objects.get(_id=id)

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(reverse('categories.index'))


@method_decorator(login_required, name='dispatch')
class UserListView(ListView):
    model = models.User
    template_name = 'dashboard/users/index.html'
    paginate_by = 20

    def dispatch(self, request, role, *args, **kwargs):
        self.role = role
        allowed = role == settings.AGENT_GROUP and self.request.user.is_gco
        if not allowed and not self.request.user.is_admin:
            return response.HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        try:
            group = Group.objects.filter(name=self.role).first()
            if self.request.user.is_gco:
                return group.user_set.filter(parent=self.request.user)
            else:
                return group.user_set.filter()
        except Exception:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role'] = self.role
        return context

@method_decorator(login_required, name='dispatch')
class UserCreateView(editViews.CreateView):

    template_name = 'dashboard/users/create.html'

    forms = {
        settings.AGENT_GROUP : forms.AgentForm,
        settings.GCO_GROUP : forms.GCOForm,
        settings.MODERATOR_GROUP : forms.ModeratorForm,
        settings.EDITOR_GROUP : forms.EditorForm,
        settings.ADMIN_GROUP: forms.AdminForm,
    }

    def dispatch(self, request, role, *args, **kwargs):
        self.role = role
        allowed = role == settings.AGENT_GROUP and self.request.user.is_gco
        if not allowed and not self.request.user.is_admin:
            return response.HttpResponseForbidden()
        return super().dispatch(request, role, *args, **kwargs)

    def get_form_class(self):
        return self.forms.get(self.role)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role'] = self.role
        return context

    def get(self, request, role, *args, **kwargs):
        if role in self.forms:
            self.role = role
            return super().get(request, *args, **kwargs)
        else:
            return response.HttpResponseNotFound()

    def post(self, request, role, *args, **kwargs):
        if role in self.forms:
            self.role = role
            return super().post(request, *args, **kwargs)
        else:
            return response.HttpResponseNotFound()

    def get_success_url(self):
        return reverse_lazy('users.index', kwargs={
            'role':self.role
        })

class UserUpdateView(editViews.UpdateView):

    template_name = 'dashboard/users/update.html'
    model = models.User
    forms = {
        settings.AGENT_GROUP : forms.AgentForm,
        settings.GCO_GROUP : forms.GCOForm,
        settings.MODERATOR_GROUP : forms.ModeratorForm,
        settings.EDITOR_GROUP : forms.EditorForm,
        settings.ADMIN_GROUP : forms.AdminForm
    }

    def get_form_class(self):
        return self.forms.get(self.role)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role'] = self.role
        return context

    def get(self, request, role, *args, **kwargs):
        if role in self.forms:
            self.role = role
            return super().get(request, *args, **kwargs)
        else:
            return response.HttpResponseNotFound()

    def post(self, request, role, *args, **kwargs):
        if role in self.forms:
            self.role = role
            return super().post(request, *args, **kwargs)
        else:
            return response.HttpResponseNotFound()

    def get_success_url(self):
        return reverse_lazy('users.index', kwargs={
            'role':self.role
        })


@login_required
def user_delete_view(request, role, id):
    try:
        models.User.objects.filter(pk=id).delete()
        return redirect(reverse('users.index', kwargs={ 'role': role }))
    except Exception:
        return response.HttpResponseNotFound()


@method_decorator(login_required, name='dispatch')
class MobileDataCreateView(editViews.FormView):
    form_class = forms.MobileDataForm
    template_name = "dashboard/mobile_number_data/form.html"
    success_url = reverse_lazy('mobile_data.index')

    def form_valid(self, form):
        fs = form.save(commit=False)
        fs.added_by = self.request.user
        fs.save()
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class MobileDataUpdateView(UpdateView):
    form_class = forms.MobileDataUpdateForm
    template_name = "dashboard/mobile_number_data/update.html"

    def get_object(self, queryset=None):
        id = self.kwargs['id']
        return models.MobileNumberData.objects.get(_id=id)

    def get_context_data(self,queryset=None, **kwargs):
        context = super().get_context_data(**kwargs)
        id = self.kwargs['id']
        context['obj'] = models.MobileNumberData.objects.get(_id=id)
        return context

    def form_valid(self, form):
        request = self.request
        f = form.save(commit=False)
        f.edit_by = request.user
        f.save()
        return HttpResponseRedirect(reverse('mobile_data.index'))

####################################################

@login_required
def mobile_data_delete_view(request, id):
    try:
        models.MobileNumberData.objects.filter(pk=id).delete()
        return redirect(reverse('mobile_data.index'))
    except Exception as e:
        return response.HttpResponseNotFound()


@method_decorator(login_required, name='dispatch')
class MobileDataView(TemplateView):
    template_name = 'dashboard/mobile_number_data/show.html'

    def dispatch(self, request, id, *args, **kwargs):
        self.id = id
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = forms.MobileDataChangeStatusForm(request.POST)
        if form.is_valid():
            form.update_status(request)
        return super().get(request, *args, **kwargs)

    def get_context_data(self):
        context = super().get_context_data()
        context['obj'] = models.MobileNumberData.objects.get(_id=self.id)
        context['change_status_form'] = forms.MobileDataChangeStatusForm()
        return context


@method_decorator(login_required, name='dispatch')
class LocationTableView(SingleTableMixin, FilterView):
    table_class = j_tables.LocationTable
    model = models.Location
    template_name = 'dashboard/locations/table.html'

    filterset_class = j_filters.LocationFilter

@method_decorator(login_required, name='dispatch')
class LocationCreateView(editViews.CreateView):
    model = models.Location
    fields = ['name', 'location_type', 'parent']
    success_url = reverse_lazy('locations.index')
    template_name = 'dashboard/locations/create.html'

########### misho ################
@login_required
def location_delete_view(request, id):
    try:
        models.Location.objects.filter(pk=id).delete()
        return redirect(reverse('locations.index'))
    except Exception as e:
        return response.HttpResponseNotFound()

@method_decorator(login_required, name='dispatch')
class LocationsUpdateView(UpdateView):
    model = models.Location
    fields = ['name', 'location_type', 'parent']
    #success_url = reverse_lazy('locations.index')
    template_name = 'dashboard/locations/update.html'

    def get_object(self, queryset=None):
        id = self.kwargs['id']
        return self.model.objects.get(_id=id)

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(reverse('locations.index'))

@method_decorator(login_required, name='dispatch')
class PaymentMethodTableView(tables.SingleTableView):
    table_class = j_tables.PaymentMethodTable
    queryset = models.PaymentMethod.objects.all()
    template_name = "dashboard/payment_methods/table.html"
    paginate_by = 20


@method_decorator(login_required, name='dispatch')
class PaymentMethodCreateView(editViews.CreateView):
    model = models.PaymentMethod
    fields = ['name']
    success_url = reverse_lazy('payment_methods.index')
    template_name = "dashboard/payment_methods/create.html"


######################################################################
@method_decorator(login_required, name='dispatch')
class PaymentMethodUpdateView(UpdateView):
    model = models.PaymentMethod
    fields = ['name']
    #success_url = reverse_lazy('payment_methods.index')
    template_name = "dashboard/payment_methods/update.html"

    def get_object(self, queryset=None):
        id = self.kwargs['id']
        return self.model.objects.get(_id=id)

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(reverse('payment_methods.index'))


@login_required
def payment_delete_view(request, id):
    try:
        models.PaymentMethod.objects.filter(pk=id).delete()
        return redirect(reverse('payment_methods.index'))
    except Exception as e:
        return response.HttpResponseNotFound()


######################################################################
@method_decorator(login_required, name='dispatch')
class ProfessionalAssociationTableView(tables.SingleTableView):
    table_class = j_tables.ProfessionalAssociationTable
    queryset = models.ProfessionalAssociation.objects.all()
    template_name = "dashboard/professional_associations/table.html"
    paginate_by = 20


@method_decorator(login_required, name='dispatch')
class ProfessionalAssociationCreateView(editViews.CreateView):
    model = models.ProfessionalAssociation
    fields = ['name']
    success_url = reverse_lazy('professional_associations.index')
    template_name = "dashboard/professional_associations/create.html"


######################################################################
@method_decorator(login_required, name='dispatch')
class ProfessionalAssociationUpdateView(UpdateView):
    model = models.ProfessionalAssociation
    fields = ['name']
    #success_url = reverse_lazy('professional_associations.index')
    template_name = "dashboard/professional_associations/update.html"

    def get_object(self, queryset=None):
        id = self.kwargs['id']
        return self.model.objects.get(_id=id)

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(reverse('professional_associations.index'))


@login_required
def professionalAssociation_delete_view(request, id):
    try:
        models.ProfessionalAssociation.objects.filter(pk=id).delete()
        return redirect(reverse('professional_associations.index'))
    except Exception as e:
        return response.HttpResponseNotFound()


@method_decorator(login_required, name='dispatch')
class CertificationTableView(tables.SingleTableView):
    table_class = j_tables.CertificationTable
    queryset = models.Certification.objects.all()
    template_name = "dashboard/certifications/table.html"
    paginate_by = 20


@method_decorator(login_required, name='dispatch')
class CertificationCreateView(editViews.CreateView):
    model = models.Certification
    fields = ['name']
    success_url = reverse_lazy('certifications.index')
    template_name = "dashboard/certifications/create.html"


@method_decorator(login_required, name='dispatch')
class CertificationUpdateView(UpdateView):
    model = models.Certification
    fields = ['name']
    #success_url = reverse_lazy('certifications.index')
    template_name = "dashboard/certifications/update.html"

    def get_object(self, queryset=None):
        id = self.kwargs['id']
        return self.model.objects.get(_id=id)

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(reverse('certifications.index'))


@login_required
def certification_delete_view(request, id):
    try:
        models.Certification.objects.filter(pk=id).delete()
        return redirect(reverse('certifications.index'))
    except Exception as e:
        return response.HttpResponseNotFound()


@method_decorator(otp_verify_required, name='dispatch')
class MyProfileView(editViews.FormView, zero_auth_views.MobileOTPMixin):
    form_class = forms.ProfileForm
    otp_form_class = zero_auth_forms.OTPValidationForm
    template_name = 'dashboard/profile.html'
    success_url = reverse_lazy('profile')

    def is_form_submitted(self):
        return self.request.session.get('FORM_SUBMITTED') == True

    def submitted(self, data_to_cache):
        self.request.session['FORM_SUBMITTED'] = True
        self.request.session['CACHED_DATA'] = json.dumps(data_to_cache)

    def get_cached_data(self):
        try:
            return json.loads(self.request.session['CACHED_DATA'])
        except Exception as e:
            print(e)
            return {}

    def reset(self):
        if self.request.session.get('FORM_SUBMITTED'):
            del self.request.session['FORM_SUBMITTED']
        super().reset()

    def get_form_class(self):
        if self.is_form_submitted():
            return self.otp_form_class
        else:
            return self.form_class

    def get_form(self):
        kwargs = super().get_form_kwargs()
        if not self.is_form_submitted():
            kwargs['instance']=self.request.user
        return self.get_form_class()(**kwargs)

    def form_valid(self, form):
        if isinstance(form, forms.ProfileForm) and form.is_number_changed():
            self.submitted(self.request.POST.dict())
            mobile_number = form.cleaned_data.get('mobile_number')
            self.send_code(mobile_number)
            messages.info(self.request, 'A verification code has been sent to %s.' % mobile_number)
            return redirect(self.request.META.get('HTTP_REFERER'))
        elif isinstance(form, zero_auth_forms.OTPValidationForm):
            if not self.verify_code(form.cleaned_data.get('code')):
                messages.error(self.request, 'Invalid OTP Code')
            else:
                form = forms.ProfileForm(**{
                    'data': self.get_cached_data(),
                    'instance': self.request.user
                })
                self.reset()
                if not form.is_valid():
                    return self.form_invalid(form)

        user = form.save(commit=True)
        update_session_auth_hash(self.request, user)
        messages.success(self.request, 'Profile Updated Successfully')
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        if request.POST.get('reset'):
            self.reset()
            return redirect(request.META.get('HTTP_REFERER'))
        else:
            return super().post(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class ReportView(BusinessInfoReportView):
    model_class = models.BusinessInfo
    approval = True
    template_name = 'dashboard/reports/reports.html'


@method_decorator(login_required, name='dispatch')
class MobileReportView(BusinessInfoReportView):
    model_class = models.MobileNumberData
    approval = False
    template_name = 'dashboard/reports/mobile_reports.html'


@method_decorator(login_required, name='dispatch')
class EditorReportView(EditorInfoReportView):
    model_class = models.BusinessInfo
    template_name = 'dashboard/reports/editor_report.html'


class CategoryReport(TemplateView):
    model_class = models.BusinessInfo
    template_name = 'dashboard/reports/category_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        init_q = models.Location.objects.filter(parent_id="5bb608df41533c632889eb8d")
        init_data = []

        for item in range(len(init_q)):
            # import pdb;pdb.set_trace()
            aggregate_query = [
                {
                    "$unwind": "$keywords_id"
                },
                {
                    "$lookup": {
                        "from": models.Category._meta.db_table,
                        "localField": "keywords_id",
                        "foreignField": "_id",
                        "as": "category"
                    }
                },
                {
                    "$match": {
                        "location.location_id": init_q[item]._id
                    }
                },
                {
                  "$group": {
                      '_id': "$keywords_id",
                      'count': {
                          '$sum': 1
                      },
                      'category': {'$addToSet': '$category'}
                  }
                }
            ]
            result_data = list(models.BusinessInfo.objects.mongo_aggregate(aggregate_query))
            prepared_data = []
            for r_item in result_data:

                prepared_data.append({
                    "category_name": r_item['category'][0][0]['name'],
                    "count": r_item['count'],
                })
            init_data.append({
                'thana_id': init_q[item]._id,
                'thana_name': init_q[item].name,
                'kwargs': prepared_data
            })
        # import pdb;pdb.set_trace()
        context['data'] = init_data
        # return Response({
        #     'data': init_data
        # })


@login_required
def validate_phone_number(request):
    phone_number = request.GET.get('phone_number')
    form = forms._MobileNumberHelperForm(data={
        'mobile_number': phone_number
    })
    if form.is_valid():
        return JsonResponse({'valid': True})
    else:
        return JsonResponse({'valid': False})


@login_required
def validate_land_line_number(request):
    land_line_number = request.GET.get('land_line_number')
    form = forms._LandLineNumberHyperForm(data={
        'land_line_number': land_line_number
    })
    if form.is_valid():
        return JsonResponse({'valid': True})
    else:
        return JsonResponse({'valid': False})


def all_categories(request):
    return JsonResponse(models.Category.objects.all())


@hijack_decorator
@hijack_require_http_methods
def login_with_id(request, user_id):
    user = get_object_or_404(get_user_model(), pk=user_id)
    return login_user(request, user)


@method_decorator(login_required, name='dispatch')
class SliderCreateView(editViews.CreateView):
    model = models.Slider
    form_class = forms.SliderForm
    template_name = 'dashboard/slider/create.html'
    success_url = reverse_lazy('slider.index')


class SliderListView(ListView):
    model = models.Slider
    queryset = models.Slider.objects.all()
    template_name = 'dashboard/slider/slider_list.html'


class SliderUpdateView(UpdateView):
    model = models.Slider
    fields = ['name', 'banner']
    template_name = 'dashboard/slider/update.html'
    success_url = reverse_lazy('slider.index')

    def get_object(self, queryset=None):
        id = self.kwargs['id']
        return self.model.objects.get(_id=id)

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(reverse('slider.index'))

