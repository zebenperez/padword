from django import template
from django.utils.safestring import mark_safe
from bookings.models import FormInstance

register=template.Library()


'''
	Inclusion tag
'''
@register.inclusion_tag('bookings/tpv/tpv-table-info.html')
def get_table_info(pos, table):
    fi = FormInstance.get_open_in_table(pos, table)
    return {"fi": fi}

