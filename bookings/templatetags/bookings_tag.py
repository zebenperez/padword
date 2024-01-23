from django import template
from django.utils.safestring import mark_safe
from bookings.common_lib import get_answer_instance, get_max_index, get_guest_total_items, check_timetable as ch_timetable

register=template.Library()


'''
	Filter tag
'''
@register.filter
def get_indexes(q, fi):
    return range(0, (get_max_index(q, fi)+ 1))

@register.filter
def check_timetable(form):
    return ch_timetable(form)

@register.filter
def get_cat_uuid(form, name):
    return form.get_category_uuid_by_code(name)

#@register.filter
#def get_item_price(item, code):
#    return item.item.get_price(code)


@register.filter
def get_file_url(cat, order):
    try:
        cf = cat.get_file_by_order(order)
    except:
        cf = None
    return cf.file.url if cf != None and cf.file else ""

'''
	Simple tag
'''
@register.simple_tag
def get_total_items(username, project_uuid):
    return get_guest_total_items(username, project_uuid)


'''
	Inclusion tag
'''
@register.inclusion_tag('bookings/field_value.html')
def field_value(fi, q, f, index):
    ai = get_answer_instance(fi, q, f, index)
    context = {'ai': ai}
    if ai != None and f.answer_type.field_type == "file":
        try:
            name_list = ai.document.name.split("/")
            name = name_list[len(name_list)-1][15:] if len(name_list[len(name_list)-1]) > 15 else ""
            context['name'] = name
        except:
            pass
    elif ai!= None and f.answer_type.field_type == "items_shop":
        item = ai.get_item() 
        context['item'] = item
        
    return context

@register.inclusion_tag('bookings/general/field_form.html', takes_context=True)
def field_form(context, fi, q, f, index, user):
    ai = get_answer_instance(fi, q, f, index) if fi != "" else None

    value = ai.text if ai != None else ""

    doc = None
    if ai != None and ai.field != None and ai.field.answer_type != None and ai.field.answer_type.field_type == "file" and ai.document:
        doc = ai.document 

    item_list = []
    if f != None and f.answer_type != None and (f.answer_type.field_type == "items" or f.answer_type.field_type == "items_shop"): 
        #item_list = fi.form.get_category_items()
        item_list = f.question.block.form.get_category_items()

    readonly = (f.read_only and not user.is_staff and not user.is_superuser)

    answer_name = "question_%s_field_%s_%s" % (q.id, f.id, index) if q != None and f != None else "questions_0_field_0_0"

#    context = {
#        'fi_id': fi.id if fi != ""  and fi != None else "", 
#        'q_id': q.id if q != None else 0, 
#        'f': f,
#        'index': index, 
#        'answer_name': answer_name, 
#        'readonly': readonly,
#        'doc': doc,
#        'item_list': item_list,
#        'selected_item': ai.get_item() if ai != None else None,
#        'value': value
#    }
    context["fi_id"] = fi.id if fi != ""  and fi != None else ""
    context["q_id"] = q.id if q != None else 0
    context["f"] = f
    context["index"] = index
    context["answer_name"] = answer_name
    context["readonly"] = readonly
    context["doc"] = doc
    context["item_list"] = item_list
    context["selected_item"] = ai.get_item() if ai != None else None
    context["value"] = value

    return context


