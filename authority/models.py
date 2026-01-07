import unicodedata

from django.db import models

from authority.helpers.similarity_helpers import fold, simhash64
from clockwork_api.mixins.detect_protected_mixin import DetectProtectedMixin


class Country(models.Model):
    """
    Represents a country authority record.

    This model stores ISO country codes, Wikidata links, authority references,
    and various metadata used in controlled vocabularies and authority records.

    Attributes:
        id (int):
            Primary key.

        alpha2 (str | None):
            ISO 3166-1 alpha-2 country code (2 letters), optional.

        alpha3 (str):
            ISO 3166-1 alpha-3 country code (3 letters).

        wikidata_id (str | None):
            Identifier for the corresponding Wikidata entity.

        wiki_url (str | None):
            URL of the corresponding Wikipedia page.

        authority_url (str | None):
            URL of an external authority record for this country.

        country (str):
            Official country name. Must be unique.

        user_created (str):
            Username of the creator, if tracked.

        date_created (datetime):
            Timestamp when the record was created.

        user_updated (str):
            Username of the last updater.

        date_updated (datetime | None):
            Timestamp of the last update.
    """
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

    def __str__(self) -> str:
        """Returns the cleaned country name."""
        return self.country.strip()

    class Meta:
        db_table = 'authority_countries'
        ordering = ['country']


class Language(models.Model):
    """
    Represents a language authority record.

    Stores ISO 639 codes, Wikidata and Wikipedia references, and a
    canonical language name. Intended for use as a controlled vocabulary
    in other parts of the system (e.g. descriptions, names in other formats).

    Attributes:
        id (int):
            Primary key.

        iso_639_1 (str | None):
            ISO 639-1 two-letter language code (e.g. "en", "fr").
            Optional.

        iso_639_2 (str | None):
            ISO 639-2 three-letter language code (bibliographic or terminologic).

        iso_639_3 (str | None):
            ISO 639-3 three-letter language code (comprehensive).

        wikidata_id (str | None):
            Identifier for the language entity in Wikidata.

        wiki_url (str | None):
            URL to the corresponding Wikipedia page.

        authority_url (str | None):
            URL to an external authority record.

        language (str):
            Canonical language name (e.g. "English"). Must be unique.

        user_created (str):
            Username of the user who created the record.

        date_created (datetime):
            Timestamp when the record was created.

        user_updated (str):
            Username of the last user who updated the record.

        date_updated (datetime | None):
            Timestamp of the last update.
    """
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

    def __str__(self) -> str:
        """Returns the cleaned language name."""
        return self.language.strip()

    class Meta:
        db_table = 'authority_languages'
        unique_together = ['iso_639_1', 'iso_639_2']
        ordering = ['language']


class Place(models.Model):
    """
    Represents a controlled-vocabulary place authority entry.

    A place may correspond to a city, region, settlement, geographic
    landmark, or any named location relevant to archival description.

    Attributes:
        id (int):
            Primary key.

        place (str):
            Canonical name of the place. Must be unique.

        wikidata_id (str | None):
            Optional identifier pointing to a Wikidata entity.

        wiki_url (str | None):
            Optional URL to the corresponding Wikipedia page.

        authority_url (str | None):
            Optional external authority reference (e.g., VIAF, LCNAF).

        other_url (str | None):
            Additional reference URL, often institution-specific.

        user_created (str):
            Username of the creator.

        date_created (datetime):
            Auto-generated timestamp at record creation.

        user_updated (str):
            Username of the last updater.

        date_updated (datetime | None):
            Auto-generated timestamp for last update.
    """
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

    def __str__(self) -> str:
        """Returns the cleaned place name for display."""
        return self.place.strip()

    class Meta:
        db_table = 'authority_places'
        ordering = ['place']


class Person(models.Model):
    """
    Represents a person authority entry used in controlled vocabularies.

    Each person consists of a first and last name, plus multiple optional
    authority identifiers and external reference URLs. Additionally,
    normalized name forms are computed and stored to support
    similarity-based search and deduplication.

    Key Features:
        - `full_name_folded` stores an ASCII-folded, normalized version of the
          person's full name. This helps with accent-insensitive searches.
        - `simhash64` stores a 64-bit SimHash fingerprint of the folded name,
          allowing detection of near-duplicates or fuzzy matching.
        - External authority references (Wikidata, Wikipedia, VIAF, etc.)
          can be stored for interoperability.
        - Audit fields track creation and updates.

    Attributes:
        first_name (str):
            Person's given name.

        last_name (str):
            Person's family name.

        full_name_folded (str):
            Folded and normalized full name. Automatically maintained.

        simhash64 (int):
            64-bit hash of folded name for similarity matching.
            Automatically maintained.

        wikidata_id, wiki_url, authority_url, other_url (str | None):
            External authority references.

        user_created, date_created, user_updated, date_updated:
            Standard audit fields.
    """
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

    def save(self, *args, **kwargs) -> None:
        """
        Overrides save() to automatically compute normalized and hashed
        name representations.

        Steps:
            1. Combines first and last names into a single full name.
            2. Applies `fold()` to remove accents and normalize characters.
            3. Computes a 64-bit SimHash fingerprint from the folded name.
            4. Saves the model normally.

        Folding and hashing allow high-performance similarity matching
        (e.g. detecting “John Smith” vs “Jón Smíth”).
        """
        full = f"{(self.first_name or '').strip()} {(self.last_name or '').strip()}".strip()
        folded = fold(full)
        self.full_name_folded = folded
        self.simhash64 = simhash64(folded)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """
        Returns a display-friendly representation: "Last, First".

        If both names are missing (should be rare), falls back to the ID.
        """
        last = (self.last_name or "").strip()
        first = (self.first_name or "").strip()
        return f"{last}, {first}" if (last or first) else str(self.id)

    class Meta:
        db_table = 'authority_people'
        ordering = ['last_name', 'first_name']
        unique_together = ('last_name', 'first_name')


