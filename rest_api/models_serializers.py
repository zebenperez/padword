from rest_framework import serializers
from guest.models import Guest, GuestCar
from guest.wristband_models import WristbandAccess
from web.models import Room
from web.models_lock import Lock
from vehicle_access.models import PlateType, VehiclePlate, normalize_plate


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
    plates = serializers.SerializerMethodField()
    regime = serializers.SerializerMethodField()

    def get_lock_code(self, obj):
        return obj.lock_code

    def get_plates(self, obj):
        return obj.plates

    def get_regime(self, obj):
        regime = obj.regime
        return regime.code if regime != None else ""

    class Meta:
        model = Guest
        fields = ['UUID', 'name', 'surname', 'language', 'mobile', 'email', 'check_in', 'check_out', 'room', 'ext_id', 'pwa_link', 'lock_code', 'plates', 'regime']

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


class VehiclePlateSerializer(serializers.ModelSerializer):
    plate_type = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=PlateType.objects.all(),
    )
    plate_type_name = serializers.CharField(source='plate_type.name', read_only=True)

    def validate(self, attrs):
        plate = attrs.get('plate', self.instance.plate if self.instance else '')
        normalized_plate = normalize_plate(plate)
        if not normalized_plate:
            raise serializers.ValidationError({
                'plate': 'Introduce una matrícula válida.'
            })

        project_uuid = self.context.get('project_uuid')
        if project_uuid:
            existing_plates = VehiclePlate.objects.filter(
                project_id=project_uuid,
                plate_normalized=normalized_plate,
            )
            if self.instance:
                existing_plates = existing_plates.exclude(pk=self.instance.pk)
            if existing_plates.exists():
                raise serializers.ValidationError({
                    'plate': 'Esta matrícula ya está registrada en el proyecto.'
                })

        return attrs

    class Meta:
        model = VehiclePlate
        fields = ['uuid', 'plate', 'plate_type', 'plate_type_name']


class PlateTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlateType
        fields = ['uuid', 'name']


class WristbandAccessSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = WristbandAccess
        fields = ['inside', 'date', 'band_name', 'zone_name', 'guest_name']
