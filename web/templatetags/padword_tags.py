from django.utils.safestring import mark_safe
from django import template
from django.urls import reverse
import json
from padword.commons import show_exc
from web.models import Project, ProjectUser
from contents.models import Allergen, Category, CategoryUser, Feature
import string, random
import os

register = template.Library()

'''
    Filters
'''
@register.inclusion_tag('link-css.html')
def get_css_project(pk_proj):
    print ("DANI")
    try:
        from padword.settings import STATIC_URL, STATIC_ROOT
        path = f'{STATIC_ROOT}/css/menu_prj_{pk_proj}.css'
        url = f'{STATIC_URL}css/menu_prj_{pk_proj}.css'
        print(path)
        if os.path.exists(path):
            return {'url':url}
        return {'url':None}
    except Exception as e:
        print (show_exc(e))
    return {'url':None}

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
        return "UNSETTING"

@register.filter
def mult(a, b):
    try:
        return a * b
    except Exception as e:
        return 0

@register.filter
def random_str(nchars='128'):
    try:
        n = int(nchars)
    except:
        n = 128
    return (''.join(random.choice(string.ascii_letters) for i in range(n)))

@register.filter()
def have_allergen(obj, allergen):
    a_list = [item.allergen for item in obj.allergen_list.all()]
    return allergen in a_list

@register.filter()
def have_feature(obj, feature):
    a_list = [item.feature for item in obj.features.all()]
    return feature in a_list

@register.filter()
def is_empty(json_str, lang):
    try:
        lang = lang.split('-')[0]
        json_dict = json.loads(json_str)
        return (json_dict[lang.upper()] == "")
    except:
        try:
            json_dict = json.loads(json_str)
            return (json_dict[list(json_dict.keys())[0]] == "")
        except Exception as e:
            try:
                json_dict = json.loads(json_str)
                keys = json_dict.keys()
                return (json_dict[keys[0]] == "")
            except Exception as e:
                return (json_str == "")


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
        try:
            lang = request.GET['lang'] if 'lang' in request.GET else context['guest'].language
        except:
            lang = request.GET['lang'] if 'lang' in request.GET else request.LANGUAGE_CODE
        lang = lang.split('-')[0]
        json_dict = json.loads(json_str)
        return mark_safe(json_dict[lang.upper()])
    except:
        try:
            json_dict = json.loads(json_str)
            return mark_safe(json_dict[list(json_dict.keys())[0]])
        except Exception as e:
            try:
                json_dict = json.loads(json_str)
                keys = json_dict.keys()
                return mark_safe(json_dict[keys[0]])
            except Exception as e:
                return mark_safe(json_str)

@register.simple_tag(takes_context=True)
def padword_translate_short(context, json_str, chars):
    val = ""
    try:
        request = context['request']
        try:
            lang = request.GET['lang'] if 'lang' in request.GET else context['guest'].language
        except:
            lang = request.GET['lang'] if 'lang' in request.GET else request.LANGUAGE_CODE
        lang = lang.split('-')[0]
        json_dict = json.loads(json_str)
        val = json_dict[lang.upper()]
    except:
        try:
            json_dict = json.loads(json_str)
            val = json_dict[list(json_dict.keys())[0]]
        except Exception as e:
            try:
                json_dict = json.loads(json_str)
                keys = json_dict.keys()
                val = json_dict[keys[0]]
            except Exception as e:
                val = json_str
    return mark_safe("{}...".format(val[:chars])) if len(val) > chars else mark_safe(val)

@register.simple_tag(takes_context=True)
def padword_translate_obj(context, obj_id):
    try:
        obj = get_obj(obj_id, 'Category')
        request = context['request']
        try:
            lang = request.GET['lang'] if 'lang' in request.GET else context['guest'].language
        except:
            lang = request.GET['lang'] if 'lang' in request.GET else request.LANGUAGE_CODE
        lang = lang.split('-')[0]
        json_str = obj.name
        json_dict = json.loads(json_str)
        return mark_safe(json_dict[lang.upper()])
    except Exception as e:
        try:
            json_dict = json.loads(json_str)
            return json_dict[list(json_dict.keys())[0]]
        except Exception as e:
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
        return true_alternative

@register.filter
def get_obj(uuid, model):
    try:
        obj = eval("{}.objects.get(uuid='{}')".format(model,uuid))
        return obj
    except Exception as e:
        return None

@register.filter
def addstr(arg1,arg2):
    return(mark_safe(str(arg1)+str(arg2)))

@register.filter
def items_in_bookings(fi,item):
    try:
        return fi.items_in_bookings(item).count()
    except Exception as e:
        return (0)


'''
    Inclusion Tags
'''
@register.inclusion_tag('main-menu.html')
def get_main_menu(user):
    try:
        if user.groups.filter(name="guests").exists():
            return {'user': user, 'menu': "guests"}
        if user.groups.filter(name="categories").exists():
            obj = CategoryUser.objects.filter(username=user.username).first()
            if obj != None: 
                return {'user': user, 'menu': "categories", "category": obj.category}
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
        return {'div':div, 'url':url, 'go':go}

@register.inclusion_tag('contents/allergens.html')
def show_allergen(obj):
    return {'obj': obj, 'item_list': Allergen.objects.all()}

@register.inclusion_tag('contents/extras.html')
def show_extras(obj):
    return {'obj': obj,}

@register.inclusion_tag('contents/features.html')
def show_feature(obj):
    return {'obj': obj, 'item_list': Feature.objects.all()}

