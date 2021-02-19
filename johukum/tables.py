import django_tables2 as tables
from johukum import models

class BusinessInfoTable(tables.Table):

    business_name = tables.Column(
        verbose_name='Business Name',
        accessor=tables.A('location.business_name'),
        orderable=False
    )

    status = tables.TemplateColumn(
        verbose_name='Status',
        template_name='dashboard/manage_data/row_status.html',
        accessor=tables.A('status'))

    actions = tables.TemplateColumn(
        verbose_name='Actions',
        template_name='dashboard/manage_data/row_actions.html',
        orderable=False)

    class Meta:
        model = models.BusinessInfo
        fields = ['business_name', 'added_by', 'created_at', 'modified_at', 'status']
        attrs = {'class': 'table table-hover'}

class MobileNumberDataTable(tables.Table):

    status = tables.TemplateColumn(
        verbose_name='Status',
        template_name='dashboard/manage_data/row_status.html',
        accessor=tables.A('status'))

    actions = tables.TemplateColumn("""
        <a class="btn btn-xs btn-info" href="{% url 'mobile_data.show' id=record.id %}">View</a>
        <a class="btn btn-xs btn-primary" href="{% url 'mobile_data.update' id=record.id %}">Update</a>
        <a onclick="return confirm('Are you sure you want to delete this?')" class="btn btn-xs btn-danger" href="{% url 'mobile_data.delete' id=record.id %}">Delete</a>
    """)

    class Meta:
        model = models.MobileNumberData
        fields = ['store_name', 'status', 'actions']

class LocationTable(tables.Table):
    TEMPLATE = """<a class="btn btn-xs btn-success" href="{% url 'locations.edit' id=record.pk %}">Edit</a>
            <a onclick="return confirm('Are you sure you want to delete this?')" class="btn btn-xs btn-default" href="{% url 'locations.delete' id=record.pk %}">Delete</a>"""
    Actions = tables.TemplateColumn(TEMPLATE)
    class Meta:
        model = models.Location
        fields = ['location_type', 'name', 'parent',]
        attrs = {'class': 'table table-hover'}


class PaymentMethodTable(tables.Table):
    TEMPLATE = """<a class="btn btn-xs btn-success" href="{% url 'payment_methods.update' id=record.pk %}">Edit</a>
             <a onclick="return confirm('Are you sure you want to delete this?')" class="btn btn-xs btn-default" href="{% url 'payment_methods.delete' id=record.pk %}">Delete</a>"""
    Actions = tables.TemplateColumn(TEMPLATE)
    class Meta:
        model = models.PaymentMethod
        fields = ['name']


class ProfessionalAssociationTable(tables.Table):
    TEMPLATE = """<a class="btn btn-xs btn-success" href="{% url 'professional_associations.update'  id=record.pk%}">Edit</a>
              <a onclick="return confirm('Are you sure you want to delete this?')" class="btn btn-xs btn-default" href="{% url 'professional_associations.delete'  id=record.pk%}">Delete</a>"""
    Actions = tables.TemplateColumn(TEMPLATE)
    class Meta:
        model = models.ProfessionalAssociation
        fields = ['name']



class CertificationTable(tables.Table):
    TEMPLATE = """<a class="btn btn-xs btn-success" href="{% url 'certifications.update' id=record.pk %}">Edit</a>
              <a onclick="return confirm('Are you sure you want to delete this?')" class="btn btn-xs btn-default" href="{% url 'certifications.delete' id=record.pk %}">Delete</a>"""
    Actions = tables.TemplateColumn(TEMPLATE)
    class Meta:
        model = models.Certification
        fields = ['name']
