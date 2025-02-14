from rest_framework import serializers
from guest.models import Guest, GuestCar
from web.models import Room
from web.models_lock import Lock


#class ActivitySerializer(serializers.ModelSerializer):
#    class Meta:
#        model = Activity
#        fields = ['pk', 'name']
#
#class CountrySerializer(serializers.ModelSerializer):
#    class Meta:
#        model = Country
#        fields = ['name']
#
#class ProfileSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = Profile
#        fields = ['name']
#
#class RaceSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = Race
#        fields = ['name']
#
#class ResponsabilitySerializer(serializers.ModelSerializer):
#    class Meta:
#        model = Responsability
#        fields = ['name']
#
#class SexSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = Sex 
#        fields = ['name']
#
class GuestSerializer(serializers.HyperlinkedModelSerializer):
#    activity = ActivitySerializer(many=False, read_only=True)
#    country = CountrySerializer(many=False, read_only=True)
#    profile = ProfileSerializer(many=False, read_only=True)
#    race = RaceSerializer(many=False, read_only=True)
#    responsability = ResponsabilitySerializer(many=False, read_only=True)
#    sex = SexSerializer(many=False, read_only=True)
#    fcoc = FcocSerializer(many=False, read_only=True)
#    #area = AreaSerializer(many=True, read_only=True, source="teacher_area")
    lock_code = serializers.SerializerMethodField()

    def get_lock_code(self, obj):
        return obj.lock_code

    class Meta:
        model = Guest
        fields = ['UUID', 'name', 'surname', 'language', 'mobile', 'email', 'check_in', 'check_out', 'room', 'ext_id', 'pwa_link', 'lock_code']

class LockSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Lock
        fields = ['uuid', 'alias', 'room']

class RoomSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Room
        fields = ['uuid', 'alias', 'number', 'order']

class GuestCarSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GuestCar
        fields = ['number', 'guest_name', 'date_in', 'date_out']
