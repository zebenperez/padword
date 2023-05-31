from django.contrib import admin
from .models import ProjectUser, Waiter, Module

class ProjectUserAdmin(admin.ModelAdmin):
	list_display = ('project', 'user')
	search_fields = ['project_uuid', 'username']

admin.site.register(ProjectUser, ProjectUserAdmin)

class WaiterAdmin(admin.ModelAdmin):
	list_display = ('project', 'user')
	search_fields = ['project_uuid', 'username']

admin.site.register(Waiter, WaiterAdmin)

class ModuleAdmin(admin.ModelAdmin):
	list_display = ('code', 'name', 'desc')

admin.site.register(Module, ModuleAdmin)
