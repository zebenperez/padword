from django import template
from django.urls import reverse
import json
from padword.commons import show_exc

register = template.Library()

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
        return json.loads(json_str)['ES']

@register.filter
def currency(json_str):
    try:
        json_dict = json.loads(json_str)
        return "{:.2f} {}".format(float(json_dict["value"]), json_dict["type"])
    except Exception as e:
        print (show_exc(e))
        return "UNSETTING"

