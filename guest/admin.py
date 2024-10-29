from django.contrib import admin
from .models import *


class RegimeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')

class WristbandAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')

class WristbandAccessPointAdmin(admin.ModelAdmin):
    list_display = ('name',)

class WristbandAccessZoneAdmin(admin.ModelAdmin):
    list_display = ('name',)

class WristbandTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')

admin.site.register(Regime, RegimeAdmin)
admin.site.register(Wristband, WristbandAdmin)
admin.site.register(WristbandAccessPoint, WristbandAccessPointAdmin)
admin.site.register(WristbandAccessZone, WristbandAccessZoneAdmin)
admin.site.register(WristbandType, WristbandTypeAdmin)
