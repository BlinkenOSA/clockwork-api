import re

from django.core.exceptions import ObjectDoesNotExist

from rest_framework.exceptions import ValidationError
from archival_unit.models import ArchivalUnit
from container.models import Container
from finding_aids.models import FindingAidsEntity


class FileNameParser:
    def __init__(self, filename):
        self.filename = filename
        self.doi, _, self.extension = filename.rpartition(".")
        self.archival_unit = None
        self.container = None
        self.finding_aids_entity = None

    def matches_any_pattern(self):
        """
        Validates whether a submitted filename matches any supported DOI patterns.

        The workflow endpoints accept access copy filenames that encode a DOI-like
        identifier in the filename prefix. This helper validates the full filename,
        including extension.

        Supported examples:
            - HU_OSA_386_1_1_0001.pdf
            - HU_OSA_386_1_1_0001_0001.jpg
            - HU_OSA_386_1_1_0001_0001_P001.tif
            - HU_OSA_386_1_1_0001_0001_0001_P001.mp4
            - HU_OSA_11112222.mkv

        Returns:
            bool: True if the filename matches a supported pattern.
        """
        patterns = [
            # HU_OSA_386_1_1_0001
            r'HU_OSA_\d{1,3}_\d{1,3}_\d{1,3}_\d{4}\.[a-zA-Z0-9]+$',

            # HU_OSA_386_1_1_0001_0001
            r'HU_OSA_\d{1,3}_\d{1,3}_\d{1,3}_\d{4}_\d{4}\.[a-zA-Z0-9]+$',

            # HU_OSA_386_1_1_0001_0001_P001
            r'HU_OSA_\d{1,3}_\d{1,3}_\d{1,3}_\d{4}_\d{4}_P\d{3}\.[a-zA-Z0-9]+$',

            # HU_OSA_384_0_2_0023_0001_P050_A (special cases for the Bartok Collection)
            r'HU_OSA_\d{1,3}_\d{1,3}_\d{1,3}_\d{4}_\d{4}_P\d{3}_[a-zA-Z]\.[a-zA-Z0-9]+$',

            # HU_OSA_386_1_1_0001_0001_0001
            r'HU_OSA_\d{1,3}_\d{1,3}_\d{1,3}_\d{4}_\d{4}_\d{4}\.[a-zA-Z0-9]+$',

            # HU_OSA_386_1_1_0001_0001_0001_P001
            r'HU_OSA_\d{1,3}_\d{1,3}_\d{1,3}_\d{4}_\d{4}_\d{4}_P\d{3}\.[a-zA-Z0-9]+$',

            # HU_OSA_11112222
            r'HU_OSA_\d{8}\.[a-zA-Z0-9]+$'
        ]
        return any(re.fullmatch(p, self.filename) for p in patterns)

    def resolve_archival_unit_or_container(self):
        """
        Resolves a DOI-like identifier into archival objects.

        Based on identifier shape, resolves:
            - archival unit
            - container
            - optionally a finding aids folder/item record
            - derived level indicator (container/folder/item)

        Returns:
            dict: Keys:
                - archival_unit (ArchivalUnit or None)
                - container (Container or None)
                - finding_aids_entity (FindingAidsEntity or None)
                - level (str or None)

        Raises:
            ValidationError: If the identifier refers to non-existent objects.
        """
        level = None
        parts = self.doi.split("_")

        # HU_OSA_11112222
        if len(parts) == 3:
            try:
                self.container = Container.objects.get(barcode=self.doi)
                self.archival_unit = self.container.archival_unit
                level = 'container'
            except ObjectDoesNotExist:
                raise ValidationError({'error': 'No container exists with this barcode'})
        else:
            self._set_archival_unit(int(parts[2]), int(parts[3]), int(parts[4]))
            self._set_container(int(parts[5]))

            # HU_OSA_386_1_1_0001
            if len(parts) == 6:
                level = 'container'

            # HU_OSA_386_1_1_0001_0001
            elif len(parts) == 7:
                self._set_finding_aids_entity(int(parts[6]), 0)
                level = 'folder'

            # HU_OSA_386_1_1_0001_0001_P001 OR HU_OSA_386_1_1_0001_0001_0001
            elif len(parts) == 8:
                if "P" in self.doi:
                    self._set_finding_aids_entity(int(parts[6]), 0)
                    level = "folder"
                else:
                    self._set_finding_aids_entity(int(parts[6]), int(parts[7]))
                    level = 'item'

            # HU_OSA_386_1_1_0001_0001_0001_P001 OR HU_OSA_386_1_1_0001_0001_P001_A
            elif len(parts) == 9:
                if 'P' in parts[7]:
                    self._set_finding_aids_entity(int(parts[6]), 0)
                    level = 'folder'
                elif 'P' in parts[8]:
                    self._set_finding_aids_entity(int(parts[6]), int(parts[7]))
                    level = 'item'
                else:
                    pass

        return {
            'archival_unit': self.archival_unit,
            'container': self.container,
            'finding_aids_entity': self.finding_aids_entity,
            'level': level
        }

    def get_doi(self):
        return self.doi

    def _set_archival_unit(self, fonds, subfonds, series):
        """
        Sets archival_unit by fonds/subfonds/series numeric identifiers.

        Args:
            fonds: Fonds number.
            subfonds: Subfonds number.
            series: Series number.

        Raises:
            ValidationError: If no matching archival unit exists.
        """
        try:
            self.archival_unit = ArchivalUnit.objects.get(fonds=fonds, subfonds=subfonds, series=series)
        except ObjectDoesNotExist:
            raise ValidationError({'error': 'No Archival Unit exists with these specifications'})

    def _set_container(self, container_no):
        """
        Sets container by archival unit and container number.

        Args:
            container_no: Container number within the unit.

        Raises:
            ValidationError: If no matching container exists.
        """
        try:
            self.container = Container.objects.get(archival_unit=self.archival_unit, container_no=container_no)
        except ObjectDoesNotExist:
            raise ValidationError({'error': 'No Container record exists with these specifications'})

    def _set_finding_aids_entity(self, folder_no, sequence_no):
        """
        Sets finding_aids_entity by container + folder + sequence.

        Args:
            folder_no: Folder number.
            sequence_no: Sequence number (0 for folder-level records).

        Raises:
            ValidationError: If no matching record exists.
        """
        try:
            self.finding_aids_entity = FindingAidsEntity.objects.get(
                container=self.container, folder_no=folder_no, sequence_no=sequence_no
            )
        except ObjectDoesNotExist:
            raise ValidationError({'error': 'No Folder / Item record exists with these specifications'})