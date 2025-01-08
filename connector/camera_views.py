from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from datetime import datetime
import csv, os, ftplib

from padword.decorators import group_required
from padword.commons import get_or_none, show_exc
from guest.models import Guest
from .models import ProjectCarUser


FILES_DIR = os.path.join(settings.BASE_DIR, "media/cars/")

def getPath(project_uuid):
    path = "{}{}/".format(FILES_DIR, project_uuid)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def get_xml_header(pcu):
    return """<?xml version = "1.0" encoding = "utf-8" ?><grouplist><nllists><nllist id="{}" description="{}" color="#000000" levenshteindist="0"/></nllists><nlelemlists>""".format(pcu.code, pcu.description)

def get_xml_elements(pcu):
    xml = ""
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%dT%H:%M:%S")
    guest_list = Guest.objects.filter(check_in__lte=now, check_out__gte=now)
    for g in guest_list:
        ini_date = g.check_in.strftime("%Y-%m-%dT%H:%M:%S")
        end_date = g.check_out.strftime("%Y-%m-%dT%H:%M:%S")
        for c in g.cars.all():
            xml += """<nlelemlist id="{}" numberplate="{}" listid="2" timestamp="{}" description="redcarJoe" startvaliditydate="{}" endvaliditydate="{}"/>""".format(pcu.code, c.number, now_str, ini_date, end_date)
    return xml

def get_xml_footer(pcu):
    return """</nlelemlists></grouplist>"""

def car_send(pcu):
    try:
        fm = open("{}matriculas.xml".format(getPath(pcu.project_uuid)), "rb")

        ftp = pcu.ftp.split("@")
        ftp_s = ftp[1].split(":")
        ftp_server = ftp_s[0]
        ftp_port = ftp_s[1] if len(ftp_s) > 1 else "21"
        ftp_up = ftp[0].split(":")
        ftp_user = ftp_up[1].replace("//", "")
        ftp_pass = ftp_up[2]
        f = ftplib.FTP()
        f.connect(ftp_server, int(ftp_port))
        f.login(ftp_user, ftp_pass)
        #session.cwd('LIQUIDACIONES')
        f.storbinary("STOR matriculas.xml", fm)
        fm.close()
        f.quit()
    except Exception as e:
        print("ERROR: {}".format(e))

@group_required("admins", "projects")
def car_plates(request, project_uuid):
    try:
        pcu = get_or_none(ProjectCarUser, project_uuid, "project_uuid")
        xml = get_xml_header(pcu)
        xml += get_xml_elements(pcu)
        xml += get_xml_footer(pcu)
        f = open("{}matriculas.xml".format(getPath(project_uuid)), "w")
        f.write(xml)
        f.close()
        car_send(pcu)
        print(xml)
        return HttpResponse("--OK--")
        response = HttpResponse(
            xml,
            content_type='text/xml',
            headers={'Content-Disposition': 'attachment; filename="matriculas.xml"'},
        )
        return response 
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})
