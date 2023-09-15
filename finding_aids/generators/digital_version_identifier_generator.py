class DigitalVersionIdentifierGenerator:
    def __init__(self, finding_aids_entity):
        self.finding_aids_entity = finding_aids_entity

    def detect(self):
        if self.finding_aids_entity.digital_version_exists:
            return True
        else:
            if self.finding_aids_entity.container.digital_version_exists:
                return True
        return False

    def detect_available_online(self):
        if self.finding_aids_entity.digital_version_online:
            return True
        else:
            if self.finding_aids_entity.container.digital_version_online:
                return True
        return False

    def generate_identifier(self):
        if self.finding_aids_entity.description_level == 'L1':
            barcode = "%s-%04d-%03d" % (
                self.finding_aids_entity.archival_unit.reference_code.replace(" ", "_"),
                self.finding_aids_entity.container.container_no,
                self.finding_aids_entity.folder_no
            )
        else:
            barcode = "%s-%04d-%03d-%03d" % (
                self.finding_aids_entity.archival_unit.reference_code.replace(" ", "_"),
                self.finding_aids_entity.container.container_no,
                self.finding_aids_entity.folder_no,
                self.finding_aids_entity.sequence_no
            )
        return barcode
