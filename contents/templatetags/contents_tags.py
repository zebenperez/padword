from django import template

from contents.models import Allergen, ItemPromo

register = template.Library()


'''
    Filters
'''
@register.filter()
def have_allergen(obj, allergen):
    a_list = [item.allergen for item in obj.allergen_list.all()]
    return allergen in a_list

@register.filter()
def have_feature(obj, feature):
    a_list = [item.feature for item in obj.features.all()]
    return feature in a_list

@register.filter()
def have_payment_type(obj, payment_type):
    a_list = [item.payment_type for item in obj.payment_types.all()]
    return payment_type in a_list

@register.filter()
def get_item_price(obj, regime_code):
    return obj.get_price(regime_code)

'''
    Inclusion tags
'''
@register.inclusion_tag('contents/prices.html')
def show_prices(obj):
    return {'obj': obj,}

@register.inclusion_tag('contents/allergens.html')
def show_allergen(obj):
    return {'obj': obj, 'item_list': Allergen.objects.all()}

@register.inclusion_tag('contents/extras.html')
def show_extras(obj):
    return {'obj': obj,}

@register.inclusion_tag('contents/promos.html')
def show_promos(obj):
    return {'obj': obj,}

@register.inclusion_tag('bookings/show-promo-gallery.html')
def get_promos(obj):
    promo_list = ItemPromo.get_current(obj.project_uuid)
    return {'category': obj, 'promo_list': promo_list, 'total_images': len(promo_list)+obj.images.all().count()}



