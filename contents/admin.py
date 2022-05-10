from django.contrib import admin
from .models import *

class AllergenAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')

class CategoryUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'category_uuid', 'view_cat', 'remove_cat')

class FeatureAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')

class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('form_instance_id', 'item', 'comments')

admin.site.register(Allergen, AllergenAdmin)
admin.site.register(CategoryUser, CategoryUserAdmin)
admin.site.register(Feature, FeatureAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
