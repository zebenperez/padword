from django.conf import settings
from django.db.models import Sum, Max

from bookings.models import Cash, FormInstance
from padword.commons import get_int, get_float, translate2
from bookings.models import FormInstance
from connector.models import ProjectWinhotelUser
from contents.models import ShoppingCart

import datetime, csv, os, ftplib

FILES_DIR = os.path.join(settings.BASE_DIR, "media/tpv/orders-daily/")

def get_date_z():
    return datetime.datetime.strptime("{} 23:59:59".format(datetime.datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d %H:%M:%S")

def get_number_z(pos_uuid):
    return get_int(Cash.objects.filter(pos_uuid=pos_uuid, zeta=True).aggregate(Max("number"))["number__max"]) + 1

def get_number_x(pos_uuid):
    return get_int(Cash.objects.filter(pos_uuid=pos_uuid, zeta=False).aggregate(Max("number"))["number__max"]) + 1

'''
    CASH
'''
def cash_exists(pos):
    return Cash.objects.filter(project_uuid=pos.project.uuid, pos_uuid=pos.uuid, date=get_date_z()).count() > 0

#def get_cash(pos, date, username=""):
def get_cash_zeta(pos, username=""):
    cash, created = Cash.objects.get_or_create(project_uuid=pos.project.uuid, pos_uuid=pos.uuid, date=get_date_z())
    if created:
        cash.zeta = True
        cash.number = get_number_z(pos.uuid)
        cash.username = username
        cash.save()
    return cash, created

#    created = False
#    cash = Cash.objects.filter(project_uuid=pos.project.uuid, pos_uuid=pos.uuid, date=date).first()
#    if cash == None:
#        cash = Cash.objects.create(project_uuid=pos.project.uuid, pos_uuid=pos.uuid, date=date)
#        created = True
#    return cash, created

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
def cancel_open_orders(cash, user):
    fi_list = FormInstance.objects.filter(pos_uuid=cash.pos_uuid, status_list__isnull=True)
    for fi in fi_list:
        fi.set_status("05", user, "Cancell in Z!")

def update_cash(cash, user, cancel_orders=False):
    date = cash.date.strftime("%Y-%m-%d")
    s_date = datetime.datetime.strptime("{} 00:00:00".format(date), "%Y-%m-%d %H:%M:%S")
    e_date = datetime.datetime.strptime("{} 23:59:59".format(date), "%Y-%m-%d %H:%M:%S")

    if cancel_orders:
        cancel_open_orders(cash, user)

    fi_list = FormInstance.objects.filter(pos_uuid=cash.pos_uuid, date__range=(s_date, e_date))

    cash_total = 0
    band_total = 0
    card_total = 0
    back_total = 0
    back_card_total = 0
    back_band_total = 0
    free_total = 0
    val1_total = 0
    val2_total = 0
    for fi in fi_list:
        #if fi.get_status == None:
        #    fi.set_status("05", user, "Cancell in Z!")
        if fi.get_status != None and fi.get_status.status != None and fi.get_status.status.code != "05" and fi.payment_type != None:
            amount = get_float(fi.amount)
            if fi.payment_type.code == "01":
                cash_total += amount
            elif fi.payment_type.code == "02":
                card_total += amount
            elif fi.payment_type.code == "03":
                band_total += amount
            elif fi.payment_type.code == "0401":
                back_total += amount
            elif fi.payment_type.code == "0402":
                back_card_total += amount
            elif fi.payment_type.code == "0403":
                back_band_total += amount
            elif fi.payment_type.code == "05":
                free_total += amount
                
            #if fi.payment_type.code == "01" or fi.payment_type.code == "02":
            #    val1_total += get_drinks_total(fi, fi.band)
            #    val2_total += get_food_total(fi, fi.band)

    cash.end_cash = cash_total
    cash.band = band_total
    cash.card = card_total
    cash.back = back_total
    cash.back_card = back_card_total
    cash.back_band = back_band_total
    cash.free = free_total
    cash.val1 = val1_total
    cash.val2 = val2_total
    cash.save()
    return cash

#def cash_daily_summary(obj, date):
#    s_date = datetime.datetime.strptime("{} 00:00:00".format(date), "%Y-%m-%d %H:%M:%S")
#    e_date = datetime.datetime.strptime("{} 23:59:59".format(date), "%Y-%m-%d %H:%M:%S")
#
#    f = open("{}{}_{}07.csv".format(FILES_DIR, e_date.strftime("%Y%m%d_%H%M"), obj.ext_code), "w", encoding='utf-8')
#
#    writer = csv.writer(f)
#    writer.writerow(['_TPV', '_TPVNom', '_Rate', 'ProductUId', '_Description', 'Date', 'Tiket_UID', '_Price', '_Units', '_Discount', 'TotalPrice', '_Room', '_ClientId'])
#
#    fi_list = FormInstance.objects.filter(pos_uuid=obj.uuid, date__range=(s_date, e_date))
#    for fi in fi_list:
#        if fi.get_status != None and fi.get_status.status != None and fi.get_status.status.code != "05":
#            info = fi.info.first()
#            room = info.client_room if info != None else ""
#            client_id = info.client_id if info != None else ""
#            for item in fi.get_items:
#                #code = obj.name[:4].upper()
#                name = obj.name
#                desc = translate2("es", item.name).replace('"', '')
#                date = fi.date.strftime("%Y%m%d%H%M")
#                if fi.payment_type != None and fi.payment_type.code == "05":
#                    discount = 100
#                    total_price = 0
#                else:
#                    discount = 100-((item.low_price/item.price)*100) if item.low_price < item.price and item.low_price > -1 else 0
#                    total_price = item.low_price if item.low_price < item.price and item.low_price > -1 else item.price
#                    #if fi.payment_type != None and fi.payment_type.code == "04":
#                    if fi.payment_type != None and "04" in fi.payment_type.code:
#                        total_price = total_price * -1
#                discount = "{:.2f}".format(discount)
#                writer.writerow([obj.ext_code, name, "", item.item.ext_id, desc, date, fi.id, item.price, 1, discount, total_price, room, client_id])
#    f.close()
#
#def cash_send_daily_summary(project_uuid, obj, date):
#    try:
#        e_date = datetime.datetime.strptime("{} 23:59:59".format(date), "%Y-%m-%d %H:%M:%S")
#        f_name = "{}_{}07.csv".format(e_date.strftime("%Y%m%d_%H%M"), obj.ext_code)
#        f = open("{}{}".format(FILES_DIR, f_name), "rb")
#
#        pau = ProjectWinhotelUser.objects.filter(project_uuid=project_uuid).first()
#        ftp = pau.ftp.split("@")
#        ftp_server = ftp[1]
#        ftp_up = ftp[0].split(":")
#        ftp_user = ftp_up[1].replace("//", "")
#        ftp_pass = ftp_up[2]
#        session = ftplib.FTP(ftp_server, ftp_user, ftp_pass)
#        session.cwd('LIQUIDACIONES')
#        session.storbinary("STOR {}".format(f_name), f)
#        f.close()
#        session.quit()
#    except Exception as e:
#        print("ERROR: {}".format(e))
#
##Bebidas
##Comidas
##Efectivo
##Tarjetas
#def cash_send_charge(cash, source, total_amount, cash_code):
#    now = datetime.datetime.now()
#
#    booking_code = band.guest.ext_id
#    room_code = "ZTPV"
#    contact_name = cash.pos.name
#    contact_id = "???"
#    has_credit = "true"
#    limit_credit = 0
#    source = source
#    source_document = "LIQ ZETA {} {}".format(cash.pos.name, now.strftime("%Y-%m-%d"))
#    date = now.strftime("%Y-%m-%dT%H:%M:%S")
#    total_amount = total_amount
#    cash_code = cash_code
#
#    send_charge(pwu,booking_code,room_code,contact_name,contact_id,has_credit,limit_credit,source,source_document,date,total_amount,cash_code)
#
#def cash_send_charges(cash):
#    date = cash.date.strftime("%Y-%m-%d")
#    s_date = datetime.datetime.strptime("{} 00:00:00".format(date), "%Y-%m-%d %H:%M:%S")
#    e_date = datetime.datetime.strptime("{} 23:59:59".format(date), "%Y-%m-%d %H:%M:%S")
#
#    fi_list = FormInstance.objects.filter(pos_uuid=cash.pos_uuid, date__range=(s_date, e_date))
#
#    total_drinks = 0
#    total_food = 0
#    total_break = 0
#    total_cash = 0
#    total_card = 0
#
#    for fi in fi_list:
#        total_drinks += get_drinks_total(fi, None)
#        total_food += get_food_total(fi, None)
#        total_break += get_breakfast_total(fi, None)
#        
#        total_low = fi.get_total_low
#        total = fi.get_total
#        if fi.payment_type.code == "01":
#            total_cash += total_low if total_low < total else total
#        if fi.payment_type.code == "02":
#            total_card += total_low if total_low < total else total
#
#    cash_send_charge(cash, "BEBIDAS", total_drinks, "")
#    cash_send_charge(cash, "COMIDAS", total_food, "")
#    cash_send_charge(cash, "DESAYUNOS", total_break, "")
#
#    cash_send_charge(cash, "EFECTIVO", total_cash, "")
#    cash_send_charge(cash, "TARJETA", total_card, "")
#    
