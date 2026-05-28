from digitization.models import DigitalVersion


class DigitalVersionIdentifierGenerator:
    """
    Generates and detects digital-version identifiers for finding aids entities.

    This helper centralizes digitization detection logic across two levels:
        - entity-level digitization (DigitalVersion records or entity flags)
        - container-level digitization (container flags and identifiers)

    Identifier formats:
        - Entity-level L1 (folder):
            <archival_unit_ref>_<container_no>_<folder_no>
        - Entity-level L2 (item):
            <archival_unit_ref>_<container_no>_<folder_no>_<sequence_no>
        - Container fallback:
            1. container.barcode
            2. container.legacy_id
            3. <archival_unit_ref>_<container_no>

    Where:
        <archival_unit_ref> is normalized by replacing spaces and hyphens with underscores.
        Numeric components are zero-padded to 4 digits.
    """

    def __init__(self, finding_aids_entity):
        """
        Args:
            finding_aids_entity: FindingAidsEntity instance to inspect.
        """
        self.finding_aids_entity = finding_aids_entity

    def detect(self):
        """
        Detects whether any digital version exists for the entity.

        Resolution order:
            1. Entity has related DigitalVersion records
            2. Container has related DigitalVersion records

        Returns:
            bool: True if a digital version is detected, otherwise False.
        """
        if self.finding_aids_entity.digital_versions.count() > 0:
            return True

        if self.finding_aids_entity.container.digital_versions.count() > 0:
            return True

        return False

    def detect_available_online(self):
        """
        Detects whether a digital version is available online.

        Resolution order:
            1. Entity has related DigitalVersion records marked online (available_online property)
            2. Container has related DigitalVersion records marked online (available_online property)

        Returns:
            bool: True if online availability is detected, otherwise False.
        """
        if DigitalVersion.objects.filter(
            finding_aids_entity=self.finding_aids_entity,
            available_online=True
        ).count() > 0:
            return True

        if DigitalVersion.objects.filter(
            container=self.finding_aids_entity.container,
            available_online=True
        ).count() > 0:
            return True

        return False

    def generate_identifier(self):
        """
        Computes a stable identifier used for digital object references.

        Resolution order:
            1. Entity-level identifier:
                - If entity has DigitalVersion records or digital_version_exists flag
                - Uses description level to produce folder vs item identifiers
            2. Container-level identifier (when only container digitization exists):
                - container.barcode (preferred)
                - generated <archival_unit_ref>_<container_no>

        This identifier is used for:
            - catalog indexing (Solr fields like digital_version_barcode)
            - IIIF/derivative addressing (when applicable)
            - client-side linking to digitized representations

        Returns:
            str: identifier string; empty string when no identifier can be generated.
        """
        barcode = ''

        # Entity-level digital versions or flags
        if self.finding_aids_entity.digital_versions.count() > 0:
            if self.finding_aids_entity.description_level == 'L1':
                return "%s_%04d_%04d" % (
                    self.finding_aids_entity.archival_unit.reference_code.replace(" ", "_").replace("-", "_"),
                    self.finding_aids_entity.container.container_no,
                    self.finding_aids_entity.folder_no
                )
            else:
                return "%s_%04d_%04d_%04d" % (
                    self.finding_aids_entity.archival_unit.reference_code.replace(" ", "_").replace("-", "_"),
                    self.finding_aids_entity.container.container_no,
                    self.finding_aids_entity.folder_no,
                    self.finding_aids_entity.sequence_no
                )

        # Container-level digitization fallback
        if self.finding_aids_entity.container.digital_versions.count() > 0:
            if self.finding_aids_entity.container.barcode:
                return self.finding_aids_entity.container.barcode
            return "%s_%04d" % (
                self.finding_aids_entity.archival_unit.reference_code.replace(" ", "_").replace("-", "_"),
                self.finding_aids_entity.container.container_no
            )

        return barcode
