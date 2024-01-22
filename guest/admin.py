from django.contrib import admin
from .models import *


class RegimeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')

class WristbandTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')

admin.site.register(Regime, RegimeAdmin)
admin.site.register(WristbandType, WristbandTypeAdmin)
