import datetime, json

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.functional import cached_property
from django_countries.fields import CountryField
from django_extensions.db.fields import AutoSlugField
from djongo import models
from djongo.models.json import JSONField
from embed_video.fields import EmbedVideoField
from rest_framework.authtoken.models import Token
from taggit.managers import TaggableManager
from treebeard.mp_tree import MP_Node
from phonenumber_field.modelfields import PhoneNumberField
import xml.etree.cElementTree as et
from hypereditor.fields import HyperField
from zero_auth.models import AbstractUser


class ToDictionaryMixin:

    def to_dict(self):
        return forms.model_to_dict(self)


class User(AbstractUser):
    _id = models.ObjectIdField()
    email = models.EmailField(blank=True, unique=False)
    parent = models.ForeignKey('self', on_delete=models.PROTECT, default=None, null=True, blank=True)
    active = models.BooleanField(default=True)
    varification_code = models.CharField(max_length=255, default=None, null=True, blank=True)

    def __is_in_group(self, group):
        return self.groups.filter(name=group).exists()

    @cached_property
    def is_agent(self):
        return self.__is_in_group(settings.AGENT_GROUP)

    @cached_property
    def is_gco(self):
        return self.__is_in_group(settings.GCO_GROUP)

    @cached_property
    def is_editor(self):
        return self.__is_in_group(settings.EDITOR_GROUP)

    @cached_property
    def is_moderator(self):
        return self.__is_in_group(settings.MODERATOR_GROUP)

    @cached_property
    def is_admin(self):
        return self.is_superuser or self.__is_in_group(settings.ADMIN_GROUP)

    @cached_property
    def is_user(self):
        return self.__is_in_group(settings.USER_GROUP)

    @cached_property
    def is_business_owner(self):
        return self.__is_in_group(settings.BUSINESS_OWNER_GROUP)

    @cached_property
    def get_children(self):
        if self.is_superuser:
            return User.objects.all()
        users = User.objects.filter(parent=self)
        if self.is_moderator or self.is_editor:

            users = User.objects.filter(Q(parent__in=users) | Q(pk=[o.pk for o in users]))
            if self.is_editor:
                users = User.objects.filter(Q(parent__in=users) | Q(pk=[o.pk for o in users]))
        return users


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class BangladeshMap(models.Model):
    FID = models.CharField(max_length=255)
    the_geom = JSONField(blank=True, null=True)
    Div_ID = models.IntegerField(blank=True, null=True)
    Dist_ID = models.IntegerField(blank=True, null=True)
    Upz_ID = models.IntegerField(blank=True, null=True)
    Un_ID = models.IntegerField(blank=True, null=True)
    Un_UID = models.IntegerField(blank=True, null=True)
    Divi_name = models.CharField(max_length=255, blank=True, null=True)
    Dist_name = models.CharField(max_length=255, blank=True, null=True)
    Upaz_name = models.CharField(max_length=255, blank=True, null=True)
    Uni_name = models.CharField(max_length=255, blank=True, null=True)
    Area_SqKm = models.DecimalField(max_digits=20, decimal_places=12, blank=True, null=True)

    _id = models.ObjectIdField()

    objects = models.DjongoManager()

    def __str__(self):
        return f'{self.Uni_name}, {self.Upaz_name}, {self.Dist_name}, {self.Divi_name}'


class ContactNumber(models.Model):
    mobile_number = PhoneNumberField()
    verified = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.mobile_number)

    def to_dict(self):
        return {
            'mobile_number': str(self.mobile_number),
            'verified': self.verified
        }


TITLE_CHOICES = [
    ('Mr.', 'Mr.'),
    ('Mrs.', 'Mrs.'),
    ('Miss.', 'Miss.'),
    ('Dr.', 'Dr.'),
]

LOCATION_TYPE_CHOICES = [
    (1, 'Country'),
    (2, 'City'),
    (3, 'Area'),
    (4, 'Thana'),
    (5, 'Postcode'),
    (6, 'PostOffice'),
    (7, 'Division')
]


