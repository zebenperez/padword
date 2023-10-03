from django.template.loader import render_to_string
from datetime import datetime, timedelta
from connector.avantio_lib import get_booking_list, get_booking_notif, send_link
from connector.winhotel_lib import get_booking_list as wh_get_booking_list
from web.models import Project
from connector.models import ProjectAvantioUser, ProjectWinhotelUser
from padword.commons import get_or_none
from padword.email_lib import send_email



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
            send_email(subject, result, "no-reply@padword.es", [pau.email])
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
        e_date = now + timedelta(days=pau.days)
        booking_list, err = wh_get_booking_list(pau, s_date.strftime("%Y-%m-%d"), e_date.strftime("%Y-%m-%d"))
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
        booking_list, err = wh_get_booking_list(pau, "", "")
        result += render_to_string('winhotel/booking-log.html', {'booking_list': booking_list, "error": err})

        #pau = ProjectWinhotelUser.objects.filter(project_uuid=project.uuid).first()
        #if pau != None and pau.email != "":
        #    subject = "Importación {} {}".format(project_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        #    send_email(subject, result, "no-reply@padword.es", [pau.email])
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
