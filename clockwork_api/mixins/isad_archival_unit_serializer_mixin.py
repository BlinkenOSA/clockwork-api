class IsadArchivalUnitSerializerMixin(object):
    def get_status(self, obj):
        if hasattr(obj, 'isad'):
            return 'Published' if obj.isad.published else 'Draft'
        else:
            return 'Not exists'
