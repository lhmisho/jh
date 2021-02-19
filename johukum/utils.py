from django import forms
from django.views.generic import TemplateView
from django.db.models import Count
import datetime
from johukum import models
from django.conf import settings
from django_select2.forms import Select2Widget
from django_select2 import views as select2_views
from bson import ObjectId, regex
class BusinessInfoReportFilterForm(forms.Form):
    from_date = forms.DateField(widget=forms.HiddenInput(), required=False)
    till_date = forms.DateField(widget=forms.HiddenInput(), required=False)
    agent = forms.ModelChoiceField(queryset=models.User.objects.filter(groups__name=settings.AGENT_GROUP), widget=Select2Widget, required=False)


class BusinessInfoReportView(TemplateView):
    template_name = 'dashboard/reports/reports.html'
    model_class = None
    approval = True

    def get_data(self):
        group_dict = {
            '_id':"$added_by_id", 
        }
        group_dict.update(self.get_total_q())

        if self.approval:
            group_dict.update(self.get_approved_q())
            group_dict.update(self.get_reviewed_q())
            group_dict.update(self.get_rejected_q())
            group_dict.update(self.get_pending_q())

        group_dict = {
            '$group': group_dict
        }
        lookup_dict = {
            "$lookup": {
                "from": "johukum_user",
                "localField": "_id",
                "foreignField": "_id",
                "as": "user"
            }
        }
        pipelines = []
        match_dict = self.get_match_q()
        if match_dict:
            pipelines.append(match_dict)
        pipelines.append(group_dict)
        pipelines.append(lookup_dict)
        return self.transform(self.model_class.objects.mongo_aggregate(pipelines))

    def transform(self, mongo_dataset):
        result = []

        for item in mongo_dataset:

            tmp = {}
            for k, v in item.items():
                if k == 'user':
                    tmp_user = {}
                    if len(v) > 0:
                        for k2, v2 in v[0].items():
                            tmp_user[k2] = v2
                        tmp[k] = tmp_user
                else:
                    tmp[k] = v
            result.append(tmp)
        return result

    def get_match_q(self):
        
        if len(self.request.GET) > 0:
            form = self.get_filter_form()
            if form.is_valid():
                till_date = form.cleaned_data['till_date'] if form.cleaned_data['till_date'] is not None else datetime.datetime.today()
                from_date = form.cleaned_data['from_date'] if form.cleaned_data['from_date'] is not None else datetime.datetime(1970, 1, 1)
                result = {
                    '$match': { 
                        'created_at': {
                            '$lte': datetime.datetime.combine(till_date, datetime.datetime.max.time()),
                            '$gte': datetime.datetime.combine(from_date, datetime.datetime.min.time())
                        } 
                    }
                }
                if form.cleaned_data['agent'] is not None:
                    result['$match']['added_by_id'] = form.cleaned_data['agent'].pk
                return result
            return None
        else:
            return None
 
    def get_total_q(self):
        return {'total': {'$sum': 1}}

    def get_approved_q(self):
        return self.__sub_q_helper('approved', models.BusinessInfo.APPROVED)
    
    def get_reviewed_q(self):
        return self.__sub_q_helper('reviewed', models.BusinessInfo.REVIEWED)
    
    def get_rejected_q(self):
        return self.__sub_q_helper('rejected', models.BusinessInfo.REJECTED)
    
    def get_pending_q(self):
        return self.__sub_q_helper('pending', models.BusinessInfo.PENDING)

    def __sub_q_helper(self, k, v):
        return {
            k: {
                '$sum': {
                    '$cond': {
                        'if': {
                            '$eq': ['$status', v],
                        },
                        'then': 1,
                        'else': 0
                    }
                }
            }
        }

    def get_filter_form(self):
        if len(self.request.GET) > 0:
            form = BusinessInfoReportFilterForm(self.request.GET)
        else:
            form = BusinessInfoReportFilterForm
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data'] = self.get_data()
        all = 0
        rejected = 0
        reviewed = 0
        approved = 0
        pending = 0
        for item in context['data']:
            all += item['total']
            if self.approval:
                rejected += item['rejected']
                pending += item['pending']
                reviewed += item['reviewed']
                approved += item['approved']
        context['all'] = all
        context['rejected'] = rejected
        context['pending'] = pending
        context['reviewed'] = reviewed
        context['approved'] = approved
        context['filter_form'] = self.get_filter_form()
        return context

class EditorInfoReportFilterForm(forms.Form):
    from_date = forms.DateField(widget=forms.HiddenInput(), required=False)
    till_date = forms.DateField(widget=forms.HiddenInput(), required=False)
    editor = forms.ModelChoiceField(queryset=models.User.objects.filter(groups__name=settings.EDITOR_GROUP), widget=Select2Widget, required=False)


