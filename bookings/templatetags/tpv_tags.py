from django import template
from django.utils.safestring import mark_safe
from bookings.models import FormInstance

register=template.Library()


'''
	Filter tag
'''
@register.filter
def get_total_by_regime(fi, code):
    return "{:.2f}".format(fi.get_total_by_regime(code))

@register.filter
def check_band(fi):
    #No band
    if fi.band == None:
        return 0

    #Locked
    if fi.band.type != None and fi.band.type.code == "00":
        return 1

    #No Limit
    if fi.band.type != None and fi.band.type.code == "03":
        return 2
        #return True

    total_regime = -1
    if fi.band != None and fi.band.guest != None and fi.band.guest.regime != None:
        regime = fi.band.guest.regime.code

        #Invalid item
        if fi.get_invalid_item(regime):
            return 3  

        total_regime = fi.get_total_by_regime(regime)

    if (total_regime > -1 and fi.band.balance < total_regime) or (total_regime == -1 and fi.band.balance < fi.get_total):
        return 4

    #Credit 0
    if fi.band.type != None and fi.band.type.code == "02":
        return 5

    return 6

'''
	Simple tag
'''
@register.simple_tag
def get_total_items(username, project_uuid):
    return get_guest_total_items(username, project_uuid)

@register.simple_tag
def get_item_price(item, band, code):
    price =  item.item.get_price(code, band)
    return "{} €".format(item.item.get_price(code, band)) if price != None else "NOT INCLUDED!"


'''
	Inclusion tag
'''
@register.inclusion_tag('bookings/tpv/tpv-table-info.html')
def get_table_info(pos, table):
    fi = FormInstance.get_open_in_table(pos, table)
    return {"fi": fi}

