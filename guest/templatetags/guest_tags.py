from django import template

from padword.commons import show_exc
from guest.models import KeyCode, KeyCard
from guest.wristband_models import WristbandAccessZoneGuest

register = template.Library()

'''
    Filters
'''
@register.filter
def zone_active(guest, zone):
    return WristbandAccessZoneGuest.objects.filter(guest=guest, zone=zone).first() != None

@register.filter
def have_open_band(guest):
    for band in guest.bands.all():
        if not band.is_close:
            return True
    return False

'''
    Inclusion Tags
'''
@register.inclusion_tag('guest/keys/guest-key-codes.html')
def guest_key_codes(guest, lock):
    key_code_list = KeyCode.objects.filter(guest=guest, lock=lock)
    return {'key_code_list': key_code_list,}

@register.inclusion_tag('guest/keys/guest-key-codes-show.html')
def guest_key_codes_show(guest, lock):
    key_code_list = KeyCode.objects.filter(guest=guest, lock=lock)
    return {'key_code_list': key_code_list,}

@register.inclusion_tag('guest/keys/guest-key-cards.html')
def guest_key_cards(guest, lock):
    key_card_list = KeyCard.objects.filter(guest=guest, lock=lock)
    return {'key_card_list': key_card_list, 'guest': guest, 'lock': lock}