class Location(models.Model):
    _id = models.ObjectIdField()
    location_type = models.IntegerField(choices=LOCATION_TYPE_CHOICES)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, default=None)
    prism_id = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = models.DjongoManager()

    def __str__(self):
        return self.name

    @staticmethod
    def get_division_queryset():
        return Location.objects.filter(location_type=7)

    @staticmethod
    def get_city_queryset():
        return Location.objects.filter(location_type=2)

    @staticmethod
    def get_thana_queryset():
        return Location.objects.filter(location_type=4)

    @staticmethod
    def get_postcode_queryset():
        return Location.objects.filter(location_type=5)

    @staticmethod
    def get_area_queryset():
        return Location.objects.filter(location_type=3)

    def to_string(self):
        locations = []
        starts = self
        while starts:
            locations.append(starts.name)
            try:
                starts = starts.parent
            except Exception as e:
                starts = None
        return ', '.join(locations)


class PaymentMethod(models.Model):
    name = models.CharField(max_length=50, unique=True)
    _id = models.ObjectIdField()

    def __str__(self):
        return self.name


class ProfessionalAssociation(models.Model):
    name = models.CharField(max_length=255, unique=True)
    _id = models.ObjectIdField()

    def __str__(self):
        return self.name


class Certification(models.Model):
    name = models.CharField(max_length=255, unique=True)
    _id = models.ObjectIdField()

    def __str__(self):
        return self.name


""" method for checking the file is svg or not """
def validate_svg(f):
    # Find "start" word in file and get "tag" from there
    f.seek(0)
    tag = None
    try:
        for event, el in et.iterparse(f, ('start',)):
            tag = el.tag
            break
    except et.ParseError:
        pass

    # Check that this "tag" is correct
    if tag != '{http://www.w3.org/2000/svg}svg':
        raise ValidationError('Uploaded file is not an image or SVG file.')

    # Do not forget to "reset" file
    f.seek(0)

    return f


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='name', unique=True)
    display_name = models.CharField(max_length=255, null=True, blank=True, default=None, db_index=True)
    icon = models.FileField(upload_to='uploads/%Y/%m/%d/', null=True, blank=True, default=None, validators=[validate_svg])
    banner = models.ImageField(upload_to='uploads/%Y/%m/%d', null=True, blank=True, default=None)
    order = models.IntegerField(blank=True, null=True, default=9999)
    show_as_slider = models.BooleanField(default=False)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, default=None)
    _id = models.ObjectIdField()

    objects = models.DjongoManager()

    def __str__(self):
        try:
            return self.display_name if self.display_name is not None else self.name
        except Exception as e:
            return self.name

    def clean(self):
        pass

    def get_children(self):
        return Category.objects.filter(parent=self)

    def children_count(self):
        return Category.objects.filter(parent=self).count()


@receiver(post_save, sender=Category)
def auto_populate_display_name(sender, instance=None, created=False, **kwargs):
    if instance:
        display_name_builder = [instance.name]
        try:
            parent = instance.parent
            while parent is not None:
                display_name_builder.append(parent.name)
                parent = parent.parent
        except Exception as e:
            pass
        display_name_builder.reverse()
        display_name = ' > '.join(list(map(lambda x: x.strip(), display_name_builder)))
        if instance.display_name != display_name:
            instance.display_name = display_name
            instance.save()
        # import pdb; pdb.set_trace()


class LocationInfo(models.Model, ToDictionaryMixin):
    business_name = models.CharField(max_length=255)
    building = models.CharField(max_length=255, blank=True)
    street = models.CharField(max_length=255)
    land_mark = models.CharField(max_length=255, blank=True)
    area = models.CharField(max_length=255, blank=True)
    postcode = models.CharField(max_length=12, blank=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, blank=True)
    plus_code = models.CharField(max_length=255, blank=True)
    geo = JSONField(blank=True)

    class Meta:
        abstract = True

    def to_dict(self):
        dict_to_send = forms.model_to_dict(self)
        dict_to_send['loc'] = self.loc.to_dict()
        return dict_to_send

    def to_string(self):
        locations = []
        starts = self.location
        while starts:
            locations.append(starts.name)
            try:
                starts = starts.parent
            except Exception as e:
                starts = None
        return ', '.join(locations)


def my_default():
    return {'foo': 'bar'}


class ContactPersonInfo(models.Model):
    title = models.CharField(max_length=255, choices=TITLE_CHOICES)
    name = models.CharField(max_length=255)
    designation = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    mobile_no = PhoneNumberField(blank=True, null=True)
    mobile_numbers = models.ArrayModelField(model_container=ContactNumber)
    landline_no = models.CharField(max_length=20, blank=True)
    fax_no = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    social_link = JSONField(blank=True, null=True, default=None)

    class Meta:
        abstract = True


