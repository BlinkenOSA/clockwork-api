from django.db import models


class DetectProtectedMixin(object):
    def is_removable(self):
        state = True
        for relation in self._meta._relation_tree:

            on_delete = relation.remote_field.on_delete
            if on_delete in [None, models.DO_NOTHING]:
                continue

            f = {relation.name: self}
            related_queryset = relation.model.objects.filter(**f)
            if on_delete == models.PROTECT:
                if related_queryset.count() > 0:
                    state = False
        return state