class EditorInfoReportView(TemplateView):

    def get_filter_form(self):
        if len(self.request.GET) > 0:
            form = EditorInfoReportFilterForm(self.request.GET)
        else:
            form = EditorInfoReportFilterForm
        return form

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        editor_filter = {}
        editor_dict = {}
        filters = {}
        reviewed_filter = {}
        rejected_filter = {}
        common_filters = {}
        approved_total = 0
        reviewed_total = 0
        rejected_total = 0
        all_total = 0
        pending_total = 0
        form = self.get_filter_form()


        filters.update({'deleted_at': None})
        reviewed_filter.update({'deleted_at': None})
        rejected_filter.update({'deleted_at': None})

        # getting data from filter ..........
        if len(self.request.GET) > 0:
            if form.is_valid():
                till_date = form.cleaned_data['till_date'] if form.cleaned_data['till_date'] is not None else datetime.datetime.today()
                from_date = form.cleaned_data['from_date'] if form.cleaned_data['from_date'] is not None else datetime.datetime(1970, 1, 1)

                common_range = {
                    '$gte': datetime.datetime.combine(from_date, datetime.datetime.min.time()),
                    '$lt': datetime.datetime.combine(till_date, datetime.datetime.max.time())
                }


                filters.update({ 'approved_at': common_range })
                reviewed_filter.update({ 'reviewed_at': common_range })
                rejected_filter.update({ 'rejected_at': common_range })

                if form.cleaned_data['editor'] is not None:
                    editor = form.cleaned_data['editor'].pk
                    editor_filter = {
                        '_id': editor
                    }
                    filters.update({'approved_by_id':editor})
                    rejected_filter.update({'rejected_by_id':editor})
                    reviewed_filter.update({'reviewed_by_id':editor})

        ## fetching all editor user
        editors = models.User.objects.filter(groups__name='Editor', **editor_filter)

        ## count of all approved, reviewed and rejected data
        approved = models.BusinessInfo.objects.mongo_aggregate([
            {'$match':filters},
            {"$group": {'_id': {'approved_by': "$approved_by_id"}, 'total': { '$sum': 1}}}
        ])

        rejected = models.BusinessInfo.objects.mongo_aggregate([
            {'$match': rejected_filter},
            {"$group": {'_id': {'rejected_by': "$rejected_by_id"}, 'total': { '$sum': 1}}}
        ])
        reviewed = models.BusinessInfo.objects.mongo_aggregate([
            {'$match': reviewed_filter},
            {"$group": {'_id': {'reviewed_by': "$reviewed_by_id"}, 'total': { '$sum': 1}}}
        ])

        ## transfer cursor to dict
        approved = list(approved)
        rejected = list(rejected)
        reviewed = list(reviewed)

        ## editor dict initialization
        editor_dict = [{
            '_id':ed._id,
            'username':ed.username,
            'first_name':ed.first_name,
            'last_name': ed.last_name,
            'approved': 0,
            'reviewed': 0,
            'rejected': 0,
            'pending': 0,
            'total': 0,
            'shouldShow': False,
            'sub_total': 0,
            'approved_total': 0,
            'obj': ed
        } for ed in editors]

        ## adding all approved, rejected and reviewed data on editor dict
        for i in range(len(approved)):
            for editor in editor_dict:
                if str(editor['_id']) == str(approved[i]['_id']['approved_by']):
                    editor['approved'] = approved[i]['total']
                    approved_total += editor['approved']

        for i in range(len(rejected)):
            for editor in editor_dict:
                if str(editor['_id']) == str(rejected[i]['_id']['rejected_by']):
                    editor['rejected'] = rejected[i]['total']
                    rejected_total += editor['rejected']

        for i in range(len(reviewed)):
            for editor in editor_dict:
                if str(editor['_id']) == str(reviewed[i]['_id']['reviewed_by']):
                    editor['reviewed'] = reviewed[i]['total']
                    reviewed_total += editor['reviewed']
        # for editor in editor_dict:
        #     editor['pending'] = models.BusinessInfo.objects.filter(
        #         added_by__in=editor['obj'].get_children,
        #         status=models.BusinessInfo.PENDING,
        #         deleted_at=None).filter(**common_filters).count()

        for editor in editor_dict:
            editor['pending'] = models.BusinessInfo.objects.mongo_find(
                {'status': models.BusinessInfo.PENDING, 'added_by_id': {'$in':[i.pk for i in editor['obj'].get_children]},'deleted_at': None}
            ).count()
            pending_total += editor['pending']

        for editor in editor_dict:
            editor['total'] = editor['rejected'] + editor['reviewed']
            editor['shouldShow'] = (editor['rejected'] + editor['reviewed'] + editor['approved']) > 0
            all_total += editor['total']

        for editor in editor_dict:
            editor['sub_total'] = editor['approved'] + editor['rejected'] + editor['reviewed']

        # for editor in editor_dict:
        #     approved_total += editor['approved']

        context['approved_total'] = approved_total
        context['reviewed_total'] = reviewed_total
        context['rejected_total'] = rejected_total
        context['pending_total'] = pending_total
        context['all_total'] = all_total
        context['editor_dict'] = editor_dict
        context['filter_form'] = self.get_filter_form()

        return context


class AutoResponseView(select2_views.AutoResponseView):
    pass


def business_data_mobile_number_is_unique(number):
    return models.BusinessInfo.objects.mongo_find({
        'contact.mobile_numbers': {
            '$elemMatch': {
                'mobile_number': {
                    '$regex': number
                }
            }
        }
    }).count() == 0
