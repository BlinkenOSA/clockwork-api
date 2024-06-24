class DigitalVersionIdentifierGenerator:
    def __init__(self, finding_aids_entity):
        self.finding_aids_entity = finding_aids_entity

    def detect(self):
        if self.finding_aids_entity.digitalversion_set.count() > 0 or self.finding_aids_entity.digital_version_exists:
            return True
        else:
            if self.finding_aids_entity.container.digital_version_exists:
                return True
        return False

    def detect_available_online(self):
        if self.finding_aids_entity.available_online or self.finding_aids_entity.digital_version_online:
            return True
        else:
            if self.finding_aids_entity.container.digital_version_online:
                return True
        return False

    def generate_identifier(self):
        barcode = ''
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
