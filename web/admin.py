from django.contrib import admin
from .models import ProjectUser, Waiter, Module, Menu, ProjectUserMenu
from .models_lock import Lock


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
	list_display = ('code', 'name', 'url', 'ico', 'promo')

admin.site.register(Module, ModuleAdmin)
admin.site.register(Menu, MenuAdmin)

class LockAdmin(admin.ModelAdmin):
	list_display = ('uuid', 'alias', 'project_uuid', 'room')
	search_fields = ['project_uuid', 'uuid', 'alias']
	list_filter = ('project_uuid',)

admin.site.register(Lock, LockAdmin)

class ProjectUserMenuAdmin(admin.ModelAdmin):
    list_display = ('project_user', 'menu', 'order')
    search_fields = ['project_user__username']

admin.site.register(ProjectUserMenu, ProjectUserMenuAdmin)
 
