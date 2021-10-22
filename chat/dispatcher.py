#!/usr/bin/python
# -*- coding: utf-8 -*-

# ---
# El Dispatcher sera el encargado de implementar los metodos para interactuar con la base de datos o la caché
#   El modulo estar dividido en dos tipos Feeds y Dispatchers. Los feeds son los elementos encargados de escribir en la base de datos y en la cache
# mientras que los dispatchers son los encargados de consultar la caché y devolver los datos, El objetivo de agrupar estas operaciones en un archivo a modo de API
# es poder cachear datos en el futuro.
# --

import json
import logging
import time
from datetime import datetime as dt

# from django.db.models import Max

# local imports
from .models import LastConnection, Room, Message, messages_to_dic  # , MessgeLink, MessgeImage
from .generic import get_session_feedback
from .utils import get_or_create, random_string
from .cache import UserCache

"""
    CONSTANTS
"""
logger = logging.getLogger(__name__)

STATUS_CODE_INTERRUPTED = -2
STATUS_CODE_TIMEOUT = -1
STATUS_CODE_SUCCESS = 0
STATUS_CODE_ERROR = 1
INTERVAL_TIMEOUT = 2.5
SECURE_EOL_CHAR = "#__EOL__#"
CONNECTION_KILL = "#__KILL_#"

"""
    Getters : Displatcher
    Metodos encargados de recuperar y formatear datos ya sea de base de datos o en caché
"""

# ---
# Recuperar la ultima conexión registrada del usuario.
def get_user_last_connection(user):
    return LastConnection.objects.filter(user=user, room__subscribers=user, room__active=True).select_related("room").order_by("-date").first()

# --
# Recupera las conexiones del usuario, si se pasa el parametro, subscriptions se filtra solo por dichas salas.
# FIXME : Las conexiones deben recuperarse de la caché para ahorrar consultas.
def get_user_connections(user, subscriptions=None):
    return LastConnection.objects.filter(user=user, room__active=True, room__subscribers=user).select_related("room").order_by("room__code")

# ---
# Devuelve la ultima sala en la que el usuario ha entrado
def get_last_room(user):
    last_connection = get_user_last_connection(user)
    if last_connection:
        return last_connection.room
    return None

# --
# Recupera de la cache todas las salas a las que el usuario esta suscrito y el estado de las mismas (ultimo mensaje recibido en la sala y ultima conexion del usuario)
def get_rooms_status_json(user):
    rooms = []
    last_user_connections = get_user_connections(user)
    lastest_connection = None
    for connection in last_user_connections:
        lastest_connection = connection if lastest_connection is None or connection.date > lastest_connection.date else  lastest_connection
        value = connection.room.to_dict(user)
        value['user_last_connection'] = connection.timestamp if connection else time.mktime(dt.min.timetuple())
        value['last_message'] = connection.room.last_message_dict(user)
        rooms.append(value)
    
    response = {'rooms': rooms}
    response['current_room'] = lastest_connection.room.to_dict(user) if lastest_connection is not None else None

    return json.dumps(response)

# --
# Lista los chats privados del usuario comprobando si se ha incorporado algun usuario nuevo y debe crearse su sala.
def get_or_create_private_chats(user):
    chats = Room.objects.filter(subscribers=user, active=True, private=True).order_by("name")
    excluded_users = [user.pk]

    for item in Room.objects.filter(private=True, subscribers=user.pk):
        pk = item.subscribers.exclude(pk=user.pk).first().pk
        if pk not in excluded_users:
            excluded_users.append(pk)

    nochat_contacts = User.objects.filter(is_active=True).exclude(pk__in=excluded_users)
    for item in nochat_contacts:
        try:
            code = "%s%s" % (user.username, item.username)
            chat = Room.objects.create(owner=user, code=code, name=code, description="Chat privado", private=True, active=True)
            chat.subscribers.add(item)
            chat.subscribers.add(user)
            chat.save()
            chats.union(chat)
        except Exception as e:
            logger.error(str(e))
    return chats

