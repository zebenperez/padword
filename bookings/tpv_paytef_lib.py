import time

def manage_transaction(): 
    trans_ok = False
    start_time = time.time()  # Guarda el momento de inicio
    timeout = 10  # Segundos
    while time.time() - start_time < timeout:
        print("Ejecutando tarea...")  # Reemplaza con tu lógica
        time.sleep(1)  # Espera 1 segundo entre iteraciones (opcional)
        print("¡Bucle terminado después de 10 segundos!")
    return trans_ok

