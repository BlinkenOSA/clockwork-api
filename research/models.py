import datetime

from django.db import models

from clockwork_api.fields.email_null_field import EmailNullField
from clockwork_api.mixins.detect_protected_mixin import DetectProtectedMixin


# Create your models here.
class Researcher(models.Model, DetectProtectedMixin):
    id = models.AutoField(primary_key=True)
    card_number = models.IntegerField(blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    address_hungary = models.CharField(max_length=200, blank=True, null=True)
    address_abroad = models.CharField(max_length=200, blank=True, null=True)
    city_hungary = models.CharField(max_length=100, blank=True, null=True)
    city_abroad = models.CharField(max_length=100, blank=True, null=True)
    country = models.ForeignKey('authority.Country', on_delete=models.PROTECT, blank=True, null=True)
    citizenship = models.ForeignKey('controlled_list.Nationality', on_delete=models.PROTECT, blank=True, null=True)
    id_number = models.CharField(max_length=50)
    email = EmailNullField(max_length=100, unique=True, blank=True, null=True)

    OCCUPATION_CHOICES = [('ceu', 'CEU'), ('other', 'Other')]
    occupation = models.CharField(max_length=20, choices=OCCUPATION_CHOICES, default='ceu')
    occupation_other = models.CharField(max_length=300, blank=True, null=True)

    OCCUPATION_TYPE_CHOICES = [('student', 'Student'), ('staff', 'Staff'), ('faculty', 'Faculty'), ('other', 'Other')]
    occupation_type = models.CharField(max_length=20, blank=True, null=True, choices=OCCUPATION_TYPE_CHOICES)
    occupation_type_other = models.CharField(max_length=300, blank=True, null=True)

    department = models.CharField(max_length=200, blank=True, null=True)
    employer_or_school = models.CharField(max_length=200, blank=True, null=True)
    degree = models.ForeignKey('ResearcherDegree', blank=True, null=True, on_delete=models.PROTECT)

    research_subject = models.TextField(blank=True, null=True)
    research_will_be_published = models.BooleanField(default=False)
    date_is_tentative = models.BooleanField(default=False)

    active = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)

    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    def get_next_card_number(self):
        researcher = Researcher.objects.filter().order_by('-card_number').first()
        if researcher:
            return researcher.card_number + 1
        else:
            return 1

    @property
    def name(self):
        return "%s, %s" % (self.last_name, self.first_name)

    def save(self, **kwargs):
        if not self.card_number:
            self.card_number = self.get_next_card_number()
        super(Researcher, self).save()

    class Meta:
        db_table = 'research_researchers'


class ResearcherDegree(models.Model):
    id = models.AutoField(primary_key=True)
    degree = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'research_researcher_degrees'


class ResearcherVisit(models.Model):
    id = models.AutoField(primary_key=True)
    researcher = models.ForeignKey('Researcher', on_delete=models.PROTECT)
    check_in = models.DateTimeField(auto_now_add=True)
    check_out = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'research_researcher_visits'


class Request(models.Model):
    id = models.AutoField(primary_key=True)
    researcher = models.ForeignKey('Researcher', on_delete=models.PROTECT)
    created_date = models.DateTimeField(blank=True, auto_now_add=True)
    request_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'research_requests'


class RequestItem(models.Model):
    id = models.AutoField(primary_key=True)
    request = models.ForeignKey('Request', on_delete=models.PROTECT)
    STATUS_VALUES = [('1', 'In Queue'), ('2', 'Pending'), ('3', 'Processed and prepared'),
                     ('4', 'Returned'), ('5', 'Reshelved'), ('9', 'Uploaded')]
    status = models.CharField(max_length=1, choices=STATUS_VALUES, default='1')
    ORIGIN = [('FA', 'Finding Aids'), ('L', 'Library'), ('FL', 'Film Library')]
    item_origin = models.CharField(max_length=3, choices=ORIGIN)
    container = models.ForeignKey('container.Container', blank=True, null=True, on_delete=models.CASCADE)
    identifier = models.CharField(max_length=20, blank=True, null=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    quantity = models.CharField(max_length=200, blank=True, null=True)
    return_date = models.DateTimeField(blank=True, null=True)
    reshelve_date = models.DateTimeField(blank=True, null=True)
    ordering = models.CharField(max_length=50, blank=True, null=True)

    def save(self, **kwargs):
        researcher = self.request.researcher
        requested_items_count = RequestItem.objects.filter(
            request__researcher=researcher,
            item_origin=self.item_origin,
            status='2'
        ).count()

        # Check if there are one free slots from 10 for the newly created item. If yes, change status to 2.
        if self.status == '1':
            if requested_items_count < 10:
                self.status = '2'

        # If return is happening, write the return date into the record.
        if self.status == '4':
            if requested_items_count < 10:
                requested_items_next_in_queue = RequestItem.objects.filter(
                    request__researcher=researcher,
                    item_origin=self.item_origin,
                    status='1'
                ).order_by('request__request_date')
                if requested_items_next_in_queue.count() > 0:
                    requested_item_next_in_queue = requested_items_next_in_queue.first()
                    requested_item_next_in_queue.status = '2'
                    requested_item_next_in_queue.save()

            if not self.return_date:
                self.return_date = datetime.datetime.now()

        if self.status == '5':
            if not self.reshelve_date:
                self.reshelve_date = datetime.datetime.now()

        # Save ordering
        if self.item_origin == 'FA':
            if self.container:
                self.ordering = "%s%04d" % (self.container.archival_unit.sort, self.container.container_no)
            else:
                self.ordering = ''
        else:
            self.ordering = self.identifier

        super(RequestItem, self).save(**kwargs)

    class Meta:
        db_table = 'research_request_items'
