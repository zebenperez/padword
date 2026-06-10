from datetime import datetime, date, time
from padword import settings
from bookings.models import GuestUser
from datetime import datetime
from padword.commons import get_date_ini, get_date_end
from .models import Guest
from .wristband_models import WristbandBackup

import os


def write_log(uuid, result):
    #band_name = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_bands.log'
    #f = open(os.path.join(settings.BASE_DIR, "media", "wristbands", "bands.log"), "a", encoding='utf-8')
    f = open(os.path.join(settings.BASE_DIR, "wristbands.log"), "a", encoding='utf-8')
    f.write("{}\n".format(result))
    f.close()

def close_band_by_regime_and_soft_remove(project, code=""):
    write_log(project.uuid, f"---------------------------------------------")
    write_log(project.uuid, f"CERRANDO PULSERAS {datetime.now()}")
    try:
        today = date.today()
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)
        guest_list = Guest.objects.filter(
            project_id=project.uuid,
            deleted=0,
            check_out__range=(start,end),
            regimes__regime__code__in=[code]
        )
        msg = ""
        for guest in guest_list:
            msg += "Deleting guest: {} {}\n".format(guest.name, guest.surname)
            for band in guest.bands.all():
                msg += "Deleting band: {} {}\n".format(band.name, band.code)
                band.make_close()
                band.delete()
            GuestUser.delete_by_guest(guest.UUID)
            msg += guest.delete_soft()
            write_log(project.uuid, f"{msg}")
            #print(msg)
    except Exception as e:
        write_log(project.uuid, f"{e}")

def get_daily_close_bands(date):
    item_list = WristbandBackup.objects.filter(date__range=(get_date_ini(date), get_date_end(date)))
    i_list = []
    for item in item_list:
        dic = {
            'room': item.guest_room,
            'guest': item.guest_name,
            'start_date': item.check_in,
            'end_date': item.check_out,
            'name': item.name,
            'type': item.type,
            'kid': item.kid,
            'balance': item.balance,
        }
        i_list.append(dic)
    return i_list
