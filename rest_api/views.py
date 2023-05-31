from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.urls import reverse

from .models_serializers import GuestSerializer, LockSerializer, RoomSerializer

from guest.models import Guest
from bookings.models import GuestUser
from web.models import ProjectUser, Lock, Room
from web.lock_lib import get_record_type
from padword.commons import new_ui_slug, reverse_cardkey, timestamp_to_date

from datetime import datetime

import logging
logger = logging.getLogger(__name__)


class GuestViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    #queryset = Guest.objects.all()
    queryset = Guest.objects.none()
    serializer_class = GuestSerializer
    permission_classes = [IsAuthenticated,]

    def serialize_guest(self, item):
        if item != None:
            return Response(GuestSerializer(item, many=False).data)
        return Response({"error": True})

    def get_queryset(self):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            logger.info("[{}]: \"Guest list\"".format(self.request.user))
            return Guest.objects.filter(project_id=pu.project_uuid)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Guest.objects.none()

    def create(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            data = {
                "UUID": new_ui_slug(Guest),
                "name": request.POST.get('name', ""),
                "surname": request.POST.get('surname', ""),
                "language": request.POST.get('language', ""),
                "mobile": request.POST.get('mobile', ""),
                "email": request.POST.get('email', ""),
                "room": request.POST.get('room', ""),
                "ext_id": request.POST.get('ext_id', ""),
                "check_in": datetime.strptime(request.POST.get('check_in', ""), "%Y-%m-%d %H:%M"),
                "check_out": datetime.strptime(request.POST.get('check_out', ""), "%Y-%m-%d %H:%M"),
                "project_id": pu.project_uuid,
            }
            #print(data)

            if len(data["mobile"]) < 9:
                msg = "Mobile is required and must be at least 9 characters long!"
                logger.error("[{}]: \"{}\"".format(self.request.user, msg))
                return Response(data={'error': 'true', 'msg': msg}, status=status.HTTP_400_BAD_REQUEST)

            serializer = self.serializer_class(data=data)
            if serializer.is_valid():
                #serializer.save()
                guest = Guest.objects.create(**data)
                guest.add_all_key_code()
                logger.info("[{}]: \"Guest {} {} created\"".format(self.request.user, guest.name, guest.surname))
                return Response(data=self.serializer_class(guest).data, status=status.HTTP_201_CREATED)
            else:
                logger.error("[{}]: \"Bad request!\"".format(self.request.user))
                return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response(data={'error': 'true', 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        try:
            guest = Guest.objects.get(UUID=pk)
            logger.info("[{}]: \"Guest {} {} retrieved\"".format(self.request.user, guest.name, guest.surname))
            return Response(self.serializer_class(guest).data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response(data={'error': 'true', 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            guest = Guest.objects.get(UUID=pk)
            guest_name = "{} {}".format(guest.name, guest.surname)
            GuestUser.delete_by_guest(guest.UUID)
            guest.delete_all()
            #guest.delete_soft()
            logger.info("[{}]: \"Guest {} destroyed\"".format(self.request.user, guest_name))
            return Response(data={'error': 'false'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response(data={'error': 'true', 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        try:
            guest = Guest.objects.get(UUID=pk)
            update_dates = False
            data = {}
            if "name" in request.POST:
                guest.name = request.POST["name"]
            if "surname" in request.POST:
                guest.surname = request.POST["surname"]
            if "language" in request.POST:
                guest.language = request.POST["language"]
            if "mobile" in request.POST:
                if len(request.POST["mobile"]) < 9:
                    msg = "Mobile is required and must be at least 9 characters long!"
                    logger.error("[{}]: \"{}\"".format(self.request.user, msg))
                    return Response(data={'error': 'true', 'msg': msg}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    guest.mobile = request.POST["mobile"]
            if "email" in request.POST:
                guest.email = request.POST["email"]
            if "ext_id" in request.POST:
                guest.ext_id = request.POST["ext_id"]
            if "check_in" in request.POST:
                guest.check_in = datetime.strptime(request.POST["check_in"], "%Y-%m-%d %H:%M")
                update_dates = True
            if "check_out" in request.POST:
                guest.check_out = datetime.strptime(request.POST["check_out"], "%Y-%m-%d %H:%M")
                update_dates = True
            if "room" in request.POST and request.POST["room"] != guest.room:
                guest.change_room(request.POST["room"])
            guest.save()
            if update_dates:
                guest.change_all_key_code_date()
                guest.change_all_key_card_date()
                #guest.remove_all_key_cards()
 
            logger.info("[{}]: \"Guest {} {} updated\"".format(self.request.user, guest.name, guest.surname))
            return Response(self.serializer_class(guest).data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response(data={'error': 'true', 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        #response = {'message': 'Update function is not offered in this path.'}
        #return Response(response, status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request, pk=None):
        logger.error("[{}]: \"Partial update function is not offered in this path.\"".format(self.request.user))
        response = {'message': 'Update function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=['get'])
    def get_locks(self, request):
        try:
            guest = Guest.objects.get(UUID = request.GET["UUID"])
            logger.info("[{}]: \"Get locks of guest {} {}\"".format(self.request.user, guest.name, guest.surname))
            return Response(guest.get_locks_json(), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": 'true', 'msg': str(e)})

    @action(detail=False, methods=['post'])
    def add_card(self, request):
        try:
            guest_uuid = request.POST["UUID"]
            code = reverse_cardkey(request.POST["card"])
            guest = Guest.objects.get(UUID=guest_uuid)
            guest.add_all_key_card(code)
            logger.info("[{}]: \"Added card to guest {} {}\"".format(self.request.user, guest.name, guest.surname))
            return Response(guest.get_locks_json(), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': str(e)})

    @action(detail=False, methods=['post'])
    def remove_card(self, request):
        try:
            guest_uuid = request.POST["UUID"]
            code = reverse_cardkey(request.POST["card"])
            guest = Guest.objects.get(UUID=guest_uuid)
            guest.remove_all_key_cards(code)
            logger.info("[{}]: \"Removed card of guest {} {}\"".format(self.request.user, guest.name, guest.surname))
            return Response(guest.get_locks_json(), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': str(e)})

    @action(detail=False, methods=['get'])
    def get_pwa_url(self, request):
        try:
            guest_uuid = request.GET["UUID"]
            guest = Guest.objects.get(UUID=guest_uuid)
            logger.info("[{}]: \"Get PWA url of guest {} {}\"".format(self.request.user, guest.name, guest.surname))
            pwa_url = request.build_absolute_uri(reverse("guest-access-auto", kwargs = {'guest_uuid': guest.UUID}))
            return Response({'link': '{}'.format(pwa_url)}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': str(e)})

    @action(detail=False, methods=['get'])
    def get_guest_by_ext_id(self, request):
        try:
            guest_ext_id = request.GET["ext_id"]
            guest = Guest.objects.filter(ext_id = guest_ext_id).first()
            if guest == None:
                logger.error("[{}]: \"Guest not found! - ext_id: {}\"".format(self.request.user, guest_ext_id))
                return Response({"error": True, 'msg': 'Guest not found!'})
            logger.info("[{}]: \"Get guest {} {} by ext_id {}\"".format(self.request.user, guest.name, guest.surname, guest_ext_id))
            return Response(self.serializer_class(guest).data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': str(e)})

    @action(detail=False, methods=['get'])
    def get_locks_by_ext_id(self, request):
        try:
            guest_ext_id = request.GET["ext_id"]
            guest = Guest.objects.filter(ext_id = guest_ext_id).first()
            if guest == None:
                logger.error("[{}]: \"Guest not found!\"".format(self.request.user))
                return Response({"error": True, 'msg': 'Guest not found!'})
            logger.info("[{}]: \"Get locks of guest {} {}\"".format(self.request.user, guest.name, guest.surname))
            return Response(guest.get_locks_json(), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": 'true', 'msg': str(e)})


class LockViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Lock.objects.none()
    serializer_class = LockSerializer
    permission_classes = [IsAuthenticated,]

    def serialize_lock(self, item):
        if item != None:
            return Response(LockSerializer(item, many=False).data)
        return Response({"error": True})

    def get_queryset(self):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            logger.info("[{}]: \"Lock list\"".format(self.request.user))
            return Lock.objects.filter(project_uuid=pu.project_uuid)
        except:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Lock.objects.none()

    def create(self, request):
        logger.error("[{}]: \"Create function is not offered in this path.\"".format(self.request.user))
        response = {'message': 'Create function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def retrieve(self, request, pk=None):
        logger.error("[{}]: \"Retrieve function is not offered in this path.\"".format(self.request.user))
        response = {'message': 'Retrieve function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, pk=None):
        logger.error("[{}]: \"Destroy function is not offered in this path.\"".format(self.request.user))
        response = {'message': 'Destroy function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, pk=None):
        logger.error("[{}]: \"Update function is not offered in this path.\"".format(self.request.user))
        response = {'message': 'Update function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request, pk=None):
        logger.error("[{}]: \"Partial update function is not offered in this path.\"".format(self.request.user))
        response = {'message': 'Update function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=['get'])
    def get_passcodes(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            lock_list = Lock.objects.filter(uuid = request.GET["uuid"], project_uuid=pu.project_uuid)
            for l in lock_list:
                print("{} {}".format(l.project_uuid, l.uuid))
            lock = Lock.objects.get(uuid = request.GET["uuid"], project_uuid = pu.project_uuid)
            code_list = lock.get_all_passcodes()
            c_list = []
            for c in code_list:
                dic = {"uuid":c["lockId"],"code_id":c["keyboardPwdId"],"startDate":c["startDate"],"endDate":c["endDate"],"type":c["keyboardPwdType"],"passcode":c["keyboardPwd"]}
                c_list.append(dic)
            logger.info("[{}]: \"Get passcode of lock {}\"".format(self.request.user, lock.uuid))
            return Response(c_list, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": 'true', 'msg': str(e)})

    @action(detail=False, methods=['post'])
    def add_passcode(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            lock_uuid = request.POST["uuid"]
            code = request.POST["code"]
            start_date = datetime.strptime(request.POST.get('start_date', ""), "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(request.POST.get('end_date', ""), "%Y-%m-%d %H:%M")
            lock = Lock.objects.get(uuid=lock_uuid, project_uuid=pu.project_uuid)
            err = lock.set_code(code, start_date, end_date)
            if "Error" in str(err):
                logger.error("[{}]: \"{}\"".format(self.request.user, str(err)))
                return Response({"error": True, "msg": str(err)})
            else:
                logger.info("[{}]: \"Added passcode to lock {}\"".format(self.request.user, lock_uuid))
                return Response({"error": False, "code_id": err, "msg": "Code added successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': str(e)})

    @action(detail=False, methods=['post'])
    def change_passcode(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            lock_uuid = request.POST["uuid"]
            code_id = request.POST["code_id"]
            code = request.POST["code"]
            start_date = datetime.strptime(request.POST.get('start_date', ""), "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(request.POST.get('end_date', ""), "%Y-%m-%d %H:%M")
            lock = Lock.objects.get(uuid=lock_uuid, project_uuid=pu.project_uuid)
            err = lock.change_code(code_id, code, start_date, end_date)
            if "Error" in str(err):
                logger.error("[{}]: \"{}\"".format(self.request.user, str(err)))
                return Response({"error": True, "msg": str(err)})
            else:
                logger.info("[{}]: \"Changed passcode to lock {}\"".format(self.request.user, lock_uuid))
                return Response({"error": False, "msg": "Code changed successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': str(e)})

    @action(detail=False, methods=['post'])
    def remove_passcode(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            lock_uuid = request.POST["uuid"]
            code_id = request.POST["code_id"]
            lock = Lock.objects.get(uuid=lock_uuid, project_uuid=pu.project_uuid)
            err = lock.remove_code(code_id)
            if "Error" in str(err):
                logger.error("[{}]: \"{}\"".format(self.request.user, str(err)))
                return Response({"error": True, "msg": str(err)})
            else:
                logger.info("[{}]: \"Removed passcode to lock {}\"".format(self.request.user, lock_uuid))
                return Response({"error": False, "msg": "Code removed successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': str(e)})


    @action(detail=False, methods=['get'])
    def get_cardcodes(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            lock = Lock.objects.get(uuid = request.GET["uuid"], project_uuid = pu.project_uuid)
            code_list = lock.get_all_cards()
            c_list = []
            for c in code_list:
                dic = {"uuid":c["lockId"],"code_id":c["cardId"],"startDate":c["startDate"],"endDate":c["endDate"],"cardcode":c["cardNumber"]}
                c_list.append(dic)
            logger.info("[{}]: \"Get card code of lock {}\"".format(self.request.user, lock.uuid))
            return Response(c_list, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": 'true', 'msg': str(e)})

    @action(detail=False, methods=['post'])
    def add_cardcode(self, request):
        try:
            #logger.info("[{}]: \"{}\"".format(self.request.user, request.POST))
            pu = ProjectUser.objects.get(username=self.request.user.username)
            lock_uuid = request.POST["uuid"]
            code = reverse_cardkey(request.POST["code"])
            start_date = datetime.strptime(request.POST.get('start_date', ""), "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(request.POST.get('end_date', ""), "%Y-%m-%d %H:%M")
            #lock = Lock.objects.get(uuid=lock_uuid)
            #lock_list = Lock.objects.filter(uuid=lock_uuid, project_uuid=pu.project_uuid)
            #for l in lock_list:
            #    logger.info("[{}]: \"{} {} {}\"".format(self.request.user, l.uuid, l.alias, l.project_uuid))
            #lock = Lock.objects.filter(uuid=lock_uuid, project_uuid=pu.project_uuid).first()
            lock = Lock.objects.get(uuid=lock_uuid, project_uuid=pu.project_uuid)

            err = lock.add_card(code, start_date, end_date)
            if "Error" in str(err):
                logger.error("[{}]: \"{}\"".format(self.request.user, str(err)))
                return Response({"error": True, "msg": str(err)})
            else:
                logger.info("[{}]: \"Add cardcode to lock {}\"".format(self.request.user, lock_uuid))
                return Response({"error": False, "code_id": err, "msg": "Card added successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': str(e)})

    @action(detail=False, methods=['post'])
    def remove_cardcode(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            lock_uuid = request.POST["uuid"]
            code_id = request.POST["code_id"]
            lock = Lock.objects.get(uuid=lock_uuid, project_uuid=pu.project_uuid)
            err = lock.remove_card(code_id)
            if "Error" in str(err):
                logger.error("[{}]: \"{}\"".format(self.request.user, str(err)))
                return Response({"error": True, "msg": str(err)})
            else:
                logger.info("[{}]: \"Remove cardcode of lock {}\"".format(self.request.user, lock_uuid))
                return Response({"error": False, "msg": "Card removed successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': str(e)})

    @action(detail=False, methods=['post'])
    def change_period_card(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            lock_uuid = request.POST["uuid"]
            code_id = request.POST["code_id"]
            start_date = datetime.strptime(request.POST.get('start_date', ""), "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(request.POST.get('end_date', ""), "%Y-%m-%d %H:%M")
            lock = Lock.objects.get(uuid=lock_uuid, project_uuid=pu.project_uuid)
            err = lock.change_period_card(code_id, start_date, end_date)
            if "Error" in str(err):
                logger.error("[{}]: \"{}\"".format(self.request.user, str(err)))
                return Response({"error": True, "msg": str(err)})
            else:
                logger.info("[{}]: \"Change card period of lock {}\"".format(self.request.user, lock_uuid))
                return Response({"error": False, "msg": "Card added successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': str(e)})

    @action(detail=False, methods=['get'])
    def get_records(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            lock = Lock.objects.get(uuid = request.GET["uuid"], project_uuid=pu.project_uuid)
            code_list = lock.get_all_records()
            c_list = []
            for c in code_list:
                dic = {
                    "uuid": c["lockId"],
                    "type": get_record_type(c["recordType"]),
                    "success": "Yes" if c["success"] == 1 else "No",
                    "username": c["username"],
                    "code": c["keyboardPwd"],
                    "lock_date": timestamp_to_date(c["lockDate"]),
                    "server_date": timestamp_to_date(c["serverDate"])
                }
                c_list.append(dic)
            logger.info("[{}]: \"Get records of lock {}\"".format(self.request.user, lock.uuid))
            return Response(c_list, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": 'true', 'msg': str(e)})

    @action(detail=False, methods=['get'])
    def open_lock(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            lock = Lock.objects.get(uuid = request.GET["uuid"], project_uuid=pu.project_uuid)
            msg = lock.open_lock() 
            if msg == True:
                logger.info("[{}]: \"The lock {} is open\"".format(self.request.user, lock.uuid))
                return Response({"error": 'false', 'msg': 'The lock {} is open'.format(lock.uuid)}, status=status.HTTP_200_OK)
            logger.info("[{}]: \"The lock {} could not be opened\"".format(self.request.user, lock.uuid))
            return Response({"error": 'true', 'msg': 'The lock {} could not be opened'.format(lock.uuid)})
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": 'true', 'msg': str(e)})


class RoomViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Room.objects.none()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated,]

    def serialize_room(self, item):
        if item != None:
            return Response(RoomSerializer(item, many=False).data)
        return Response({"error": True})

    def get_queryset(self):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            logger.info("[{}]: \"Room list\"".format(self.request.user))
            return Room.objects.filter(project_uuid=pu.project_uuid)
        except:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Room.objects.none()

    def create(self, request):
        logger.error("[{}]: \"Create function is not offered in this path.\"".format(self.request.user))
        response = {'message': 'Create function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def retrieve(self, request, pk=None):
        logger.error("[{}]: \"Retrieve function is not offered in this path.\"".format(self.request.user))
        response = {'message': 'Retrieve function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, pk=None):
        logger.error("[{}]: \"Destroy function is not offered in this path.\"".format(self.request.user))
        response = {'message': 'Destroy function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, pk=None):
        logger.error("[{}]: \"Update function is not offered in this path.\"".format(self.request.user))
        response = {'message': 'Update function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request, pk=None):
        logger.error("[{}]: \"Partial update function is not offered in this path.\"".format(self.request.user))
        response = {'message': 'Update function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)


