from django.utils.safestring import mark_safe
from django import template
from django.urls import reverse
import json
from padword.commons import show_exc
from web.models import Project, ProjectUser
import string, random

register = template.Library()

'''
    Filters
'''
@register.filter
def in_group(user, group):
    try:
        return user.groups.filter(name=group).exists()
    except:
        return False

@register.filter
def currency(json_str):
    try:
        json_dict = json.loads(json_str)
        return "{:.2f} {}".format(float(json_dict["value"]), json_dict["type"])
    except Exception as e:
        print (show_exc(e))
        return "UNSETTING"

@register.filter
def mult(a, b):
    try:
        return a * b
    except Exception as e:
        print (show_exc(e))
        return 0

@register.filter
def random_str(nchars='128'):
    try:
        n = int(nchars)
    except:
        n = 128
    return (''.join(random.choice(string.ascii_letters) for i in range(n)))


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
def current_lang(context):
    try:
        request = context['request']
        lang = request.GET['lang'] if 'lang' in request.GET else request.LANGUAGE_CODE
        return lang.upper()
    except:
        return "ES"

@register.simple_tag
def idx_page (idx, page, items_per_page):
    try:
        return (int(idx) + int(page)*int(items_per_page))
    except:
        return 0


@register.simple_tag(takes_context=True)
def padword_translate(context, json_str):
    try:
        request = context['request']
        lang = request.GET['lang'] if 'lang' in request.GET else request.LANGUAGE_CODE
        lang = lang.split('-')[0]
        json_dict = json.loads(json_str)
        return json_dict[lang.upper()]
    except:
        try:
            json_dict = json.loads(json_str)
            return json_dict[list(json_dict.keys())[0]]
        except Exception as e:
            print(show_exc(e))
            try:
                json_dict = json.loads(json_str)
                keys = json_dict.keys()
                return json_dict[keys[0]]
            except Exception as e:
                return json_str

@register.simple_tag(takes_context=True)
def is_current_lang(context, language, true_alternative='current', false_alternative=''):
    try:
        request = context['request']
        lang = request.GET['lang'] if 'lang' in request.GET else request.LANGUAGE_CODE
        lang = lang.split('-')[0]
        if (lang.upper() == language.upper()):
            return (true_alternative)
        return (false_alternative)
    except Exception as e:
        print (show_exc(e))
        return true_alternative

@register.filter
def get_obj(uuid, model):
    try:
        obj = eval("{}.objects.get(uuid='{}')".format(model,uuid))
        return obj
    except Exception as e:
        print (show_exc(e))
        return None

@register.filter
def addstr(arg1,arg2):
    return(mark_safe(str(arg1)+str(arg2)))

@register.filter
def items_in_bookings(fi,item):
    try:
        return fi.items_in_bookings(item).count()
    except Exception as e:
        print (show_exc(e))
        return (0)


'''
    Inclusion Tags
'''
@register.inclusion_tag('main-menu.html')
def get_main_menu(user):
    try:
        if user.groups.filter(name="guests").exists():
            return {'user': user, 'menu': "guests"}
        if user.groups.filter(name="projects").exists():
            obj = ProjectUser.objects.filter(username=user.username).first()
            if obj != None: 
                return {'user': user, 'menu': "projects", "project": obj.project}
        if user.groups.filter(name="admins").exists() or user.is_superuser:
            return {'user': user, 'menu': "admins"}
    except:
        return {}

@register.inclusion_tag('web/second-menu.html')
def get_second_menu(user):
    try:
        if user.groups.filter(name="guests").exists():
            return {'user': user, 'menu': "guests"}
        if user.groups.filter(name="projects").exists():
            obj = ProjectUser.objects.filter(username=user.username).first()
            if obj != None: 
                return {'user': user, 'menu': "projects", "project": obj.project}
        if user.groups.filter(name="admins").exists() or user.is_superuser:
            return {'user': user, 'menu': "admins"}
    except Exception as e:
        print (show_exc(e))
        return {}

@register.inclusion_tag('ark.html')
def ark(url, div, **kwargs):
    go = False
    try:
        kwargs = eval(str(kwargs))
        go = kwargs.pop('go', False)
        prefix = kwargs.pop('prefix', False)
        posfix = kwargs.pop('posfix', False)
        url = reverse(url, kwargs=kwargs)
        return {'div':div, 'url':url, 'go':go, 'prefix':prefix, 'posfix':posfix}
    except Exception as e:
        url = reverse(url)
        print (show_exc(e))
        return {'div':div, 'url':url, 'go':go}

