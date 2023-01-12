from django.db import models

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
    citizenship = models.ForeignKey('controlled_list.Nationality', on_delete=models.PROTECT)
    id_number = models.CharField(max_length=50)
    email = models.EmailField(max_length=100, unique=True)

    OCCUPATION_CHOICES = [('ceu', 'CEU'), ('other', 'Other')]
    occupation = models.CharField(max_length=20, choices=OCCUPATION_CHOICES, default='ceu')

    OCCUPATION_TYPE_CHOICES = [('student', 'Student'), ('staff', 'Staff'), ('faculty', 'Faculty')]
    occupation_type = models.CharField(max_length=20, blank=True, null=True, choices=OCCUPATION_TYPE_CHOICES)

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
        self.card_number = self.get_next_card_number()
        super(Researcher, self).save()

    class Meta:
        db_table = 'research_researcher'


class ResearcherDegree(models.Model):
    id = models.AutoField(primary_key=True)
    degree = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'research_degree'


class Request(models.Model):
    id = models.AutoField(primary_key=True)
    researcher = models.ForeignKey('Researcher', on_delete=models.PROTECT)
    request_date = models.DateTimeField(blank=True, auto_now_add=True)

    class Meta:
        db_table = 'research_request'


class RequestItems(models.Model):
    id = models.AutoField(primary_key=True)
    request = models.ForeignKey('Request', on_delete=models.PROTECT)
    ORIGIN = [('FA', 'Finding Aids'), ('L', 'Library'), ('FL', 'Film Library')]
    item_origin = models.CharField(max_length=3, choices=ORIGIN)
    archival_reference_number = models.CharField(max_length=30)
    identifier = models.CharField(max_length=20)
    title = models.CharField(max_length=200, blank=True, null=True)
    request_date = models.DateTimeField(blank=True, auto_now_add=True)
    closing_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'research_request_items'