class PersonOtherFormat(models.Model):
    """
    Represents an alternative name format for a Person.

    These records store variations of a person's first and last name in
    different languages or transliteration systems. This is especially useful
    for archival or authority systems where individuals may appear in multiple
    scripts or cultural naming conventions.

    Examples:
        - Transliteration: "Aleksandr" vs "Alexander"
        - Language variation: "Juan" vs "John"
        - Script variation: Cyrillic, Latin, Greek, etc.

    Attributes:
        id (int):
            Primary key.

        person (Person):
            The person to whom this alternative name belongs.

        language (Language | None):
            Optional language specifying the context of this name variant.

        first_name (str):
            Alternative given name.

        last_name (str):
            Alternative family name.
    """
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
    """
    Represents a corporate body authority entry.

    This model is used for organizations, institutions, companies,
    government bodies, or other corporate entities that appear in
    archival descriptions or authority records.

    Each corporation may be linked to external authority systems
    such as Wikidata, Wikipedia, or other institutional authority
    registries.

    Attributes:
        id (int):
            Primary key.

        name (str):
            Canonical name of the corporation. Must be unique.

        wikidata_id (str | None):
            Identifier for the corresponding Wikidata entity.

        wiki_url (str | None):
            URL to the corresponding Wikipedia page.

        authority_url (str | None):
            URL to an external authority record (e.g. VIAF).

        other_url (str | None):
            Additional reference URL.

        user_created (str):
            Username of the creator.

        date_created (datetime):
            Timestamp when the record was created.

        user_updated (str):
            Username of the last updater.

        date_updated (datetime | None):
            Timestamp of the last update.
    """
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

    def __str__(self) -> str:
        """Returns the cleaned corporation name."""
        return self.name.strip()

    class Meta:
        db_table = 'authority_corporations'
        ordering = ['name']


class CorporationOtherFormat(models.Model):
    """
    Represents an alternative name format for a Corporation.

    This model stores additional name variants for a corporate body,
    typically used for:
        - Names in different languages
        - Transliteration variants
        - Historical or alternative spellings

    These variants allow better searchability and interoperability with
    external authority systems.

    Attributes:
        id (int):
            Primary key.

        corporation (Corporation):
            The corporate entity to which this name variant belongs.

        language (Language | None):
            Optional language context for this name variant.

        name (str):
            Alternative name of the corporation.
    """
    id = models.AutoField(primary_key=True)
    corporation = models.ForeignKey('authority.Corporation', on_delete=models.CASCADE)
    language = models.ForeignKey('authority.Language', blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=250)

    class Meta:
        db_table = 'authority_corporations_other_formats'
        ordering = ['name']
        unique_together = ('corporation', 'name')


class Genre(models.Model):
    """
    Represents a genre authority entry.

    Genres are controlled vocabulary terms used to classify materials
    by form, style, or category (e.g. "Photographs", "Correspondence",
    "Reports"). They are typically applied across multiple archival
    descriptions and entities.

    Each genre may be linked to external authority systems to support
    interoperability and semantic alignment.

    Attributes:
        id (int):
            Primary key.

        genre (str):
            Canonical genre term. Must be unique.

        wikidata_id (str | None):
            Identifier for the corresponding Wikidata entity.

        wiki_url (str | None):
            URL to the corresponding Wikipedia page.

        authority_url (str | None):
            URL to an external authority record.

        other_url (str | None):
            Additional reference URL.

        user_created (str):
            Username of the user who created the record.

        date_created (datetime):
            Timestamp when the record was created.

        user_updated (str):
            Username of the last user who updated the record.

        date_updated (datetime | None):
            Timestamp of the last update.
    """
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

    def __str__(self) -> str:
        """Returns the cleaned genre label."""
        return self.genre.strip()

    class Meta:
        db_table = 'authority_genres'
        ordering = ['genre']


class Subject(models.Model):
    """
    Represents a subject authority entry.

    Subjects are controlled vocabulary terms used to describe the topical
    content of archival materials (e.g. "Human rights", "Cold War",
    "Political movements"). They support consistent indexing and
    improved discovery across the system.

    Subject terms may optionally be aligned with external authority
    systems such as Wikidata or institutional thesauri.

    Attributes:
        id (int):
            Primary key.

        subject (str):
            Canonical subject term. Must be unique.

        wikidata_id (str | None):
            Identifier for the corresponding Wikidata entity.

        wiki_url (str | None):
            URL to the corresponding Wikipedia page.

        authority_url (str | None):
            URL to an external authority record.

        other_url (str | None):
            Additional reference URL.

        user_created (str):
            Username of the user who created the record.

        date_created (datetime):
            Timestamp when the record was created.

        user_updated (str):
            Username of the last user who updated the record.

        date_updated (datetime | None):
            Timestamp of the last update.
    """
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
        """Returns the cleaned subject label."""
        return self.subject.strip()

    class Meta:
        db_table = 'authority_subjects'
        ordering = ['subject']