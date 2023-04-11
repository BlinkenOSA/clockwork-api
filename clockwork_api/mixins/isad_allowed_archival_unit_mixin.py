from archival_unit.models import ArchivalUnit


class IsadListAllowedArchivalUnitMixin(object):
    def get_queryset(self):
        user = self.request.user

        if not self.kwargs:
            if user.user_profile.allowed_archival_units.count():
                queryset = ArchivalUnit.objects.none()
                for archival_unit in user.user_profile.allowed_archival_units.all():
                    queryset |= ArchivalUnit.objects.filter(fonds=archival_unit.fonds, level='F')
            return queryset
