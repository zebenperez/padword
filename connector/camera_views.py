from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from datetime import datetime, timedelta
import csv, os, ftplib

from padword.decorators import group_required
from padword.commons import get_or_none, show_exc
from guest.models import Guest
from .models import ProjectCarUser


FILES_DIR = os.path.join(settings.BASE_DIR, "media/cars/")
HEADER = """<?xml version = "1.0" encoding = "utf-8" ?>
<grouplist>
"""
#HEADER = """
#<?xml version = "1.0" encoding = "utf-8" ?>
#<grouplist>
#    <nllists>
#        <nllist id="-2" description="all plates" color="#000000" levenshteindist="0"/>
#        <nllist id="-1" description="not in list" color="#000000" levenshteindist="0"/>
#        <nllist id="1" description="BLOCKLIST" color="#000000" levenshteindist="0"/>
#        <nllist id="2" description="ALLOWLIST" color="#000000" levenshteindist="0"/>
#        <nllist id="3" description="PERMITIDO" color="#000000" levenshteindist="0"/>
#    </nllists>
#    <nlelemlists>
#"""
HEADER_CSV = """
nllist-id;description;color;levenshteindist
-2;all plates;#000000;0
-1;not in list;#000000;0
0;;;0
1;BLOCKLIST;#000000;0
2;ALLOWLIST;#000000;0
3;GUEST;;0
4;Testing;;0
"""
FOOTER = """
</grouplist>
"""
#FOOTER = """
#    </nlelemlists>
#</grouplist>
#"""

def getPath(project_uuid):
    path = "{}{}/".format(FILES_DIR, project_uuid)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

#def get_xml_header(pcu):
#    return """
#        <?xml version = "1.0" encoding = "utf-8" ?>
#        <grouplist>
#            <nllists>
#                <nllist id="{}" description="{}" color="#000000" levenshteindist="0"/>
#            </nllists>
#            <nlelemlists>
#    """.format(pcu.code, pcu.description)

def get_xml_elements(pcu):
    xml = "\n<nlelemlists>"
    now = datetime.now()
    late = now + timedelta(pcu.days)
    now_str = now.strftime("%Y-%m-%dT%H:%M:%S")
    #Reservas activas
    guest_list = list(Guest.objects.filter(check_in__lte=now, check_out__gte=now, project_id=pcu.project_uuid))
    #Reservas que se activarán en pcu.days
    guest_list += list(Guest.objcts.filter(check_in__gt=now, check_in__lte=late, project_id=pcu.project_uuid))
    #Reservas que salesn en pcu.days
    #guest_list += list(Guest.objcts.filter(check_in__gt=now, check_in__lte=late, project_id=pcu.project_uuid))
    for g in guest_list:
        ini_date = g.check_in.strftime("%Y-%m-%dT%H:%M:%S")
        end_date = g.check_out.strftime("%Y-%m-%dT%H:%M:%S")
        for c in g.cars.all():
            xml += """\n<nlelemlist id="{}" numberplate="{}" listid="3" timestamp="{}" description="redcarJoe" startvaliditydate="{}" endvaliditydate="{}"/>""".format(pcu.code, c.number, now_str, ini_date, end_date)
    xml += "\n\n</nlelemlists>"
    return xml

def get_csv_elements(pcu):
    csv = "\nnlelemlist-id;numberplate;listid;timestamp;description;startvaliditydate;endvaliditydate"
    now = datetime.now()
    late = now + timedelta(pcu.days)
    now_str = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    #Reservas activas
    guest_list = list(Guest.objects.filter(check_in__lte=now, check_out__gte=now, project_id=pcu.project_uuid))
    #Reservas que se activarán en pcu.days
    guest_list += list(Guest.objects.filter(check_in__gt=now, check_in__lte=late, project_id=pcu.project_uuid))
    #Reservas que salesn en pcu.days
    #guest_list += list(Guest.objcts.filter(check_in__gt=now, check_in__lte=late, project_id=pcu.project_uuid))
    i = 0
    for g in guest_list:
        print("{} {} {} {}".format(g.name, g.surname, g.check_in, g.check_out))
        ini_date = g.check_in.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        end_date = g.check_out.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        for c in g.cars.all():
            name = "{} {}".format(g.name, g.surname)
            csv += """\n{};{};{};{};{};{};{}""".format(i, c.number, pcu.code, now_str, name, ini_date, end_date)
            i = i+1
    return csv

#def get_xml_footer(pcu):
#    return """</nlelemlists></grouplist>"""

