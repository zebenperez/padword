from rest_framework import serializers
from web.models import Lock


class LockSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Lock
        fields = ['uuid', 'alias', 'room']


