from django.template.loader import render_to_string
from datetime import datetime
from connector.avantio_lib import get_booking_list, get_booking_notif, send_link
from web.models import Project
from padword.commons import get_or_none


def avantio_booking_schedule(project_uuid):
    #project_uuid = "0fa03300-2646-b206-981b-b078262cacc5"
    project = get_or_none(Project, project_uuid, "uuid")
    project_name = project.name if project != None else "---"
    result = "\n<br/>Importación {} {}<br/>\n".format(project_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    result += "-----------------------------------------------------<br/>\n"
    try:
        booking_list, err = get_booking_list(project_uuid)
        result += render_to_string('avantio/booking-list.html', {'booking_list': booking_list, "error": err})
    except Exception as e:
        print("\n<br/>Error: {}".format(e))
    print(result)

def avantio_notification_schedule(project_uuid):
    #project_uuid = "0fa03300-2646-b206-981b-b078262cacc5"
    project = get_or_none(Project, project_uuid, "uuid")
    project_name = project.name if project != None else "---"
    result = "\n<br/>Notificaciones {} {}<br/>\n".format(project_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    result += "-----------------------------------------------------<br/>\n"
    try:
        booking_list = get_booking_notif(project_uuid)
        result += render_to_string('avantio/booking-list.html', {'booking_list': booking_list})
    except Exception as e:
        print("\n<br/>Error: {}".format(e))
    print(result)
