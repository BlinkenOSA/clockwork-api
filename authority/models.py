from django.db import models


class Country(models.Model):
    id = models.AutoField(primary_key=True)
    alpha2 = models.CharField(max_length=2, blank=True, null=True)
    alpha3 = models.CharField(max_length=3)
    wiki_url = models.CharField(max_length=150, blank=True, null=True)
    authority_url = models.CharField(max_length=200, blank=True, null=True)
    country = models.CharField(unique=True, max_length=100)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.country

    class Meta:
        db_table = 'authority_countries'
        ordering = ['country']


class Language(models.Model):
    id = models.AutoField(primary_key=True)
    iso_639_1 = models.CharField(max_length=10, blank=True, null=True)
    iso_639_2 = models.CharField(max_length=10, blank=True, null=True)
    iso_639_3 = models.CharField(max_length=10, blank=True, null=True)
    wiki_url = models.CharField(max_length=150, blank=True, null=True)
    authority_url = models.CharField(max_length=200, blank=True, null=True)
    language = models.CharField(unique=True, max_length=100)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.language

    class Meta:
        db_table = 'authority_languages'
        unique_together = ['iso_639_1', 'iso_639_2']
        ordering = ['language']


class Place(models.Model):
    id = models.AutoField(primary_key=True)
    wiki_url = models.CharField(max_length=150, blank=True, null=True)
    authority_url = models.CharField(max_length=200, blank=True, null=True)
    place = models.CharField(unique=True, max_length=100)
    other_url = models.CharField(max_length=150, blank=True, null=True)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.place

    class Meta:
        db_table = 'authority_places'
        ordering = ['place']


class Person(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    wiki_url = models.CharField(max_length=150, blank=True, null=True)
    authority_url = models.CharField(max_length=150, blank=True, null=True)
    other_url = models.CharField(max_length=150, blank=True, null=True)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return ', '.join((self.last_name, self.first_name))

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
        unique_together = ('last_name', 'first_name')


class Corporation(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=250)
    wiki_url = models.CharField(max_length=150, blank=True, null=True)
    authority_url = models.CharField(max_length=150, blank=True, null=True)
    other_url = models.CharField(max_length=150, blank=True, null=True)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'authority_corporations'
        ordering = ['name']


class CorporationOtherFormat(models.Model):
    id = models.AutoField(primary_key=True)
    corporation = models.ForeignKey('authority.Corporation', on_delete=models.CASCADE)
    language = models.ForeignKey('authority.Language', blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=250, unique=True)

    class Meta:
        db_table = 'authority_corporations_other_formats'
        ordering = ['name']


class Genre(models.Model):
    id = models.AutoField(primary_key=True)
    genre = models.CharField(unique=True, max_length=50)
    wiki_url = models.CharField(max_length=150, blank=True, null=True)
    authority_url = models.CharField(max_length=150, blank=True, null=True)
    other_url = models.CharField(max_length=150, blank=True, null=True)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.genre

    class Meta:
        db_table = 'authority_genres'
        ordering = ['genre']


class Subject(models.Model):
    id = models.AutoField(primary_key=True)
    subject = models.CharField(unique=True, max_length=50)
    wiki_url = models.CharField(max_length=150, blank=True, null=True)
    authority_url = models.CharField(max_length=150, blank=True, null=True)
    other_url = models.CharField(max_length=150, blank=True, null=True)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.subject

    class Meta:
        db_table = 'authority_subjects'
        ordering = ['subject']