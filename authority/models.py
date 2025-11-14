import unicodedata

from django.db import models

from authority.helpers.similarity_helpers import fold, simhash64
from clockwork_api.mixins.detect_protected_mixin import DetectProtectedMixin


class Country(models.Model):
    id = models.AutoField(primary_key=True)
    alpha2 = models.CharField(max_length=2, blank=True, null=True)
    alpha3 = models.CharField(max_length=3)
    wikidata_id = models.CharField(max_length=20, blank=True, null=True)
    wiki_url = models.CharField(max_length=200, blank=True, null=True)
    authority_url = models.CharField(max_length=200, blank=True, null=True)
    country = models.CharField(unique=True, max_length=100)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.country.strip()

    class Meta:
        db_table = 'authority_countries'
        ordering = ['country']


class Language(models.Model):
    id = models.AutoField(primary_key=True)
    iso_639_1 = models.CharField(max_length=10, blank=True, null=True)
    iso_639_2 = models.CharField(max_length=10, blank=True, null=True)
    iso_639_3 = models.CharField(max_length=10, blank=True, null=True)
    wikidata_id = models.CharField(max_length=20, blank=True, null=True)
    wiki_url = models.CharField(max_length=200, blank=True, null=True)
    authority_url = models.CharField(max_length=200, blank=True, null=True)
    language = models.CharField(unique=True, max_length=100)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.language.strip()

    class Meta:
        db_table = 'authority_languages'
        unique_together = ['iso_639_1', 'iso_639_2']
        ordering = ['language']


class Place(models.Model):
    id = models.AutoField(primary_key=True)
    place = models.CharField(unique=True, max_length=100)
    wikidata_id = models.CharField(max_length=20, blank=True, null=True)
    wiki_url = models.CharField(max_length=200, blank=True, null=True)
    authority_url = models.CharField(max_length=200, blank=True, null=True)
    other_url = models.CharField(max_length=150, blank=True, null=True)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.place.strip()

    class Meta:
        db_table = 'authority_places'
        ordering = ['place']


class Person(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    full_name_folded = models.CharField(max_length=210, db_index=True, blank=True, default="")
    simhash64 = models.PositiveBigIntegerField(db_index=True, default=0)

    wikidata_id = models.CharField(max_length=20, blank=True, null=True)
    wiki_url = models.CharField(max_length=200, blank=True, null=True)
    authority_url = models.CharField(max_length=200, blank=True, null=True)
    other_url = models.CharField(max_length=150, blank=True, null=True)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def save(self, *args, **kwargs):
        full = f"{(self.first_name or '').strip()} {(self.last_name or '').strip()}".strip()
        folded = fold(full)
        self.full_name_folded = folded
        self.simhash64 = simhash64(folded)
        super().save(*args, **kwargs)

    def __str__(self):
        last = (self.last_name or "").strip()
        first = (self.first_name or "").strip()
        return ', '.join((last, first)) if last or first else str(self.id)

    class Meta:
        db_table = 'authority_people'
        ordering = ['last_name', 'first_name']
        unique_together = ('last_name', 'first_name')


class PersonOtherFormat(models.Model):
    id = models.AutoField(primary_key=True)
    person = models.ForeignKey('authority.Person', on_delete=models.CASCADE)
    language = models.ForeignKey('authority.Language', blank=True, null=True, on_delete=models.PROTECT)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    class Meta:
        db_table = 'authority_people_other_formats'
        ordering = ['last_name', 'first_name']
        unique_together = ('last_name', 'first_name', 'person')


class Corporation(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=250)
    wikidata_id = models.CharField(max_length=20, blank=True, null=True)
    wiki_url = models.CharField(max_length=200, blank=True, null=True)
    authority_url = models.CharField(max_length=200, blank=True, null=True)
    other_url = models.CharField(max_length=150, blank=True, null=True)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.name.strip()

    class Meta:
        db_table = 'authority_corporations'
        ordering = ['name']


class CorporationOtherFormat(models.Model):
    id = models.AutoField(primary_key=True)
    corporation = models.ForeignKey('authority.Corporation', on_delete=models.CASCADE)
    language = models.ForeignKey('authority.Language', blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=250)

    class Meta:
        db_table = 'authority_corporations_other_formats'
        ordering = ['name']
        unique_together = ('corporation', 'name')


class Genre(models.Model):
    id = models.AutoField(primary_key=True)
    genre = models.CharField(unique=True, max_length=50)
    wikidata_id = models.CharField(max_length=20, blank=True, null=True)
    wiki_url = models.CharField(max_length=200, blank=True, null=True)
    authority_url = models.CharField(max_length=200, blank=True, null=True)
    other_url = models.CharField(max_length=150, blank=True, null=True)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.genre.strip()

    class Meta:
        db_table = 'authority_genres'
        ordering = ['genre']


class Subject(models.Model):
    id = models.AutoField(primary_key=True)
    subject = models.CharField(unique=True, max_length=50)
    wikidata_id = models.CharField(max_length=20, blank=True, null=True)
    wiki_url = models.CharField(max_length=200, blank=True, null=True)
    authority_url = models.CharField(max_length=200, blank=True, null=True)
    other_url = models.CharField(max_length=150, blank=True, null=True)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.subject.strip()

    class Meta:
        db_table = 'authority_subjects'
        ordering = ['subject']