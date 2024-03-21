from django.conf import settings
from django.db.models import Sum

from contents.models import ShoppingCart
from bookings.models import Cash, FormInstance
from padword.commons import get_float, translate2
from bookings.models import FormInstance
from connector.models import ProjectWinhotelUser

import datetime, csv, os, ftplib

FILES_DIR = os.path.join(settings.BASE_DIR, "media/tpv/orders-daily/")

def get_drinks_total(fi, band):
    regime = band.guest.regime.code if band != None and band.guest != None and band.guest.regime != None else ""
    if regime == "":
        total = ShoppingCart.objects.filter(form_instance_id=fi.pk, item__ext_id__lt=50000).aggregate(Sum('price'))["price__sum"]
    else:
        total = ShoppingCart.objects.filter(form_instance_id=fi.pk, item__ext_id__lt=50000).aggregate(Sum('low_price'))["low_price__sum"]
    return total
 
def get_food_total(fi, band):
    break_list = [56029, 56030, 56031, 56032]
    regime = band.guest.regime.code if band != None and band.guest != None and band.guest.regime != None else ""
    if regime == "":
        total = ShoppingCart.objects.filter(form_instance_id=fi.pk, item__ext_id__gte=50000).exclude(item__ext_id__in=break_list).aggregate(Sum('price'))["price__sum"]
    else:
        total = ShoppingCart.objects.filter(form_instance_id=fi.pk, item__ext_id__gte=50000).exclude(item__ext_id__in=break_list).aggregate(Sum('low_price'))["low_price__sum"]
    return total

def get_breakfast_total(fi, band):
    break_list = [56029, 56030, 56031, 56032]
    regime = band.guest.regime.code if band != None and band.guest != None and band.guest.regime != None else ""
    if regime == "":
        total = ShoppingCart.objects.filter(form_instance_id=fi.pk, item__ext_id__in=break_list).aggregate(Sum('price'))["price__sum"]
    else:
        total = ShoppingCart.objects.filter(form_instance_id=fi.pk, item__ext_id__in=break_list).aggregate(Sum('low_price'))["low_price__sum"]
    return total

'''
    CASH
'''
def cash_daily_summary(obj, date):
    s_date = datetime.datetime.strptime("{} 00:00:00".format(date), "%Y-%m-%d %H:%M:%S")
    e_date = datetime.datetime.strptime("{} 23:59:59".format(date), "%Y-%m-%d %H:%M:%S")

    f = open("{}{}_{}07.csv".format(FILES_DIR, e_date.strftime("%Y%m%d_%H%M"), obj.ext_code), "w", encoding='utf-8')

    writer = csv.writer(f)
    writer.writerow(['_TPV', '_TPVNom', '_Rate', 'ProductUId', '_Description', 'Date', 'Tiket_UID', '_Price', '_Units', '_Discount', 'TotalPrice', '_Room', '_ClientId'])

    fi_list = FormInstance.objects.filter(pos_uuid=obj.uuid, date__range=(s_date, e_date))
    for fi in fi_list:
        #Tickets no cancelados
        #if fi.get_status != None and fi.get_status.status != None and fi.get_status.status.code != "05":
        if not fi.current_status("05"):
            info = fi.info.first()
            room = info.client_room if info != None else ""
            client_id = info.client_id if info != None else ""
            for item in fi.get_items:
                #code = obj.name[:4].upper()
                name = obj.name
                desc = translate2("es", item.name).replace('"', '')
                date = fi.date.strftime("%Y%m%d%H%M")
                units = 1
                #Invitación
                if fi.payment_type != None and fi.payment_type.code == "05":
                    discount = 100
                    total_price = 0
                else:
                    #discount = 100-((item.low_price/item.price)*100) if item.low_price < item.price and item.low_price > -1 else 0
                    #total_price = item.low_price if item.low_price < item.price and item.low_price > -1 else item.price
                    discount = 100-((item.total_price/item.price)*100) if item.total_price < item.price else 0
                    total_price = item.total_price
                    #Devolución
                    if fi.payment_type != None and "04" in fi.payment_type.code:
                        #total_price = total_price * -1
                        units = -1
                discount = "{:.2f}".format(discount)
                writer.writerow([obj.ext_code, name, "", item.item.ext_id, desc, date, fi.id, item.price, units, discount, total_price, room, client_id])
    f.close()

