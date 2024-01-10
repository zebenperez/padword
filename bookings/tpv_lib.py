from bookings.models import Cash, FormInstance
from padword.commons import get_float

import datetime 


def get_date_z():
    return datetime.datetime.strptime("{} 23:59:59".format(datetime.datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d %H:%M:%S")

def cash_exists(pos):
    return Cash.objects.filter(project_uuid=pos.project.uuid, pos_uuid=pos.uuid, date=get_date_z()).count() > 0

def get_cash(pos, date, username=""):
    cash, created = Cash.objects.get_or_create(project_uuid=pos.project.uuid, pos_uuid=pos.uuid, date=date)
    if created:
        cash.username = username
        cash.save()
    return cash, created

#def generate_cash(project, pos, user, date_str, cash_type, ini_cash=0):
#    s_date = datetime.datetime.strptime("{} 00:00".format(date_str), "%Y-%m-%d %H:%M")
#    if cash_type == "z":
#        e_date = datetime.datetime.strptime("{} 23:59:59".format(date_str), "%Y-%m-%d %H:%M:%S")
#    else:
#        e_date = datetime.datetime.strptime("{} {}".format(date_str, datetime.datetime.now().strftime("%H:%M:%S")), "%Y-%m-%d %H:%M:%S")
#
#    #if zeta_exists(pos, e_date):
#    #    return None
#
#    fi_list = FormInstance.objects.filter(pos_uuid=pos.uuid, date__range=(s_date, e_date))
#
#    cash_total = 0
#    band_total = 0
#    card_total = 0
#    back_total = 0
#    free_total = 0
#    for fi in fi_list:
#        if fi.get_status == None:
#            fi.set_status("05", user, "Cancell in Z!")
#        elif fi.get_status.status != None and fi.get_status.status.code != "05":
#            amount = get_float(fi.amount.replace(",", "."))
#            if fi.payment_type.code == "01":
#                cash_total += amount
#            elif fi.payment_type.code == "02":
#                card_total += amount
#            elif fi.payment_type.code == "03":
#                band_total += amount
#            elif fi.payment_type.code == "04":
#                back_total += amount
#            elif fi.payment_type.code == "05":
#                free_total += amount
#
#    #cash = Cash(project_uuid = project.uuid, pos_uuid = pos.uuid, date = e_date)
#    cash, created = get_cash(pos, e_date, user.username)
#    cash.ini_cash = ini_cash
#    cash.end_cash = cash_total
#    cash.band = band_total
#    cash.card = card_total
#    cash.back = back_total
#    cash.free = free_total
#    #cash.username = request.user.username
#    cash.save()
#    return cash
#
def update_cash(cash, user):
    date = cash.date.strftime("%Y-%m-%d")
    s_date = datetime.datetime.strptime("{} 00:00:00".format(date), "%Y-%m-%d %H:%M:%S")
    e_date = datetime.datetime.strptime("{} 23:59:59".format(date), "%Y-%m-%d %H:%M:%S")

    fi_list = FormInstance.objects.filter(pos_uuid=cash.pos_uuid, date__range=(s_date, e_date))

    cash_total = 0
    band_total = 0
    card_total = 0
    back_total = 0
    free_total = 0
    for fi in fi_list:
        if fi.get_status == None:
            fi.set_status("05", user, "Cancell in Z!")
        elif fi.get_status.status != None and fi.get_status.status.code != "05":
            amount = get_float(fi.amount.replace(",", "."))
            if fi.payment_type.code == "01":
                cash_total += amount
            elif fi.payment_type.code == "02":
                card_total += amount
            elif fi.payment_type.code == "03":
                band_total += amount
            elif fi.payment_type.code == "04":
                back_total += amount
            elif fi.payment_type.code == "05":
                free_total += amount

    cash.end_cash = cash_total
    cash.band = band_total
    cash.card = card_total
    cash.back = back_total
    cash.free = free_total
    cash.save()
    return cash

