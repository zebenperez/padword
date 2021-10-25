#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import logging
import queue
import threading
from django.contrib.auth.decorators import login_required
# from django.db.models import Q
from django.contrib.auth.models import User
from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import render  # , redirect, reverse
from django.views.decorators.csrf import csrf_exempt
# local-imprts
# from .feed import *
from .dispatcher import *
from .generic import *
from .utils import list_get, get_or_none_query, get_or_none  # , get_or_create#, random_string
from .models import Room, Message, messages_to_dic

# Create your views here.

logging.basicConfig(level=logging.ERROR, format=' %(asctime)s - %(levelname)s - [%(lineno)s] %(message)s')
logger = logging.getLogger(__name__)

'''
    CONSTANTS
'''

PAGE_SIZE = 15

'''
     VIEWS
'''
@login_required
def index(request):
    context = {}

    context['room'] = request.GET.get('code', getattr(get_last_room(request.user), "code", ""))
    context['rooms_list'] = get_rooms_status_json(request.user)
    return render(request, "chat/chat_base.html", context)

# #----
# #DEPRECATED: El menu lateral se dibuja con javascript ahora
# # Este metodo deberia devolver un listado de salas json
# #---
# @login_required
# def rooms_list(request):
#    context = {}
#    t1 = threading.Thread(target=set_user_rooms_cache, args=[request.user])
#    t1.start()

#    context['chats'] = get_or_create_private_chats(request.user)
#    context['rooms'] = Room.objects.filter(subscribers=request.user, active=True, private=False).order_by("code")
#    return render(request, "chat/sidebar_rooms.html", context)

@login_required
def chat_room_form(request):
    context = {}
    context = get_session_feedback(context, request)
    if context.get("success", None):
        room = get_or_none(Room, get_feedback_pk(context))
        if room:
            set_connection(request.user, room)
            context['room'] = room
    else:
        print(context)
    return render(request, "chat/chat_room_form.html", context)

@login_required
def chat_room(request, code):
    context = {}
    room = get_or_none_query(Room, {'code': code})
    # slice_size = None
    messages = Message.objects.filter(room=room, deleted=False).select_related()
    total_msgs = messages.count()
    first_room_message = messages.first() if total_msgs > 0 else {}  # primer mensaje de la sala
    last_room_message = messages.last() if total_msgs > 0 else {}  # ultimo mensaje de la sala.
    last_readed_message = messages.filter(readed_by=request.user).order_by("pk").last()

    if last_readed_message and last_readed_message.pk != messages.last().pk:
        unreaded = messages.filter(pk__gte=last_readed_message.pk).order_by("creation_date")
        if unreaded.count() > PAGE_SIZE:
            messages = unreaded
        else:
            messages = messages.order_by("-creation_date")[:PAGE_SIZE][::-1]
    else:
        messages = messages.order_by("-creation_date")[:PAGE_SIZE][::-1]
    # update_cache
    set_connection(request.user, room)

    context['last_readed_message'] = last_readed_message if last_readed_message != last_room_message else -1
    context['first_room_message'] = first_room_message
    context['last_room_message'] = last_room_message
    context['messages_first'] = list_get(messages, 0, "-1")  # primer mensaje de los que se van a mostrar enm pantalla
    context['messages_last'] = list_get(messages, -1, "-1")  # último mensaje de los que se van a mostrar en pantalla.
    context['messages'] = json.dumps(messages_to_dic(messages))
    context['room'] = room

    return render(request, "chat/chat_room.html", context)

@login_required
def message_image_form(request, code):
    context = {}
    room = get_or_none_query(Room, {'code': code})
    context['room'] = room
    return render(request, "chat/message_image_form.html", context)


@login_required
def room_subscribers_form(request, code):
    context = {}
    room = get_or_none_query(Room, {'code': code})
    # t1 = threading.Thread(target=update_subscribers_rooms, args=[room])
    # t1.start()
    context['room'] = room
    context['users'] = User.objects.filter(is_active=True).exclude(pk=room.owner.pk)
    context = get_session_feedback(context, request)
    print(context)
    if context.get('success', None):
        for user in room.subscribers.filter(is_active=True):
            get_or_create(LastConnection, {'user': user, 'room': room})

    return render(request, "chat/room_subscribers_form.html", context)

@login_required
def deactivate_room(request, code):
    room = get_or_none_query(Room, {'code': code})
    room.active = False
    room.save()
    
    return redirect("chat_index")


@csrf_exempt
def get_messages_page(request, code):
    messages = []
    status_code = STATUS_CODE_ERROR
    
    data = json.loads(request.body.decode("utf-8")) if request.body else None
    if data:
        limit_pk = data.get("pk", None)
        messages = Message.objects.filter(room__code=code, deleted=False)

        page_type = data.get("type", None)
        if page_type == "previous":
            messages = messages.filter(pk__lt=limit_pk).order_by("-creation_date", "-pk")
            messages = messages[:PAGE_SIZE][::-1]
        else:
            messages = messages.filter(pk__gt=limit_pk).order_by("creation_date", "pk")
            messages = messages[:PAGE_SIZE]

        status_code = STATUS_CODE_SUCCESS

    first_message = list_get(messages, 0, None)
    first_message = messages_to_dic([first_message])[0] if first_message else {"pk": "-1"}

    last_message = list_get(messages, -1, None)
    last_message = messages_to_dic([last_message])[0] if last_message else {"pk": "-1"}
    # print("enviando")
    # last_message = {'pk': "-1"}
    return JsonResponse({'status': status_code, "messages": messages_to_dic(messages), "first_message": first_message, "last_message": last_message})

# ---------------------------
# Dispatcher views
# ---------------------------
@login_required
def notification_dispatcher(request):
    return StreamingHttpResponse(dispatcher(request), content_type='text/event-stream')

# ---------------------------
# Feed view
# ---------------------------
@login_required
def message_receiver(request):
    try:
        # Esta tarea es importante que no sea interrumpida aunque se generen otras similares
        resp_queue = queue.Queue()
        t1 = threading.Thread(target=message_receiver_task, args=[request, resp_queue])
        t1.start()
        t1.join()
        response = JsonResponse(resp_queue.get())
        return response
    except Exception as e:
        return JsonResponse({'status': STATUS_CODE_ERROR, 'status_message': str(e)})

@login_required
@csrf_exempt
def reading_confirmation(request, code):
    # la vista recibirá una peticion POST - JSON con los ids de los mensajes recibidos
    # Los marcará como leidos y devolverá el mismo listado a la aplicación en el parametro datas
    error_message = ""
    status_code = STATUS_CODE_TIMEOUT
    pending = None
    datas = json.loads(request.body)
    if datas:
        room = get_or_none_query(Room, {'code': code})
        pending = sorted(datas.get('messages', []))
        if len(pending) > 0:
            last_readed_pk = pending[-1]
            if last_readed_pk:
                t = threading.Thread(target=mark_as_readed, args=[room, request.user, last_readed_pk])
                t.start()
                t.join()

    else:
        status_code = STATUS_CODE_ERROR
        error_message = "Bad Request"

    response = JsonResponse({'status': status_code, 'status_message': error_message, 'data': pending})
    return response