# --
# Busca mensajes recibidos en la sala actual para enviarlos al usuario.
#  conn_id identifica a la conexion que realiza el mensaje
def check_for_messages(request, conn_id, user_cache):
    messages = None
    user = request.user
    last_connection = get_user_last_connection(user)
    room = last_connection.room
    if last_connection is None:
        room_obj = Room.objects.filter(pk=room).first()
        if room_obj:
            last_connection = LastConnection.objects.create(user=user, room=room_obj)

    # comprobamos que la conexion no haya  cambiado
    if conn_id == user_cache.get_conn_id():
        messages = Message.objects.filter(room__pk=room.pk, creation_date__gt=last_connection.date, deleted=False).select_related("user").exclude(user=request.user).order_by("pk")
        if messages.count() > 0:
            set_connection(user, room)
            return messages_to_dic(messages)

    return None

# ---
# Generar una cadena con formato compatible con sse
def set_data_string(event, datas, delay=None):
    output = '\nevent: %s\n' % event.replace("\n", SECURE_EOL_CHAR)  # se eliminan los fin de lineas de la entrada
    output += 'data: %s' % datas.replace("\n", SECURE_EOL_CHAR)

    if delay and isinstance(delay, int):
        output += "\nretry: %s" % delay

    return output
# ---
# Finalizar cadena SSE para su envío
def send_data(string):
    return "%s \n\n" % string

# El dispatcher es el generador encargado de escuchar la cache e informar de vuelta al usuario (este metodo es llamado ppor httpstreamresponse en el views.py)
def dispatcher(req):
    user_cache = UserCache(req.user.pk)
    conn_id = random_string(10)
    user_cache.set_conn_id(conn_id)
    # Mientras la conexion actual siga siendo la conexion activa
    # En cada interaccion comprobaremos si algun otro proceso ha modificado la cache, por si hubiera que cortar la conexion
    while (conn_id == user_cache.get_conn_id()):
        # print("session %s[%s] para el usuario %s" % (conn_id, req.session.get("conn_id", ""), req.user.username))

        time.sleep(INTERVAL_TIMEOUT)
        data = set_data_string("rooms_status", get_rooms_status_json(req.user))
        unread_messages = check_for_messages(req, conn_id, user_cache)
        if unread_messages:
            yield send_data(set_data_string("message", json.dumps(unread_messages)))
        yield send_data(data)
    # print("kill")
    yield send_data(set_data_string("kill", json.dumps({"msg": CONNECTION_KILL})))


"""
    Setters : Feed
    Metodos encargados de modificar la base de datos y la caché
"""

# --
# Actualiza la ultima conexion del usuario a la sala.
def set_connection(user, room):
    con = get_or_create(LastConnection, {'room': room, 'user': user})
    con.set_to_now()


# --
# Marca los mensajes como leidos. Si se indica limit_pk marca todos los mensajes hasta dicho pk
def mark_as_readed(room, user, limit_pk=None):
    unreaded_messages = Message.objects.filter(room=room).exclude(readed_by=user)
    if limit_pk:
        unreaded_messages = unreaded_messages.filter(pk__lte=limit_pk)
    for um in unreaded_messages:
        um.readed_by.add(user)
        um.save()

    return


# --
# Este método actualiza la información de la caché cuando un usuario envía un mensaje
def message_receiver_task(request, resp_queue):
    context = {}
    context = get_session_feedback(context, request)
    messages = []
    status_code = STATUS_CODE_TIMEOUT
    if context.get("success", None):
        status_code = STATUS_CODE_SUCCESS
        messages = Message.objects.filter(pk=context.get("form_data").get("pk"))
        if messages.count() > 0:
            msg = messages.first()
            msg.save()
            messages = messages_to_dic([msg])
        if context.get("error", None):
            status_code = STATUS_CODE_ERROR

    resp_queue.put({'status': status_code, 'messages': messages, 'room': "inserted", 'message_identifier': context.get("form_data").get("message_identifier")})
