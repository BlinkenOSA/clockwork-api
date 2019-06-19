from django.utils import timezone


class UserDataSerializerMixin(object):
    def create(self, validated_data):
        validated_data['user_created'] = self.context['request'].user.username
        return super(UserDataSerializerMixin, self).create(validated_data)

    def update(self, instance, validated_data):
        validated_data['user_updated'] = self.context['request'].user.username
        validated_data['date_updated'] = timezone.now()
        return super(UserDataSerializerMixin, self).update(instance, validated_data)