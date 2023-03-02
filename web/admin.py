from django.contrib import admin
from .models import ProjectUser

class ProjectUserAdmin(admin.ModelAdmin):
	list_display = ('project', 'user')
	search_fields = ['project_uuid', 'username']

admin.site.register(ProjectUser, ProjectUserAdmin)
