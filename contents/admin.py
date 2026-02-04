from django.contrib import admin
from .models import *

class AllergenAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'internal', 'project_uuid', 'active')
    search_fields = ['project_uuid', 'internal']

class CategoryUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'category_uuid', 'view_cat', 'remove_cat')

class FeatureAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')

class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'ext_id', 'project_uuid', 'active')
    search_fields = ['ext_id']

    def project_uuid(self, obj):
        try:
            return obj.project.uuid 
        except:
            return ""

class PaymentTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')

class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('form_instance_id', 'item', 'comments')

class PosCodeItemAdmin(admin.ModelAdmin):
    list_display = ('pos', 'code', 'name', 'item_id', 'project_uuid')
    search_fields = ['project_uuid']

class PointOfSaleAdmin(admin.ModelAdmin):
    list_display = ('name', 'ext_code', 'project_uuid')
    search_fields = ['project_uuid']

class PointOfSaleCategoryAdmin(admin.ModelAdmin):
    list_display = ('point_of_sale', 'category', 'pos_project', 'cat_project')
    search_fields = ['point_of_sale__ext_code']

    def pos_project(self, obj):
        return obj.point_of_sale.project_uuid

    def cat_project(self, obj):
        return obj.category.project_uuid

admin.site.register(Allergen, AllergenAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(CategoryUser, CategoryUserAdmin)
admin.site.register(Feature, FeatureAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(PaymentType, PaymentTypeAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(PosCodeItem, PosCodeItemAdmin)
admin.site.register(PointOfSale, PointOfSaleAdmin)
admin.site.register(PointOfSaleCategory, PointOfSaleCategoryAdmin)
