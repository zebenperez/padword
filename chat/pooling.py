#!/usr/bin/python
#-*- coding: utf-8 -*- 
import queue
import time
import threading
from django.contrib.auth.decorators import login_required 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .single_threading import SingleThread as SThread, TH_FINISHED
from .generic import * 
from .utils import  get_or_none_query, get_or_create
from .models import *
from .views import SESSION_ROOM_KEY, PAGE_SIZE,  mark_as_readed, messages_to_dic
# Create your views here.

import logging 
logging.basicConfig(level=logging.INFO, format=' %(asctime)s ##> %(levelname)s -%(module)s.%(filename)s [%(lineno)s] %(message)s')
logger = logging.getLogger(__name__)


'''
CONSTANTS 
'''

STATUS_CODE_INTERRUPTED = -2
STATUS_CODE_TIMEOUT = -1
STATUS_CODE_SUCCESS = 0
STATUS_CODE_ERROR = 1

# determinar la duracion y las consultas del pooling
POOLING_ROUNDS = 8 #Consultas que se realizaran
WAIT_SECONDS = 3 #tiempo de espera entre consultas 
REST_TIME = WAIT_SECONDS / 2

DEFAULT_RESPONSE = JsonResponse({"status": STATUS_CODE_ERROR, 'status_message': "Bad Request"})

'''
Classes 
'''

#recupera los mensajes no leidos
def retrieve_messages_task(request, room, thread):
    code = room.code
    status_code = STATUS_CODE_TIMEOUT
    last_connection =get_or_create(LastConnection, {'user' : request.user, 'room': room})
    for i in range(1,POOLING_ROUNDS):
        if thread.is_running():
            messages = Message.objects.filter(room=room, creation_date__gt=last_connection.date, deleted=False).exclude(user=request.user).order_by("pk")
            if messages.count() > 0:
                last_connection.set_con_now() #set time to now with auto_now       
                return JsonResponse({"status": STATUS_CODE_SUCCESS,'messages': messages_to_dic(messages), 'room': code })
            time.sleep(WAIT_SECONDS)
    
    status_code = STATUS_CODE_TIMEOUT if thread.get_status() == TH_FINISHED else STATUS_CODE_INTERRUPTED
    msg = "interrupted" if status_code == STATUS_CODE_INTERRUPTED else "timeout"
    return JsonResponse({"status" : status_code, 'status_message': msg})


def get_messages_page(request, room, thread):
    code = room.code
    if request.method == "POST":
       limit_pk = request.POST.get("top_message", None)
       if limit_pk:
           messages = Message.objects.filter(room=room, pk__lt=limit_pk, deleted=False).order_by("-pk")
           if messages.count() > 0:
                
                messages = messages[:PAGE_SIZE][::-1]
                top_message = messages[0].pk
                return JsonResponse({'status': STATUS_CODE_SUCCESS, "messages": messages_to_dic(messages), 'room': code, 'top_message': top_message})

           return JsonResponse({'status': STATUS_CODE_SUCCESS, "messages": [], "room": code, 'top_message':limit_pk})
    return DEFAULT_RESPONSE


def retrieve_unread_messages_task(request, thread):
    error_message = ""
    status_code = STATUS_CODE_TIMEOUT
    datas = []

    total_unread = None
    if request.method=="POST":
        rooms = Room.objects.filter(active=True, subscribers=request.user)
        total_unread = 0
        current_room = request.session.get(SESSION_ROOM_KEY, None)  
        for item in rooms:
            if thread.is_running():
                unreaded_count = Message.objects.filter(room=item).exclude(readed_by=request.user).exclude(user=request.user).count()
                datas.append({'room': item.code, 'unreaded_messages': unreaded_count , "current_room": current_room})
                total_unread += unreaded_count
        status_code = STATUS_CODE_SUCCESS if thread.get_status() == TH_FINISHED else STATUS_CODE_INTERRUPTED
    else:
        status_code = STATUS_CODE_ERROR
        error_message = "Bad Request"    
    return JsonResponse({'status': status_code, 'status_message': error_message, 'datas':datas, 'unread_messages_count':total_unread})
   

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
           msg.readed_by.add(request.user)
           msg.save()
           messages = messages_to_dic([msg])
        #logger.info("messages %s"%messages)
        if context.get("error", None):
            status_code = STATUS_CODE_ERROR
    resp_queue.put(JsonResponse({'status': status_code, 'messages': messages , 'room':"inserted", 'message_identifier': context.get("form_data").get("message_identifier") }))





## REST-views
@login_required
def message_consumer(request, code):
    room = get_or_none_query(Room, {'code': code})
    if room:
        thread_group = "%s_room_data"%(request.user.username)
        t1 = SThread(thread_group, retrieve_messages_task, [request, room])     
        t1.start()
        t1.join()
        response = t1.get_result()
        return response if response else DEFAULT_RESPONSE
    else:
        return JsonResponse({'status': STATUS_CODE_ERROR, 'status_message': "No se ha encontrado la sala indicada"})


@login_required
def messages_page_load(request, code):
    room = get_or_none_query(Room, {'code': code})
    if room:
        thread_group = "%s_room_page_data"%(request.user.username)
        t1 = SThread(thread_group, get_messages_page, [request, room])     
        t1.start()
        t1.join()
        response = t1.get_result()
        return response if response else DEFAULT_RESPONSE
    else:
        return JsonResponse({'status': STATUS_CODE_ERROR, 'status_message': "No se ha encontrado la sala indicada"})


# Recupera si hay mensajes no leidos en las salas que no estamos conectados
@login_required
@csrf_exempt
def unreaded_messages_updater(request):
    try:
        thread_group="%s_unread_messages"%(request.user.username)
        t1 = SThread(thread_group, retrieve_unread_messages_task, [request])         
        t1.start()
        t1.join()
        response = t1.get_result()
        return response if response else DEFAULT_RESPONSE
    except Exception as e:
        return JsonResponse({'status': STATUS_CODE_ERROR, 'status_message': str(e)})


@login_required
def message_receiver(request):
    try:
        #Esta tarea es importante que no sea interrumpida aunque se generen otras similares
        resp_queue = queue.Queue()
        t1 = threading.Thread(target=message_receiver_task, args=[request, resp_queue])
        t1.start()
        t1.join()
        response = resp_queue.get()
        return response
    except Exception as e:
        return JsonResponse({'status': STATUS_CODE_ERROR, 'status_message': str(e)})



@login_required
@csrf_exempt
def reading_confirmation(request, code):
    error_message = ""
    status_code = STATUS_CODE_TIMEOUT
    if request.method == "POST":
        room = get_or_none_query(Room, {'code':code})
        last_readed_pk = request.POST.get('last_readed_id', None)
        if last_readed_pk :
            t = threading.Thread(target=mark_as_readed, args=[room, request.user, last_readed_pk])
            t.start()
       
    else:
        status_code = STATUS_CODE_ERROR
        error_message = "Bad Request"

    return JsonResponse({'status': status_code, 'status_message': error_message})

