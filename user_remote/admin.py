from django.contrib import admin
from .models import *


class PWUserAdmin(admin.ModelAdmin):
	list_display = ('uuid', 'name', 'email', 'project_uuid')
	search_fields = ['name', 'email', 'uuid']

admin.site.register(PWUser, PWUserAdmin)