class OpenClose(models.Model, ToDictionaryMixin):
    open_from = models.TimeField(blank=True, default=datetime.time(9,0))
    open_till = models.TimeField(blank=True, default=datetime.time(17,0))
    leisure_start   = models.TimeField(blank=True, null=True, default=None)
    leisure_end     = models.TimeField(blank=True, null=True, default=None)
    open_24h    = models.BooleanField(default=False)
    close       = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __str__(self):
        if self.open_24h:
            return "Open 24h"
        elif self.close:
            return "Close"
        else:
            return "Open From %s to %s.\n Leisure start From %s to %s" % (self.open_from, self.open_till, self.leisure_start, self.leisure_end)


class HoursOfOperation(models.Model, ToDictionaryMixin):
    display_hours_of_operation = models.BooleanField(default=True)
    monday = models.EmbeddedModelField(model_container=OpenClose)
    tuesday = models.EmbeddedModelField(model_container=OpenClose)
    wednesday = models.EmbeddedModelField(model_container=OpenClose)
    thursday = models.EmbeddedModelField(model_container=OpenClose)
    friday = models.EmbeddedModelField(model_container=OpenClose)
    saturday = models.EmbeddedModelField(model_container=OpenClose)
    sunday = models.EmbeddedModelField(model_container=OpenClose)

    class Meta:
        abstract = True

    def __str__(self):
        return "Hours of Operation"

    def to_dict(self):
        return {
            'monday': self.monday.to_dict(),
            'tuesday': self.tuesday.to_dict(),
            'wednesday': self.wednesday.to_dict(),
            'thursday': self.thursday.to_dict(),
            'friday': self.friday.to_dict(),
            'saturday': self.saturday.to_dict(),
            'sunday': self.sunday.to_dict(),
        }


NO_OF_EMPLOYEES_CHOICES = [
    ('1-5', '1-5'),
    ('6-20', '6-20'),
    ('21-50', '21-50'),
    ('51-100', '51-100'),
    ('101-500', '101-500'),
    ('500+', '500+')
]

YEARLY_TURNOVER_CHOICES = [
    ('N/A', 'N/A'),
    ('1-500000', '1-500000'),
    ('500001-1000000', '500001-1000000'),
    ('1000001-5000000', '1000001-5000000'),
    ('5000001-20000000', '5000001-20000000'),
    ('20000001-50000000', '20000001-50000000'),
    ('50000001+', '50000001+')
]


class UploadedImage(models.Model):
    _id = models.ObjectIdField()
    image = models.ImageField(upload_to='uploads/%Y/%m/%d/')

    def __str__(self):
        return self.image.url


class UploadedVideo(models.Model):
    _id = models.ObjectIdField()
    video = models.FileField(upload_to='uploads/%Y/%m/%d/', validators=[FileExtensionValidator(allowed_extensions=['avi', 'wmv', 'mov', 'mp4'])])

    def __str__(self):
        return self.video.url


class SoftDeleteQuerySet(models.QuerySet):

    def delete(self):
        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(deleted_at=None)

    def dead(self):
        return self.exclude(deleted_at=None)


