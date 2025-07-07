from connector.paytef_lib import Paytef
from connector.models import ProjectPaytefUser
from padword.commons import get_float
import time

def manage_transaction(project, total, ref, tcod=""): 
    amount = round(get_float(total), 2) * 100
    ppu = ProjectPaytefUser.objects.filter(project_uuid=project.uuid).first()
    pt = Paytef("", "", "", ppu.accessKey, ppu.secretKey, ppu.token)
    if tcod == "":
        tcod = ppu.tcod
    session = pt.transaction_start_query(ppu, tcod, amount, ref)

    trans_ok = False
    start_time = time.time()  # Guarda el momento de inicio
    timeout = 60  # Segundos
    while time.time() - start_time < timeout:
        #print("Ejecutando tarea...")  
        time.sleep(1)  # Espera 1 segundo entre iteraciones (opcional)
        #res = pt.transaction_poll_query(ppu.tcod)
        res = pt.transaction_poll_query(tcod)
        #print("¡Bucle terminado después de 10 segundos!")
        try:
            #if info["transactionConfirmed"] == "true" and info["transactionStatus"] == "finished" and info["sessionID"] == session:
            info = res["info"]
            result = res["result"]
            if info["transactionStatus"] == "finished":
                if result["approved"] == True and result["failed"] == False and info["sessionID"] == session:
                    trans_ok = True
                break
        except:
            pass

    return trans_ok

def paytef_scan_band(project, tcod=""): 
    ppu = ProjectPaytefUser.objects.filter(project_uuid=project.uuid).first()
    pt = Paytef("", "", "", ppu.accessKey, ppu.secretKey, ppu.token)
    if tcod == "":
        return ""

    msg = pt.mifare_start_query(ppu, tcod)
    band_code = ""
    start_time = time.time()  # Guarda el momento de inicio
    timeout = 60  # Segundos
    while time.time() - start_time < timeout:
        time.sleep(1)  # Espera 1 segundo entre iteraciones (opcional)
        res = pt.mifare_poll_query(tcod)
        try:
            info = res["info"]
            result = res["result"]
            if info["finished"] == True:
                if result["success"] == True:
                    try:
                        band_code = int(result["cardUID"], 16)
                    except:
                        band_code = ""
                break
        except:
            pass
    return band_code

