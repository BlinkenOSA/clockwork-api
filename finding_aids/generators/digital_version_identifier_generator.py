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
            2. Entity has digital_version_exists flag set
            3. Container has digital_version_exists flag set

        Returns:
            bool: True if a digital version is detected, otherwise False.
        """
        if self.finding_aids_entity.digitalversion_set.count() > 0 or self.finding_aids_entity.digital_version_exists:
            return True
        else:
            if self.finding_aids_entity.container.digital_version_exists:
                return True
        return False

    def detect_available_online(self):
        """
        Detects whether a digital version is available online.

        Resolution order:
            1. Entity has related DigitalVersion records marked online (available_online property)
            2. Entity has digital_version_online flag set
            3. Container has digital_version_online flag set

        Returns:
            bool: True if online availability is detected, otherwise False.
        """
        if self.finding_aids_entity.available_online or self.finding_aids_entity.digital_version_online:
            return True
        else:
            if self.finding_aids_entity.container.digital_version_online:
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
                - container.legacy_id
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
        if self.finding_aids_entity.digitalversion_set.count() > 0 or self.finding_aids_entity.digital_version_exists:
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
        else:
            if self.finding_aids_entity.container.digital_version_exists:
                if self.finding_aids_entity.container.barcode:
                    return self.finding_aids_entity.container.barcode
                if self.finding_aids_entity.container.legacy_id:
                    return self.finding_aids_entity.container.legacy_id
                return "%s_%04d" % (
                    self.finding_aids_entity.archival_unit.reference_code.replace(" ", "_").replace("-", "_"),
                    self.finding_aids_entity.container.container_no
                )
        return barcode
