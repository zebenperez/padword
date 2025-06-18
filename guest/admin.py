from django.contrib import admin
from .models import *
from .wristband_models import *


class RegimeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'alt_code', 'project_uuid')

class WristbandAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')

class WristbandAccessAdmin(admin.ModelAdmin):
    list_display = ('date', 'wristband', 'access_point', 'inside')

class WristbandAccessPointAdmin(admin.ModelAdmin):
    list_display = ('name',)

class WristbandAccessZoneAdmin(admin.ModelAdmin):
    list_display = ('name',)

class WristbandTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')

admin.site.register(Regime, RegimeAdmin)
admin.site.register(Wristband, WristbandAdmin)
admin.site.register(WristbandAccess, WristbandAccessAdmin)
admin.site.register(WristbandAccessPoint, WristbandAccessPointAdmin)
admin.site.register(WristbandAccessZone, WristbandAccessZoneAdmin)
admin.site.register(WristbandType, WristbandTypeAdmin)
