import unicodedata

from django.db import models


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


def fold(s: str) -> str:
    return (
        unicodedata.normalize('NFKD', s or '')
        .encode('ascii', 'ignore')
        .decode('ascii')
        .lower()
        .strip()
    )

# --- SimHash helpers (64-bit) over character 3-grams ---
def _trigrams(s: str):
    s = f"  {s}  "  # padding to keep edges informative
    return [s[i:i+3] for i in range(len(s) - 2)]

def _hash64(s: str) -> int:
    # a tiny, fast 64-bit non-cryptographic hash
    # (splitmix-like; good enough for SimHash purposes)
    x = 0x9E3779B97F4A7C15
    h = 0
    for ch in s:
        x ^= ord(ch)
        x = (x * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        x ^= (x >> 30)
        x = (x * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        h ^= x
    return h & 0xFFFFFFFFFFFFFFFF

def simhash64(s: str) -> int:
    # Character-3gram SimHash
    grams = _trigrams(s)
    if not grams:
        return 0
    bits = [0]*64
    for g in grams:
        h = _hash64(g)
        for i in range(64):
            bits[i] += 1 if (h >> i) & 1 else -1
    out = 0
    for i, val in enumerate(bits):
        if val >= 0:
            out |= (1 << i)
    return out & 0xFFFFFFFFFFFFFFFF

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