def cash_send_daily_summary(project_uuid, obj, date):
    try:
        e_date = datetime.datetime.strptime("{} 23:59:59".format(date), "%Y-%m-%d %H:%M:%S")
        f_name = "{}_{}07.csv".format(e_date.strftime("%Y%m%d_%H%M"), obj.ext_code)
        f = open("{}{}".format(FILES_DIR, f_name), "rb")

        pau = ProjectWinhotelUser.objects.filter(project_uuid=project_uuid).first()
        ftp = pau.ftp.split("@")
        ftp_server = ftp[1]
        ftp_up = ftp[0].split(":")
        ftp_user = ftp_up[1].replace("//", "")
        ftp_pass = ftp_up[2]
        session = ftplib.FTP(ftp_server, ftp_user, ftp_pass)
        session.cwd('LIQUIDACIONES')
        session.storbinary("STOR {}".format(f_name), f)
        f.close()
        session.quit()
    except Exception as e:
        print("ERROR: {}".format(e))

#Bebidas
#Comidas
#Efectivo
#Tarjetas
def cash_send_charge(cash, source, total_amount, cash_code):
    now = datetime.datetime.now()

    booking_code = band.guest.ext_id
    room_code = "ZTPV"
    contact_name = cash.pos.name
    contact_id = "???"
    has_credit = "true"
    limit_credit = 0
    source = source
    source_document = "LIQ ZETA {} {}".format(cash.pos.name, now.strftime("%Y-%m-%d"))
    date = now.strftime("%Y-%m-%dT%H:%M:%S")
    total_amount = total_amount
    cash_code = cash_code

    send_charge(pwu,booking_code,room_code,contact_name,contact_id,has_credit,limit_credit,source,source_document,date,total_amount,cash_code)

def cash_send_charges(cash):
    date = cash.date.strftime("%Y-%m-%d")
    s_date = datetime.datetime.strptime("{} 00:00:00".format(date), "%Y-%m-%d %H:%M:%S")
    e_date = datetime.datetime.strptime("{} 23:59:59".format(date), "%Y-%m-%d %H:%M:%S")

    fi_list = FormInstance.objects.filter(pos_uuid=cash.pos_uuid, date__range=(s_date, e_date))

    total_drinks = 0
    total_food = 0
    total_break = 0
    total_cash = 0
    total_card = 0

    break_list = [56029, 56030, 56031, 56032]
    for fi in fi_list:
        #if fi.get_status != None and fi.get_status.status != None and fi.get_status.status.code != "05":
        #Tickets no cancelados
        if not fi.current_status("05"):

            for item in fi.get_items:
                #item_price = item.low_price if item.low_price < item.price and item.low_price > -1 else item.price
                item_price = item.total_price
                if item.item.ext_id in break_list:
                    total_break += item_price
                elif item.item.ext_id < 50000:
                    total_drinks += item_price
                elif item.item.ext_id >= 50000:
                    total_food += item_price
                if fi.payment_type != None and fi.payment_type.code == "01":
                    total_cash += item_price
                if fi.payment_type != None and fi.payment_type.code == "02":
                    total_card += item_price

    cash_send_charge(cash, "BEBIDAS", total_drinks, "")
    cash_send_charge(cash, "COMIDAS", total_food, "")
    cash_send_charge(cash, "DESAYUNOS", total_break, "")

    cash_send_charge(cash, "EFECTIVO", total_cash, "")
    cash_send_charge(cash, "TARJETA", total_card, "")
    
