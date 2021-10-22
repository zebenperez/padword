#!/usr/bin/python
# -*- coding: utf-8 -*-
# import collections
import logging
import random
import string

from django.core.cache import caches

logger = logging.getLogger(__name__)

"""
    Esta clase representa la instacia de la caché de un usuario conectado al chat
"""
CACHE2 = caches['level2']
CACHE1 = caches['default']
CACHE2.clear()
CACHE1.clear()

TIMEOUT = None

def clear_all_cache():
    CACHE1.clear()
    CACHE1.clear()

# ---------------------------
# BaseCache : Crea una clase que permite escribir y recuperar datos de los diferentes niveles de caché
# ---------------------------
class BaseCache():

    def __init__(self, cache_key, initial=None):
        self._key = "_%s_" % cache_key
        # self._id = self.__generate_id
        initial = initial if initial else {"__key__": self._key}
        CACHE1.get_or_set(self._key, initial, TIMEOUT)
        CACHE2.get_or_set(self._key, initial, TIMEOUT)

    def __generate_id(self):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for i in range(20))

    # Establece un valor en la cache pasada como parametro
    def __set(self, cache, key, value):
        try:
            cache_obj = cache.get(self._key)
            cache_obj[key] = value
            cache.set(self._key, cache_obj, TIMEOUT)
            return True
        except Exception as e:
            logger.error(str(e))

        return False

    # Devuelve el valor correspondiente a la clave en la cache pasada como parametro
    def __get(self, cache, key, default=None):
        try:
            cache_obj = cache.get(self._key)
            return cache_obj.get(key, default)
        except Exception as e:
            logger.error(str(e))

        return default

    def __clear(self):
        CACHE1.delete(self._key)
        CACHE2.delete(self._key)

    # Establece un valor en la cache de nivel 1
    def set_l1(self, key, value):
        return self.__set(CACHE1, key, value)

    # Establece un valor en la cache de nivel2
    def set_l2(self, key, value):
        return self.__set(CACHE2, key, value)

    # recupera el valor pasado de la cache de nivel 1
    def get_l1(self, key, default=None):
        return self.__get(CACHE1, key, default)

    # recupera el valor pasado de la cache de nivel 2
    def get_l2(self, key, default=None):
        return self.__get(CACHE2, key, default)

    # recupera las claves almacenadas en la cache
    def __keys(self, cache):
        try:
            return cache.get(self._pk).keys()
        except Exception as e:
            logger.error(str(e))
        return []

    # Claves para la cache de nivel 1
    def l1_keys(self):
        return self.__keys(self, CACHE1)

    # Claves para la cache de nivel 2
    def l2_keys(self):
        return self.__keys(self, CACHE2)

    def clear(self):
        self.__clear()


# ---------------------------
# UserCache: Almacena datos de uso frecuente del usuario
# ---------------------------
class UserCache(BaseCache):
    # ROOM_TUPLE = collections.namedtuple("Room", "pk private")
    CONN_ID_KEY = "__connection_id__"
    ROOM_KEY = "__room_code__"
    LAST_NOT_KEY = "__last_not_id__"
    LAST_CONN_KEY = "__last_connection_id__"
    SUBSCRIPTIONS_KEY = "__user_rooms__"

    def __init__(self, user_pk):
        self._user = user_pk
        super(UserCache, self).__init__(self._user)

    def get_pk(self):
        return self._user

    # Gestionar el identificador de la conexión para la cache de nivel 1
    def set_conn_id(self, value):
        return self.set_l1(UserCache.CONN_ID_KEY, value)

    def get_conn_id(self):
        return self.get_l1(UserCache.CONN_ID_KEY)

    # TODO: El usuario se tiene que suscribir a esta sala en la caché para recibir notificaciones.
    def set_room(self, room):
        return self.set_l1(UserCache.ROOM_KEY, room)

    def get_room(self):
        return self.get_l1(UserCache.ROOM_KEY)

    def set_last_connection(self, last_connection):
        self.set_l1(UserCache.LAST_CONN_KEY, last_connection)

    def get_last_connection(self):
        return self.get_l1(UserCache.LAST_CONN_KEY)

    def get_subscriptions(self):
        return self.get_l1(UserCache.SUBSCRIPTIONS_KEY, dict())

    def set_subscription(self, room_dict):
        subscriptions = self.get_subscriptions()
        key = room_dict.get("pk")
        subscriptions[key] = room_dict
        self.set_l1(UserCache.SUBSCRIPTIONS_KEY, subscriptions)
        return True

    def rm_susbscription(self, room):
        subscriptions = self.get_subscriptions()
        try:
            del subscriptions[str(room.pk)]
            self.set_l1(UserCache.SUBSCRIPTIONS_KEY, subscriptions)
            return True
        except Exception as e:
            logger.error(str(e))

        return False

    # Gestionar objetos en la cache de nivel 2
    def set(self, key, obj):
        return self.set_l2(key, obj)

    def get(self, key):
        return self.get_l2(key)

# ---------------------------
# RoomsCache : Almacena en cache los datos de las salas y el momento en el que se recibió el ultimo mensaje
# ---------------------------

class RoomCache(BaseCache):

    SUBSCRIBERS_KEY = "__subscribers__"
    LAST_MESSAGE_KEY = "__last_message__"
    LAST_CONNECTIONS_KEY = "__last_connections__"

    def __init__(self, room_pk):
        self._pk = room_pk
        super(RoomCache, self).__init__(self._pk)

    def set_subscribers(self, room):
        subscribers = [item.pk for item in room.subscribers.all()]
        self.set_l1(RoomCache.SUBSCRIBERS_KEY, subscribers)

    def get_subscribers(self):
        return self.get_l1(RoomCache.SUBSCRIBERS_KEY, [])

    def set_last_message(self, message):
        self.set_l1(RoomCache.LAST_MESSAGE_KEY, message)

    def get_last_message(self):
        return self.get_l1(RoomCache.LAST_MESSAGE_KEY)

    def get_last_connections(self):
        return self.get_l1(RoomCache.LAST_CONNECTIONS_KEY, {})

    def set_user_last_connection(self, last_connection):
        connections = self.get_last_connections()
        connections[last_connection.user.pk] = last_connection
        self.set_l1(RoomCache.LAST_CONNECTIONS_KEY, connections)

    def get_user_last_connection(self, user_pk):
        connections = self.get_last_connections()
        return connections.get(user_pk, None)
