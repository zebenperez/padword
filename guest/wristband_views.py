from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from .models import Guest, Wristband, WristbandBalance, WristbandType
from web.models import Project
from padword.commons import show_exc, get_or_none, get_param, reverse_cardkey, get_float
from padword.decorators import group_required


'''
    Bands in guest
'''
@group_required("admins", "projects")
def guest_band_details(request):
    try:
        guest = get_or_none(Guest, get_param(request.GET, "obj_id"))
        print(guest)
        return render(request, "guest/bands/guest-details-bands.html", {"obj": guest})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_add(request):
    try:
        guest = get_or_none(Guest, get_param(request.GET, "obj_id"))
        return render(request, "guest/bands/guest-details-bands-form.html", {"obj": guest, "step": 0})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_save(request):
    try:
        guest = get_or_none(Guest, get_param(request.GET, "obj_id"))
        code = reverse_cardkey(get_param(request.GET, "value"))

        b = Wristband.objects.filter(code=code).first()
        #for b in b_list:
        #    if b != None and b.guest.have_valid_booking():
        if b != None:
            #msg = "There are another user ({} {} - {}) with this band!".format(b.guest.name, b.guest.surname, b.guest.room)
            err = "True"
            return render(request, "guest/bands/guest-details-bands-form.html", {"obj": guest, "band": b, "step": 0, "err": err})
        
        type_list = WristbandType.objects.all()
        band = Wristband.objects.create(guest=guest, code=code)
        return render(request, "guest/bands/guest-details-bands-form.html", {"obj": guest, "band": band, "type_list": type_list, "step": 1})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_name(request):
    try:
        guest = get_or_none(Guest, get_param(request.GET, "obj_id"))
        band = get_or_none(Wristband, get_param(request.GET, "band_id"))
        band.name = get_param(request.GET, "value")
        band.save()
        type_list = WristbandType.objects.all()
        return render(request, "guest/bands/guest-details-bands-form.html", {"obj": guest, "band": band, "type_list": type_list, "step": 2})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_type(request):
    try:
        guest = get_or_none(Guest, get_param(request.GET, "obj_id"))
        band = get_or_none(Wristband, get_param(request.GET, "band_id"))
        band.type = get_or_none(WristbandType, get_param(request.GET, "value"))
        band.save()
        type_list = WristbandType.objects.all()
        return render(request, "guest/bands/guest-details-bands-form.html", {"obj": guest, "band": band, "type_list": type_list, "step": 3})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_locks(request):
    try:
        band = get_or_none(Wristband, get_param(request.GET, "obj_id"))
        if "locks" in request.GET and request.GET["locks"] == "true":
            band.guest.add_all_key_card(band.code)
            band.locks = True
            band.save()
        type_list = WristbandType.objects.all()
        return render(request, "guest/bands/guest-details-bands-form.html", {"obj": band.guest, "band": band, "type_list": type_list, "step": 4})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_kid(request):
    try:
        band = get_or_none(Wristband, get_param(request.GET, "obj_id"))
        band.kid = True if "kid" in request.GET and request.GET["kid"] == "true" else False
        band.save()
        type_list = WristbandType.objects.all()
        return render(request, "guest/bands/guest-details-bands-form.html", {"obj": band.guest, "band": band, "type_list": type_list, "step": 5})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_balance_add(request):
    try:
        band = get_or_none(Wristband, get_param(request.GET, "obj_id"))
        amount = get_float(get_param(request.GET, "balance"))
        if amount > 0:
            balance = WristbandBalance.objects.create(wristband=band, amount=amount, desc=_("Init charge"))
        return render(request, "guest/guest-details-tabs.html", {'obj': band.guest, 'current_tab': 'bands', 'temp_range': range(16,26)})
        #return render(request, "guest/bands/guest-details-bands-list.html", {"obj": band.guest})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_edit(request):
    try:
        band = get_or_none(Wristband, get_param(request.GET, "obj_id"))
        type_list = WristbandType.objects.all()
        return render(request, "guest/bands/guest-details-bands-edit-form.html", {"obj": band, "type_list": type_list})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_remove(request):
    try:
        band = get_or_none(Wristband, get_param(request.GET, "obj_id"))
        guest = band.guest 
        code = band.code
        band.delete()
        if request.GET["band_lock"] == "true":
            guest.remove_all_key_cards(code)
        return render(request, "guest/bands/guest-details-bands-list.html", {"obj": guest})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_remove2(request):
    try:
        guest = get_or_none(Guest, get_param(request.GET, "guest"))
        band = get_or_none(Wristband, get_param(request.GET, "obj_id"))
        band_guest = band.guest 
        code = band.code
        band.delete()
        if request.GET["band_lock"] == "true":
            band_guest.remove_all_key_cards(code)
        return render(request, "guest/bands/guest-details-bands-form.html", {"obj": guest, "step": 0})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})


@group_required("admins", "projects")
def guest_bands_balance(request):
    try:
        guest = get_or_none(Guest, get_param(request.GET, "obj_id"))
        return render(request, "guest/bands/bands.html", {"obj": guest})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_balance_list(request):
    try:
        band = get_or_none(Wristband, get_param(request.GET, "obj_id"))
        return render(request, "guest/bands/balance.html", {"band": band})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_balance_form(request):
    try:
        band = get_or_none(Wristband, get_param(request.GET, "obj_id"))
        balance = get_or_none(WristbandBalance, get_param(request.GET, "balance_id"))
        if balance == None:
            balance = WristbandBalance.objects.create(wristband=band)
        return render(request, "guest/bands/balance-form.html", {"obj": balance})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_balance_remove(request):
    try:
        balance = get_or_none(WristbandBalance, get_param(request.GET, "obj_id"))
        band = balance.wristband
        balance.delete()
        return render(request, "guest/bands/balance.html", {"band": band})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})


'''
    Wristbands
'''
@group_required("admins")
def wristbands(request):
    return render (request, "wristbands/wristbands.html", {'active': 'searchbands'})

@group_required("admins")
def wristbands_search(request):
    value = reverse_cardkey(get_param(request.GET, "value"))
    band_result = Wristband.objects.filter(code=value)
    return render (request, "wristbands/wristbands-search.html", {'band_list': band_result, 'band_code': value})

'''
    Wristbands by project
'''
@group_required("projects")
def wristbands_by_project(request):
    try:
        return render (request, "wristbands-by-project/wristbands.html", {'active': 'searchbands'})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def wristbands_search_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        value = reverse_cardkey(get_param(request.GET, "value"))
        band_result = Wristband.objects.filter(code=value, guest__project_id=project.uuid)
        return render (request, "wristbands-by-project/wristbands-search.html", {'band_list': band_result, 'band_code': value})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


