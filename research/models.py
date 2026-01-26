import datetime
import uuid

from django.db import models

from clockwork_api.fields.email_null_field import EmailNullField
from clockwork_api.mixins.detect_protected_mixin import DetectProtectedMixin


# Create your models here.
class Researcher(models.Model, DetectProtectedMixin):
    """
    Core model representing a registered researcher.

    A researcher record stores identity, contact, affiliation, and research
    intent information used for registration, approval, and request management.
    Each researcher is assigned a sequential ``card_number`` on first save.

    Notes
    -----
    - ``email`` uses :class:`clockwork_api.fields.email_null_field.EmailNullField`
      and is unique when provided.
    - ``card_number`` is assigned by querying the current maximum value and
      incrementing it. In high-concurrency scenarios, additional safeguards
      (e.g., database-side sequence/locking) may be needed to avoid duplicates.
    """

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

    captcha = models.CharField(max_length=1, blank=True, null=True)

    HOW_DO_YOU_KNOW_CHOICES = [
        ('web', 'OSA Web page'),
        ('event', 'Event at OSA'),
        ('verzio', 'Verzio'),
        ('ceu', 'CEU'),
        ('contacts', 'Personal Contacts'),
        ('media', 'Media'),
        ('other', 'Other')
    ]
    how_do_you_know_osa = models.CharField(max_length=20, blank=True, null=True, choices=HOW_DO_YOU_KNOW_CHOICES)
    how_do_you_know_osa_other = models.TextField(blank=True, null=True)

    active = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)

    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    def get_next_card_number(self):
        """
        Returns the next available researcher card number.

        The method finds the current highest ``card_number`` and returns the
        next integer value. If no researcher exists with a card number, it
        returns 1.

        Returns
        -------
        int
            Next card number.
        """
        researcher = Researcher.objects.filter().order_by('-card_number').first()
        if researcher:
            return researcher.card_number + 1
        else:
            return 1

    @property
    def name(self):
        """
        Returns the researcher's display name in "Last, First" format.
        """
        return "%s, %s" % (self.last_name, self.first_name)

    def save(self, **kwargs):
        """
        Overrides save to assign a card number when missing.

        Ensures:
            - ``card_number`` is set on first save using :meth:`get_next_card_number`.
        """
        if not self.card_number:
            self.card_number = self.get_next_card_number()
        super(Researcher, self).save()

    class Meta:
        db_table = 'research_researchers'


class ResearcherDegree(models.Model):
    """
    Controlled vocabulary for researcher degree values.
    """

    id = models.AutoField(primary_key=True)
    degree = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'research_researcher_degrees'


class ResearcherVisit(models.Model):
    """
    Stores a check-in/check-out visit record for a researcher.

    Visits are created on check-in (``check_in`` set automatically) and may be
    completed by setting ``check_out``.
    """

    id = models.AutoField(primary_key=True)
    researcher = models.ForeignKey('Researcher', on_delete=models.PROTECT)
    check_in = models.DateTimeField(auto_now_add=True)
    check_out = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'research_researcher_visits'


class Request(models.Model):
    """
    Represents a research request created by a researcher.

    A request groups one or more :class:`RequestItem` entries and stores the
    creation timestamp and an optional requested datetime.
    """

    id = models.AutoField(primary_key=True)
    researcher = models.ForeignKey('Researcher', on_delete=models.PROTECT)
    created_date = models.DateTimeField(blank=True, auto_now_add=True)
    request_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'research_requests'


