from django.contrib import admin
from .models import *

# Register your models here.
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('form_instance_id', 'item', 'comments')
admin.site.register(ShoppingCart, ShoppingCartAdmin)
