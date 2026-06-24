from datetime import datetime, date, time
from padword import settings
from bookings.models import GuestUser
from datetime import datetime
from padword.commons import get_date_ini, get_date_end
from .models import Guest
from .wristband_models import Wristband, WristbandBackup

import os


def write_log(uuid, result):
    #band_name = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_bands.log'
    #f = open(os.path.join(settings.BASE_DIR, "media", "wristbands", "bands.log"), "a", encoding='utf-8')
    f = open(os.path.join(settings.BASE_DIR, "wristbands.log"), "a", encoding='utf-8')
    f.write("{}\n".format(result))
    f.close()

#def close_band_by_regime_and_soft_remove(project, code=""):
def close_band_by_regime_and_soft_remove(project, start_date, end_date):
    write_log(project.uuid, f"---------------------------------------------")
    write_log(project.uuid, f"CERRANDO PULSERAS {datetime.now()}")
    try:
        #today = date.today()
        #start = datetime.combine(today, time.min)
        #end = datetime.combine(today, time.max)
        #guest_list = Guest.objects.filter( project_id=project.uuid, deleted=0, check_out__range=(start,end), regimes__regime__code__in=[code])
        guest_list = Guest.objects.filter(project_id=project.uuid, deleted=0, check_out__range=(start,end))
        msg = ""
        for guest in guest_list:
            msg += "Deleting guest: {} {}\n".format(guest.name, guest.surname)
            for band in guest.bands.all():
                msg += "Deleting band: {} {}\n".format(band.name, band.code)
                band.make_new_close()
                band.delete()
            GuestUser.delete_by_guest(guest.UUID)
            msg += guest.delete_soft()
            write_log(project.uuid, f"{msg}")
            #print(msg)
    except Exception as e:
        write_log(project.uuid, f"{e}")

def get_daily_close_bands(project_uuid, ini_date, end_date):
    #item_list = WristbandBackup.objects.filter(project_uuid=project_uuid, date__range=(get_date_ini(date), get_date_end(date)))
    item_list = WristbandBackup.objects.filter(project_uuid=project_uuid, date__range=(ini_date, end_date))
    i_list = []
    for item in item_list:
        dic = {
            'code': item.code,
            'name': item.name,
            'room': item.guest_room,
            'guest': item.guest_name,
            'start_date': item.check_in,
            'end_date': item.check_out,
            'type': item.type,
            #'kid': item.kid,
            'balance': item.balance,
        }
        i_list.append(dic)
    return i_list

def get_daily_open_bands(project_uuid, ini_date, end_date):
    item_list = Wristband.objects.filter(guest__check_out__range=(ini_date, end_date), guest__project_id=project_uuid)
    i_list = []
    for item in item_list:
        btype = item.type.name if item.type != None else ""
        dic = {
            'code': item.code,
            'name': item.name,
            'room': item.guest.room,
            'guest': f"{item.guest.name} {item.guest.surname}",
            'start_date': item.guest.check_in,
            'end_date': item.guest.check_out,
            'type': btype,
            #'kid': item.kid,
            'balance': item.balance,
        }
        i_list.append(dic)
    print("--2--")
    print(i_list)
    return i_list
