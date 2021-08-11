from django import template
from django.utils.safestring import mark_safe
from bookings.common_lib import get_answer_instance, get_max_index

register=template.Library()


'''
	Filter tag
'''
@register.filter
def get_indexes(q, fi):
    return range(0, (get_max_index(q, fi)+ 1))

'''
	Simple tag
'''
@register.simple_tag
def field_value(fi, q, f, index):
    ai = get_answer_instance(fi, q, f, index)
    text = ""
    if ai != None and f.answer_type.field_type == "file":
        try:
            print(ai.document.name)
            name_list = ai.document.name.split("/")
            name = name_list[len(name_list)-1][15:] if len(name_list[len(name_list)-1]) > 15 else ""
            return mark_safe("<a href='{}' target='_blank'>{}</a>".format(ai.document.url, name))
        except:
            return ""
    elif ai != None:
        return ai.text 
    return ""
    #return ai.text if ai != None else ""

'''
	Inclusion tag
'''
@register.inclusion_tag('bookings/field_form.html')
def field_form(fi, q, f, index, user):
    ai = get_answer_instance(fi, q, f, index)

    value = ai.text if ai != None else ""

    doc = None
    if ai != None and ai.field != None and ai.field.answer_type != None and ai.field.answer_type.field_type == "file" and ai.document:
        doc = ai.document 

    item_list = []
    if f != None and f.answer_type != None and f.answer_type.field_type == "items":
        item_list = fi.form.get_category_items()

    readonly = (f.read_only and not user.is_staff and not user.is_superuser)

    answer_name = "question_%s_field_%s_%s" % (q.id, f.id, index)

    context = {
        'fi_id': fi.id, 
        'q_id': q.id, 
        'f': f,
        'index': index, 
        'answer_name': answer_name, 
        'readonly': readonly,
        'doc': doc,
        'item_list': item_list,
        'value': value
    }
    return context