class SoftDeleteManager(models.DjongoManager):
    def __init__(self, *args, **kwargs):
        self.alive_only = kwargs.pop('alive_only', False)
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        queryset = SoftDeleteQuerySet(model=self.model, using=self.db)
        if self.alive_only:
            return queryset.filter(deleted_at=None)
        return queryset

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class BusinessInfo(models.Model):
    _id = models.ObjectIdField()

    location = models.EmbeddedModelField(model_container=LocationInfo)
    contact = models.EmbeddedModelField(model_container=ContactPersonInfo)
    hours_of_operation = models.EmbeddedModelField(model_container=HoursOfOperation)

    description = models.TextField(blank=True)

    year_of_establishment = models.IntegerField()
    annual_turnover = models.CharField(max_length=30, choices=YEARLY_TURNOVER_CHOICES, blank=True, null=True)
    no_of_employees = models.CharField(max_length=30, choices=NO_OF_EMPLOYEES_CHOICES, blank=True)
    professional_associations = models.ArrayReferenceField(ProfessionalAssociation, blank=True)
    certifications = models.ArrayReferenceField(Certification, blank=True)

    # Files
    logo = models.ImageField(upload_to='uploads/%Y/%m/%d/', blank=True)
    cover_photo = models.ImageField(upload_to='uploads/%Y/%m/%d/', blank=True)
    photos = models.ArrayReferenceField(UploadedImage, blank=True)
    videos = models.ArrayReferenceField(UploadedVideo, blank=True)
    embed_video = EmbedVideoField(verbose_name='Embed Video (Youtube, Vimeo etc)', blank=True)

    accepted_payment_methods = models.ArrayReferenceField(PaymentMethod, blank=True)

    keywords = models.ArrayReferenceField(Category, blank=True)

    added_by = models.ForeignKey(User, on_delete=models.PROTECT, db_index=True)
    edit_by  = models.ForeignKey(User, on_delete=models.PROTECT, related_name='edit_by', db_index=True, default=None)
    reviewed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reviewed_by', default=None, db_index=True)
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='approved_by', default=None, db_index=True)
    rejected_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='rejected_by', default=None, db_index=True)

    reviewed_at = models.DateTimeField(default=None, null=True, db_index=True)
    approved_at = models.DateTimeField(default=None, null=True, db_index=True)
    rejected_at = models.DateTimeField(default=None, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_at = models.DateTimeField(auto_now=True, db_index=True)
    deleted_at = models.DateField(default=None, db_index=True)

    REJECTED = 0; PENDING = 1; REVIEWED = 2; APPROVED = 3
    status = models.IntegerField(choices=[
        (PENDING, 'PENDING'),
        (REVIEWED, 'REVIEWED'),
        (APPROVED, 'APPROVED'),
        (REJECTED, 'REJECTED')
    ], default=1)

    # reviews
    total_reviews = models.IntegerField(blank=True, null=True, default=0)
    aggregate_rating = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True, default=0.0)

    objects = SoftDeleteManager()
    dobjects = models.DjongoManager()

    def delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self):
        super().delete()


class MobileNumberData(models.Model):
    _id = models.ObjectIdField()
    name = models.CharField(max_length=255, null=True, default=None)
    designation = models.CharField(max_length=255, default=None, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(default=None, blank=True, null=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, blank=True)
    store_name = models.CharField(max_length=255,blank=True, null=True, verbose_name='Organaization')
    numbers = models.ListField(blank=True)
    land_line_numbers = models.ListField(blank=True, null=True, default=[])
    photos = models.ArrayReferenceField(UploadedImage, blank=True, null=True)
    categories = models.ArrayReferenceField(Category, blank=True, null=True)

    REJECTED = 0; PENDING = 1; REVIEWED = 2; APPROVED = 3
    status = models.IntegerField(choices=[
        (PENDING, 'PENDING'),
        (REVIEWED, 'REVIEWED'),
        (APPROVED, 'APPROVED'),
        (REJECTED, 'REJECTED')
    ], default=1)

    added_by = models.ForeignKey(User, on_delete=models.PROTECT)
    edit_by  = models.ForeignKey(User, on_delete=models.PROTECT, default=None, related_name='m_edit_by')
    reviewed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='m_reviewed_by', default=None)
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='m_approved_by', default=None)
    rejected_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='m_rejected_by', default=None)

    reviewed_at = models.DateTimeField(default=None, null=True, db_index=True)
    approved_at = models.DateTimeField(default=None, null=True, db_index=True)
    rejected_at = models.DateTimeField(default=None, null=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateField(default=None)

    objects = SoftDeleteManager()


class Page(models.Model):
    title = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='title', unique=True)
    content = HyperField(default=None)

    def __str__(self):
        return self.title


class Snippet(models.Model):
    title = models.CharField(max_length=255)
    code = models.CharField(max_length=25, unique=True)
    content = HyperField(default=None)


class Slider(models.Model):
    _id = models.ObjectIdField()

    name = models.CharField(max_length=255, null=True, blank=False, default=None)
    banner = models.ImageField(upload_to='uploads/%Y/%m/%d', null=True, blank=True, default=None)

    objects = SoftDeleteManager()
    dobjects = models.DjongoManager()

    def __str__(self):
        return self.name


class Review(models.Model):
    _id = models.ObjectIdField
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)
    business_id = models.ForeignKey(BusinessInfo, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, null=True, blank=True)
    comment = models.CharField(max_length=500, null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = SoftDeleteManager()
    dobjects = models.DjongoManager()

    def delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self):
        super().delete()

    def __str__(self):
        return self.comment