#def car_get(pcu, path, ext):
#    """
#    Descarga un archivo XML desde un servidor FTP.
#
#    Args:
#        servidor (str): Dirección del servidor FTP (ej: 'ftp.ejemplo.com').
#        usuario (str): Nombre de usuario.
#        contraseña (str): Contraseña.
#        ruta_remota (str): Ruta del archivo en el FTP (ej: '/carpeta/archivo.xml').
#        ruta_local (str): Ruta donde se guardará localmente (ej: './descargas/archivo.xml').
#    """
#    try:
#        # Conectarse al servidor FTP
#        ftp = pcu.ftp.split("@")
#        ftp_s = ftp[1].split(":")
#        ftp_server = ftp_s[0]
#        ftp_port = ftp_s[1] if len(ftp_s) > 1 else "21"
#        ftp_up = ftp[0].split(":")
#        ftp_user = ftp_up[1].replace("//", "")
#        ftp_pass = ftp_up[2]
# 
#        with ftplib.FTP(ftp_server) as ftp:
#            ftp.login(user=ft_user, passwd=ftp_pass)
#            print(f"Conexión FTP establecida con {servidor}")
#
#            # Crear directorio local si no existe
#            os.makedirs(path, exist_ok=True)
#
#            # Descargar el archivo en modo binario ('wb')
#            with open(ruta_local, 'wb') as pcu.file_name:
#                ftp.retrbinary(f'RETR {ruta_remota}', archivo_local.write)
#
#            print(f"Archivo descargado: {ruta_local}")
#
#    except Exception as e:
#        print(f"Error al descargar el XML: {e}")

def car_send(pcu, ext):
    try:
        #fm = open("{}matriculas.xml".format(getPath(pcu.project_uuid)), "rb")
        fm = open("{}{}.{}".format(getPath(pcu.project_uuid), pcu.file_name, ext), "rb")
        ffm = open("{}{}.{}.FLAG".format(getPath(pcu.project_uuid), pcu.file_name, ext), "rb")

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
        #f.storbinary("STOR matriculas.xml", fm)
        f.cwd("/{}".format(pcu.dir_name))
        f.storbinary("STOR {}.{}".format(pcu.file_name, ext), fm)
        f.storbinary("STOR {}.{}.FLAG".format(pcu.file_name, ext), ffm)
        fm.close()
        f.quit()
    except Exception as e:
        print("ERROR: {}".format(e))

@group_required("admins", "projects")
def car_plates(request, project_uuid):
    try:
        pcu = get_or_none(ProjectCarUser, project_uuid, "project_uuid")
        pcu_list = ProjectCarUser.objects.filter(project_uuid=project_uuid)
        #xml = get_xml_header(pcu)
        xml = HEADER
        xml += pcu.header_xml
        xml += get_xml_elements(pcu)
        xml += FOOTER
        #xml += get_xml_footer(pcu)
        #f = open("{}matriculas.xml".format(getPath(project_uuid)), "w")
        f = open("{}{}.{}".format(getPath(project_uuid), pcu.file_name, "xml"), "w")
        f.write(xml)
        xml.close()
        ff = open("{}{}.{}.FLAG".format(getPath(project_uuid), pcu.file_name, "xml"), "w")
        ff.close()
        car_send(pcu, "xml")
        #print(xml)
        return HttpResponse("--OK--")
        response = HttpResponse(
            xml,
            content_type='text/xml',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(pcu.file_name)},
            #headers={'Content-Disposition': 'attachment; filename="matriculas.xml"'},
        )
        return response 
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def car_plates_csv(request, project_uuid):
    try:
        pcu = get_or_none(ProjectCarUser, project_uuid, "project_uuid")
        pcu_list = ProjectCarUser.objects.filter(project_uuid=project_uuid)
        #car_get(pcu, getPath(project_uuid), "csv")
        csv = pcu.header_csv
        csv += get_csv_elements(pcu)
        f = open("{}{}.csv".format(getPath(project_uuid), pcu.file_name), "w")
        f.write(csv)
        f.close()
        ff = open("{}{}.csv.FLAG".format(getPath(project_uuid), pcu.file_name), "w")
        ff.close()
        car_send(pcu, "csv")
        return HttpResponse("--OK--")
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

def car_plates_csv_cron(project_uuid):
    try:
        pcu = get_or_none(ProjectCarUser, project_uuid, "project_uuid")
        pcu_list = ProjectCarUser.objects.filter(project_uuid=project_uuid)
        csv = pcu.header_csv
        csv += get_csv_elements(pcu)
        f = open("{}{}.csv".format(getPath(project_uuid), pcu.file_name), "w")
        f.write(csv)
        f.close()
        ff = open("{}{}.csv.FLAG".format(getPath(project_uuid), pcu.file_name), "w")
        ff.close()
        car_send(pcu, "csv")
        return "-- File Sended OK!"
    except Exception as e:
        return "-- Error: {}".format(e)

