from django.contrib import admin
from .models import ProjectUser, Waiter, Module, Menu, ProjectUserMenu


class ProjectUserMenuTabular(admin.TabularInline):
    model = ProjectUserMenu
    extra = 1

class ProjectUserAdmin(admin.ModelAdmin):
    list_display = ('project', 'user')
    search_fields = ['project_uuid', 'username']
    inlines = [ProjectUserMenuTabular,]
    #filter_horizontal = ('menus_mod',)

admin.site.register(ProjectUser, ProjectUserAdmin)

class WaiterAdmin(admin.ModelAdmin):
	list_display = ('project', 'user')
	search_fields = ['project_uuid', 'username']

admin.site.register(Waiter, WaiterAdmin)

class ModuleAdmin(admin.ModelAdmin):
	list_display = ('code', 'name', 'desc')

class MenuAdmin(admin.ModelAdmin):
	list_display = ('code', 'name')

admin.site.register(Module, ModuleAdmin)
admin.site.register(Menu, MenuAdmin)
