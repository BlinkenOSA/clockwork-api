import uuid as uuid
from typing import Optional

from django.db import models

from clockwork_api.mixins.detect_protected_mixin import DetectProtectedMixin


class ArchivalUnit(models.Model, DetectProtectedMixin):
    """
    Represents an archival description unit within a hierarchical structure.

    An archival unit belongs to a specific level:
        - F  = Fonds
        - SF = Subfonds
        - S  = Series

    The model stores:
        - hierarchical relationships via ``parent`` and ``children``
        - archival reference codes (for sorting, display, and identifiers)
        - descriptive metadata such as title, acronym, and themes
        - calculated fields (sort key, reference code, full title)

    The unit's position in the hierarchy is determined by:
        fonds, subfonds, series, and level.

    Methods are provided to:
        - get parent fonds or subfonds
        - set the sort key
        - generate full titles
        - generate reference codes
        - automatically update the related ISAD record upon save
    """

    # ------------------------------------------------------------
    # Core identity and relations
    # ------------------------------------------------------------
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.PROTECT)
    theme = models.ManyToManyField('controlled_list.ArchivalUnitTheme', blank=True)

    # ------------------------------------------------------------
    # Hierarchical identifiers
    # ------------------------------------------------------------
    fonds = models.IntegerField(db_index=True)
    subfonds = models.IntegerField(default=0, db_index=True)
    series = models.IntegerField(default=0, db_index=True)

    # Sorting field (derived)
    sort = models.CharField(max_length=12, blank=True)

    # ------------------------------------------------------------
    # Titles and descriptive metadata
    # ------------------------------------------------------------
    title = models.CharField(max_length=500, blank=True, null=True)
    title_full = models.CharField(max_length=2000, blank=True, null=True)
    title_original = models.CharField(max_length=500, blank=True, null=True)
    original_locale = models.ForeignKey('controlled_list.Locale', blank=True, null=True, on_delete=models.PROTECT)
    acronym = models.CharField(max_length=50, blank=True, null=True)

    # Reference code fields (derived)
    reference_code = models.CharField(max_length=20, db_index=True)
    reference_code_id = models.CharField(max_length=20, db_index=True)

    # ------------------------------------------------------------
    # Status fields
    # ------------------------------------------------------------
    level = models.CharField(max_length=2)
    status = models.CharField(max_length=10, default='Final')
    ready_to_publish = models.BooleanField(default=False)

    # ------------------------------------------------------------
    # Audit metadata
    # ------------------------------------------------------------
    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    # ------------------------------------------------------------
    # Hierarchy helpers
    # ------------------------------------------------------------
    def get_fonds(self) -> "ArchivalUnit":
        """
        Returns the fonds-level archival unit for this item.

        Returns:
            ArchivalUnit: The fonds-level ancestor or self if already at level F.
        """
        if self.level == 'F':
            return self
        elif self.level == 'SF':
            return self.parent
        else:
            return self.parent.parent

    def get_subfonds(self) -> Optional["ArchivalUnit"]:
        """
        Returns the subfonds-level archival unit for this item.

        Returns:
            ArchivalUnit | None:
                - None if the unit is at fonds level (F)
                - The unit itself if level SF
                - The parent subfonds if deeper than SF
        """
        if self.level == 'F':
            return None
        elif self.level == 'SF':
            return self
        else:
            return self.parent

    # ------------------------------------------------------------
    # Field derivation helpers
    # ------------------------------------------------------------
    def set_sort(self) -> None:
        """
        Generates a sortable key based on fonds/subfonds/series.

        Format: ``%04d%04d%04d`` so lexical order matches numeric hierarchy.
        """
        self.sort = f"{self.fonds:04d}{self.subfonds:04d}{self.series:04d}"

    def set_title_full(self) -> None:
        """
        Constructs the full hierarchical title for display.

        The logic varies depending on level:
            - F:   HU OSA X  <title>
            - SF:  HU OSA X-Y  <parent fonds title>  [+ ': ' + own title if applicable]
            - S: hierarchical combination of fonds + subfonds + own title
        """
        if self.level == "F":
            self.title_full = f"{self.reference_code} {self.title}"

        elif self.level == "SF":
            fonds_title = self.parent.title
            if self.subfonds == 0:
                self.title_full = f"{self.reference_code} {fonds_title}"
            else:
                self.title_full = f"{self.reference_code} {fonds_title}: {self.title}"

        else:
            # Series or deeper
            subfonds_title = self.parent.title
            fonds_title = self.parent.parent.title

            if self.level == "S" and self.subfonds == 0:
                self.title_full = f"{self.reference_code} {fonds_title}: {self.title}"
            else:
                self.title_full = (
                    f"{self.reference_code} {fonds_title}: {subfonds_title}: {self.title}"
                )

    def set_reference_code(self) -> None:
        """
        Generates the standard OSA reference code and reference_code_id.

        Examples:
            F:   Reference code: HU OSA 123         reference_code_id: hu_osa_123
            SF:  Reference code: HU OSA 123-4       reference_code_id: hu_osa_123_4
            S:   Reference code: HU OSA 123-4-56    reference_code_id: hu_osa_123_4_56
        """
        if self.level == "F":
            self.reference_code = f"HU OSA {self.fonds}"
            self.reference_code_id = f"hu_osa_{self.fonds}"

        elif self.level == "SF":
            self.reference_code = f"HU OSA {self.fonds}-{self.subfonds}"
            self.reference_code_id = f"hu_osa_{self.fonds}-{self.subfonds}"

        else:
            self.reference_code = (
                f"HU OSA {self.fonds}-{self.subfonds}-{self.series}"
            )
            self.reference_code_id = (
                f"hu_osa_{self.fonds}-{self.subfonds}-{self.series}"
            )

    # ------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------
    def __str__(self) -> str:
        """Returns the standard archival reference string."""
        return ' '.join((self.reference_code, self.title))

    def save(self, **kwargs) -> None:
        """
        Overrides save() to update calculated fields and sync the ISAD record.

        Order of operations:
            1. Update sort key
            2. Update reference code + reference_code_id
            3. Update full title
            4. If an ISAD object is attached, update its title
            5. Save the model normally
        """
        self.set_sort()
        self.set_reference_code()
        self.set_title_full()

        if hasattr(self, 'isad'):
            isad = self.isad
            isad.title = self.title
            isad.save()

        super(ArchivalUnit, self).save()

    # ------------------------------------------------------------
    # Meta
    # ------------------------------------------------------------
    class Meta:
        db_table = 'archival_units'
        ordering = ['fonds', 'subfonds', 'series']
        unique_together = ("fonds", "subfonds", "series", "level")
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['fonds']),
            models.Index(fields=['subfonds']),
            models.Index(fields=['series']),
            models.Index(fields=['fonds', 'subfonds', 'series'], name='fsfs_idx'),
            models.Index(fields=['title']),
            models.Index(fields=['reference_code']),
        ]