class RequestItem(models.Model):
    """
    Represents a single requested item within a research request.

    Request items can originate from multiple systems (finding aids, library,
    film library) and progress through a status workflow.

    Queueing rules
    --------------
    The save logic enforces a simple per-researcher, per-origin limit:
        - at most 10 items can be in status ``'2'`` (Pending) at a time
        - items start in ``'1'`` (In Queue) and are promoted to ``'2'`` when a slot is free
        - when an item is returned (status ``'4'``) or uploaded (status ``'9'``),
          the next queued item is promoted to pending (if any)

    Additional behavior
    -------------------
    - When status becomes Returned (``'4'``) or Uploaded (``'9'``), ``return_date`` is set if missing.
    - When status becomes Reshelved (``'5'``), ``reshelve_date`` is set if missing.
    - ``ordering`` is computed to support sorting:
        - For finding aids items, uses ``archival_unit.sort`` + container number when available.
        - Otherwise uses ``identifier``.
    """

    id = models.AutoField(primary_key=True)
    request = models.ForeignKey('Request', on_delete=models.CASCADE)
    STATUS_VALUES = [('1', 'In Queue'), ('2', 'Pending'), ('3', 'Processed and prepared'),
                     ('4', 'Returned'), ('5', 'Reshelved'), ('9', 'Uploaded')]
    status = models.CharField(max_length=1, choices=STATUS_VALUES, default='1')
    ORIGIN = [('FA', 'Finding Aids'), ('L', 'Library'), ('FL', 'Film Library')]
    item_origin = models.CharField(max_length=3, choices=ORIGIN)
    container = models.ForeignKey('container.Container', blank=True, null=True, on_delete=models.CASCADE)
    identifier = models.CharField(max_length=100, blank=True, null=True)
    library_id = models.IntegerField(blank=True, null=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    quantity = models.CharField(max_length=200, blank=True, null=True)
    return_date = models.DateTimeField(blank=True, null=True)
    reshelve_date = models.DateTimeField(blank=True, null=True)
    ordering = models.CharField(max_length=50, blank=True, null=True)

    def save(self, **kwargs):
        """
        Overrides save to enforce queue rules and derive dates/order keys.

        Behavior includes:
            - promotion from queue to pending when fewer than 10 pending items exist
            - promotion of the next queued item when an item is returned/uploaded
            - auto-populating ``return_date`` and ``reshelve_date`` on status transitions
            - computing ``ordering`` based on origin and container/identifier
        """
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
        if self.status == '4' or self.status == '9':
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


class RequestItemRestriction(models.Model):
    """
    Stores restriction request data for a single requested item.

    This model attaches a single restriction form to a :class:`RequestItem` via
    a 1:1 relation and stores the submitted justification and acceptance flags.
    """

    id = models.AutoField(primary_key=True)
    request_item = models.OneToOneField('RequestItem', on_delete=models.CASCADE, related_name='restriction')

    # Restricted material
    restricted_uuid = models.UUIDField(default=uuid.uuid4, db_index=True)

    # Restricted form data
    research_organisation = models.TextField(blank=True)
    research_subject = models.TextField(blank=True)
    motivation = models.TextField(blank=True)

    conditions_accepted = models.BooleanField(default=False)

    class Meta:
        db_table = 'research_request_items_restrictions'


class RequestItemPart(models.Model):
    """
    Links a request item to a finding aids entity at a more granular level.

    This model supports partial access/decision workflows for restricted
    materials by representing "parts" (e.g., items/pages/files) tied to a
    :class:`finding_aids.FindingAidsEntity`.

    Notes
    -----
    The ``status`` field appears intended to use :attr:`STATUS_CHOICES` defined
    on this model, but currently references ``RequestItem.STATUS_VALUES`` in the
    field definition.
    """

    id = models.AutoField(primary_key=True)
    request_item = models.ForeignKey('RequestItem', on_delete=models.CASCADE)
    finding_aids_entity = models.ForeignKey('finding_aids.FindingAidsEntity', on_delete=models.CASCADE)

    STATUS_CHOICES = [('new', 'New'), ('approved', 'Approved'), ('approved_on_site', 'Approved for on-site'),
                      ('rejected', 'Rejected'), ('lifted', 'Lifted')]
    status = models.CharField(max_length=20, choices=RequestItem.STATUS_VALUES, default='new', db_index=True)

    # If restricted, this field will be filled
    decision_date = models.DateTimeField(blank=True, null=True)
    decision_by = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'research_request_items_parts'

