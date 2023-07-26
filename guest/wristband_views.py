from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from .models import Wristband
from padword.commons import show_exc, get_or_none, get_param, reverse_cardkey
from padword.decorators import group_required


@group_required("admins")
def wristbands(request):
    return render (request, "wristbands/wristbands.html", {'active': 'searchkeycard'})

@group_required("admins")
def wristbands_search(request):
    value = get_param(request.GET, "value")
    #card_result = number_search(value)
    band_result = []
    return render (request, "wristbands/wristbands-search.html", {'band_list': band_result})


