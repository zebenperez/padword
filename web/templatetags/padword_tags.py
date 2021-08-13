from django import template
from django.urls import reverse
import json
from padword.commons import show_exc
from web.models import ProjectUser

register = template.Library()

'''
    Filters
'''
@register.filter
def in_group(user, group):
    return user.groups.filter(name=group).exists()

@register.filter
def currency(json_str):
    try:
        json_dict = json.loads(json_str)
        return "{:.2f} {}".format(float(json_dict["value"]), json_dict["type"])
    except Exception as e:
        print (show_exc(e))
        return "UNSETTING"

'''
    Simple Tags
'''
@register.simple_tag(takes_context=True)
def current(context, url, **kwargs):
    try:
        request = context['request']
        if request.get_full_path().startswith(reverse(url)) :
            return "active current"
        else:
            return ""
    except:
        return ""

@register.simple_tag(takes_context=True)
def current_exact(context, url, **kwargs):
    try:
        request = context['request']
        reverseurl = reverse(url, kwargs=eval(str(kwargs)))
        if reverseurl == request.get_full_path() :
            return "active current"
        else:
            return ""
    except:
        return ""

@register.simple_tag(takes_context=True)
def padword_translate(context, json_str):
    try:
        request = context['request']
        lang = request.LANGUAGE_CODE
        json_dict = json.loads(json_str)
        return json_dict[lang.upper()]
    except:
        print (json_str)
        try:
            return json.loads(json_str)['ES']
        except Exception as e:
            print (json_str)
            return 'ERROR'

'''
    Inclusion Tags
'''
@register.inclusion_tag('main-menu.html')
def get_main_menu(user):
    if user.groups.filter(name="admins").exists():
        return {'user': user, 'menu': "admins"}
    if user.groups.filter(name="projects").exists():
        obj = ProjectUser.objects.filter(user=user).first()
        if obj != None: 
            return {'user': user, 'menu': "projects", "project": obj.project}
    if user.groups.filter(name="clients").exists():
        return {'user': user, 'menu': "clients"}
    return {}

@register.inclusion_tag('web/second-menu.html')
def get_second_menu(user):
    if user.groups.filter(name="admins").exists():
        return {'user': user, 'menu': "admins"}
    if user.groups.filter(name="projects").exists():
        obj = ProjectUser.objects.filter(user=user).first()
        if obj != None: 
            return {'user': user, 'menu': "projects", "project": obj.project}
    if user.groups.filter(name="clients").exists():
        return {'user': user, 'menu': "clients"}
    return {}

