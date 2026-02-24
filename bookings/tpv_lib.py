from django.conf import settings
from django.db.models import Sum, Max

from bookings.models import Cash, FormInstance
from padword.commons import get_int, get_float, translate2
from bookings.models import FormInstance
from connector.models import ProjectWinhotelUser
from contents.models import ShoppingCart

import datetime, csv, os, ftplib


def get_date_z(local_date):
    return datetime.datetime.strptime("{} 23:59:59".format(local_date.strftime("%Y-%m-%d")), "%Y-%m-%d %H:%M:%S")
    #return datetime.datetime.strptime("{} 23:59:59".format(datetime.datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d %H:%M:%S")

def get_number_z(pos_uuid):
    return get_int(Cash.objects.filter(pos_uuid=pos_uuid, zeta=True).aggregate(Max("number"))["number__max"]) + 1

def get_number_x(pos_uuid):
    return get_int(Cash.objects.filter(pos_uuid=pos_uuid, zeta=False).aggregate(Max("number"))["number__max"]) + 1

'''
    CASH
'''
def cash_exists(pos):
    return Cash.objects.filter(project_uuid=pos.project.uuid, pos_uuid=pos.uuid, date=get_date_z()).count() > 0

def get_cash_zeta(pos, username=""):
    local_date = pos.project.local_date(datetime.datetime.now())
    cash, created = Cash.objects.get_or_create(project_uuid=pos.project.uuid, pos_uuid=pos.uuid, date=get_date_z(local_date))
    if created:
        cash.zeta = True
        cash.number = get_number_z(pos.uuid)
        cash.username = username
        cash.save()
    return cash, created

def cancel_open_orders(cash, user):
    fi_list = FormInstance.objects.filter(pos_uuid=cash.pos_uuid, status_list__isnull=True)
    for fi in fi_list:
        fi.set_status("05", user, "Cancell in Z!")

def update_cash(cash, user, cancel_orders=False):
    #date = cash.date.strftime("%Y-%m-%d")
    #s_date = datetime.datetime.strptime("{} 00:00:00".format(date), "%Y-%m-%d %H:%M:%S")
    #e_date = datetime.datetime.strptime("{} 23:59:59".format(date), "%Y-%m-%d %H:%M:%S")

    if cancel_orders:
        cancel_open_orders(cash, user)

    #fi_list = FormInstance.objects.filter(pos_uuid=cash.pos_uuid, date__range=(s_date, e_date))
    fi_list = FormInstance.get_by_local_date(cash.date.strftime("%Y-%m-%d"), cash.pos)

    cash_total = 0
    band_total = 0
    card_total = 0
    room_total = 0
    cardpay_total = 0
    back_total = 0
    back_card_total = 0
    back_band_total = 0
    back_room_total = 0
    back_cardpay_total = 0
    free_total = 0
    val1_total = 0
    val2_total = 0
    for fi in fi_list:
        if fi.get_status != None and fi.get_status.status != None and fi.get_status.status.code != "05" and fi.payment_type != None:
            amount = get_float(fi.amount)
            if fi.payment_type.code == "01":
                cash_total += amount
            elif fi.payment_type.code == "02":
                card_total += amount
            elif fi.payment_type.code == "03":
                band_total += amount
            elif fi.payment_type.code == "08":
                room_total += amount
            elif fi.payment_type.code == "06":
                cardpay_total += amount
            elif fi.payment_type.code == "0401":
                back_total += amount
            elif fi.payment_type.code == "0402":
                back_card_total += amount
            elif fi.payment_type.code == "0403":
                back_band_total += amount
            elif fi.payment_type.code == "0408":
                back_room_total += amount
            elif fi.payment_type.code == "0406":
                back_cardpay_total += amount
            elif fi.payment_type.code == "05":
                free_total += fi.get_total_total
                #free_total += amount
                
    cash.end_cash = cash_total
    cash.band = band_total
    cash.card = card_total
    cash.room = room_total
    cash.cardpay = cardpay_total
    cash.back = back_total
    cash.back_card = back_card_total
    cash.back_band = back_band_total
    cash.back_room = back_room_total
    cash.back_cardpay = back_cardpay_total
    cash.free = free_total
    cash.val1 = val1_total
    cash.val2 = val2_total
    cash.save()
    return cash


