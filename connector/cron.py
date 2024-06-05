from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime, timedelta

from connector.avantio_lib import get_booking_list, get_booking_notif, send_link
from connector.winhotel_lib import get_booking_list as wh_get_booking_list, get_booking_cancelled as wh_get_booking_cancelled
from connector.winhotel_lib import import_item_prices as wh_import_item_prices, get_booking_new_list as wh_get_booking_new_list
from web.models import Project, ProjectLockUser
from web.models_lock import Lock, LockCron
from connector.models import ProjectAvantioUser, ProjectWinhotelUser
from padword.commons import get_or_none
from padword.email_lib import send_email

import os, subprocess, time


def avantio_booking_schedule(project_uuid):
    #project_uuid = "0fa03300-2646-b206-981b-b078262cacc5"
    project = get_or_none(Project, project_uuid, "uuid")
    project_name = project.name if project != None else "---"
    result = "Importación {} {}\n".format(project_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    result += "-----------------------------------------------------"
    try:
        booking_list, err = get_booking_list(project_uuid)
        result += render_to_string('avantio/booking-log.html', {'booking_list': booking_list, "error": err})

        pau = ProjectAvantioUser.objects.filter(project_uuid=project.uuid).first()
        if pau != None and pau.email != "":
            subject = "Importación {} {}".format(project_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            send_email(subject, result, settings.EMAIL_FROM_DEFAULT, [pau.email])
            #send_email(subject, result, "no-reply@padword.es", [pau.email])
    except Exception as e:
        print("\n<br/>Error: {}".format(e))
    print(result)

def avantio_notification_schedule(project_uuid):
    #project_uuid = "0fa03300-2646-b206-981b-b078262cacc5"
    project = get_or_none(Project, project_uuid, "uuid")
    project_name = project.name if project != None else "---"
    result = "Notificaciones {} {}\n".format(project_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    result += "-----------------------------------------------------"
    try:
        booking_list = get_booking_notif(project_uuid)
        result += render_to_string('avantio/booking-log.html', {'booking_list': booking_list})
    except Exception as e:
        print("\n<br/>Error: {}".format(e))
    print(result)

def winhotel_booking_schedule(project_uuid):
    project = get_or_none(Project, project_uuid, "uuid")
    project_name = project.name if project != None else "---"
    result = "Importación Winhotel {} {}\n".format(project_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    result += "-----------------------------------------------------"
    try:
        pau = ProjectWinhotelUser.objects.filter(project_uuid=project.uuid).first()
        s_date = datetime.now()
        e_date = s_date + timedelta(days=pau.days)
        #booking_list, err = wh_get_booking_list(pau, s_date.strftime("%Y-%m-%d"), e_date.strftime("%Y-%m-%d"))
        #booking_list, err = wh_get_booking_list(pau, "1")
        booking_list, err = wh_get_booking_new_list(pau, "1")
        result += render_to_string('winhotel/booking-log.html', {'booking_list': booking_list, "error": err})

        #pau = ProjectWinhotelUser.objects.filter(project_uuid=project.uuid).first()
        #if pau != None and pau.email != "":
        #    subject = "Importación {} {}".format(project_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        #    send_email(subject, result, "no-reply@padword.es", [pau.email])
    except Exception as e:
        print("\n<br/>Error: {}".format(e))
    print(result)

def winhotel_check_schedule(project_uuid):
    project = get_or_none(Project, project_uuid, "uuid")
    project_name = project.name if project != None else "---"
    result = "Chequeo Winhotel {} {}\n".format(project_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    result += "-----------------------------------------------------"
    try:
        pau = ProjectWinhotelUser.objects.filter(project_uuid=project.uuid).first()
        booking_list, err = wh_get_booking_list(pau, "2")
        result += render_to_string('winhotel/booking-log.html', {'booking_list': booking_list, "error": err})

        #pau = ProjectWinhotelUser.objects.filter(project_uuid=project.uuid).first()
        #if pau != None and pau.email != "":
        #    subject = "Importación {} {}".format(project_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        #    send_email(subject, result, "no-reply@padword.es", [pau.email])
    except Exception as e:
        print("\n<br/>Error: {}".format(e))
    print(result)

def winhotel_price_schedule(project_uuid):
    updated = []
    not_updated = []
    project = get_or_none(Project, project_uuid, "uuid")
    project_name = project.name if project != None else "---"
    now = datetime.now()
    result = "Importar precios Winhotel {} {}\n".format(project_name, now.strftime("%Y-%m-%d %H:%M:%S"))
    result += "-----------------------------------------------------"
    try:
        #url = "ftp://L0F98HH:P00IkMMhs!2@51.38.104.89/20231107_Products_07__TPV_HIGO.CSV"
        pau = ProjectWinhotelUser.objects.filter(project_uuid=project.uuid).first()
        fname = "{}_{}".format(now.strftime("%Y%m%d"), pau.ftp_filename)

        url = "{}/{}".format(pau.ftp, fname)
        path = os.path.join(settings.BASE_DIR, "media", "winhotel")
        res = subprocess.run(['wget', '-P', path, url])
        #res = subprocess.run(['wget', '-P', '/srv/dockers/padword/src/padword/media/', url], check=True)
        time.sleep(5)

        file = open(os.path.join(settings.BASE_DIR, "media", "winhotel", fname), 'rb')

        updated, not_updated = wh_import_item_prices(file, project_uuid, pau.update_all_prices)
        result += render_to_string('winhotel/booking-price-log.html', {'updated': updated, "not_updated": not_updated})
    except Exception as e:
        print("\n<br/>Error: {}".format(e))
    print(result)

def winhotel_cancel_schedule(project_uuid):
    project = get_or_none(Project, project_uuid, "uuid")
    project_name = project.name if project != None else "---"
    result = "Cancelar reservas Winhotel {} {}\n".format(project_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    result += "-----------------------------------------------------"
    try:
        pau = ProjectWinhotelUser.objects.filter(project_uuid=project.uuid).first()
        booking_list, err = wh_get_booking_cancelled(pau, "5")
        result += render_to_string('winhotel/booking-log.html', {'booking_list': booking_list, "error": err})
    except Exception as e:
        print("\n<br/>Error: {}".format(e))
    print(result)


#def avantio_notification_schedule(project_uuid):
#    #project_uuid = "0fa03300-2646-b206-981b-b078262cacc5"
#    project = get_or_none(Project, project_uuid, "uuid")
#    project_name = project.name if project != None else "---"
#    result = "Notificaciones {} {}\n".format(project_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
#    result += "-----------------------------------------------------"
#    try:
#        booking_list = get_booking_notif(project_uuid)
#        result += render_to_string('avantio/booking-log.html', {'booking_list': booking_list})
#    except Exception as e:
#        print("\n<br/>Error: {}".format(e))
#    print(result)


def locks_tasks_schedule(project_uuid):
    project = get_or_none(Project, project_uuid, "uuid")
    project_name = project.name if project != None else "---"
    result = "Ejecución de tareas {} {}\n".format(project_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    result += "-----------------------------------------------------\n"
    try:
        task_list = LockCron.objects.filter(project_uuid=project.uuid, done=False)
        for task in task_list:
            result += "- TAREA [{}] {}: \n".format(task.id, task.task)
            if task.task == "ADD CARD" or task.task == "ADD CODE":
                lock_list = task.lock_list.split(";")
                params = task.params.split(";")
                for lock in lock_list:
                    l = get_or_none(Lock, lock)
                    if l != None:
                        if task.task == "ADD CARD":
                            err = l.add_card(params[0], params[2], params[3], params[1])
                            result += "--- AÑADIENDO TARJETA A CERRADURA [{}]: {}\n".format(l.id, err)
                        elif task.task == "ADD CODE":
                            err = l.set_code(params[0], params[2], params[3], params[1])
                            result += "--- AÑADIENDO CÓDIGO A CERRADURA [{}]: {}\n".format(l.id, err)
            task.done = True
            task.save()

        plu = ProjectLockUser.objects.filter(project_uuid=project.uuid).first()
        #print("--- TEST: {}".format(plu.report_email))
        if plu != None and plu.report_email != "":
            subject = "Informe de tarea {} {}".format(project_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            send_email(subject, result, settings.EMAIL_FROM_DEFAULT, [plu.report_email])
    except Exception as e:
        print("\n<br/>Error: {}".format(e))
    print(result)


