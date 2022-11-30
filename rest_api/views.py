from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models_serializers import GuestSerializer, LockSerializer, RoomSerializer

from guest.models import Guest
from web.models import ProjectUser, Lock, Room
from padword.commons import new_ui_slug, reverse_cardkey 

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
            return Guest.objects.filter(project_id=pu.project_uuid)
        except:
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
                "check_in": datetime.strptime(request.POST.get('check_in', ""), "%Y-%m-%d %H:%M"),
                "check_out": datetime.strptime(request.POST.get('check_out', ""), "%Y-%m-%d %H:%M"),
                "project_id": pu.project_uuid,
            }
            #print(data)
            serializer = self.serializer_class(data=data)
            if serializer.is_valid():
                #serializer.save()
                guest = Guest.objects.create(**data)
                guest.add_all_key_code()
                return Response(data=serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(data={'error': 'true', 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        try:
            guest = Guest.objects.get(UUID=pk)
            return Response(self.serializer_class(guest).data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response(data={'error': 'true'}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            guest = Guest.objects.get(UUID=pk)
            guest.delete()
            return Response(data={'error': 'false'}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response(data={'error': 'true'}, status=status.HTTP_400_BAD_REQUEST)

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
                guest.mobile = request.POST["mobile"]
            if "email" in request.POST:
                guest.email = request.POST["email"]
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
                guest.remove_all_key_cards()
 
            return Response(self.serializer_class(guest).data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response(data={'error': 'true', 'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        #response = {'message': 'Update function is not offered in this path.'}
        #return Response(response, status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request, pk=None):
        response = {'message': 'Update function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=['get'])
    def get_locks(self, request):
        try:
            guest = Guest.objects.get(UUID = request.GET["UUID"])
            return Response(guest.get_locks_json(), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("(get_guest): %s" % e)
            return Response({"error": 'true'})

    @action(detail=False, methods=['post'])
    def add_card(self, request):
        try:
            guest_uuid = request.POST["UUID"]
            code = reverse_cardkey(request.POST["card"])
            guest = Guest.objects.get(UUID=guest_uuid)
            guest.add_all_key_card(code)
            return Response(guest.get_locks_json(), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("(get_guest): %s" % e)
            return Response({"error": True})

    @action(detail=False, methods=['post'])
    def remove_card(self, request):
        try:
            guest_uuid = request.POST["UUID"]
            code = reverse_cardkey(request.POST["card"])
            guest = Guest.objects.get(UUID=guest_uuid)
            guest.remove_all_key_cards(code)
            return Response(guest.get_locks_json(), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("(get_guest): %s" % e)
            return Response({"error": True})


class LockViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Lock.objects.none()
    serializer_class = LockSerializer
    permission_classes = [IsAuthenticated,]

    def serialize_guest(self, item):
        if item != None:
            return Response(LockSerializer(item, many=False).data)
        return Response({"error": True})

    def get_queryset(self):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            return Lock.objects.filter(project_uuid=pu.project_uuid)
        except:
            return Lock.objects.none()

    def create(self, request):
        response = {'message': 'Create function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def retrieve(self, request, pk=None):
        response = {'message': 'Retrieve function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, pk=None):
        response = {'message': 'Destroy function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, pk=None):
        response = {'message': 'Update function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request, pk=None):
        response = {'message': 'Update function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=['get'])
    def get_passcodes(self, request):
        try:
            lock = Lock.objects.get(uuid = request.GET["uuid"])
            code_list = lock.get_all_passcodes()
            c_list = []
            for c in code_list:
                dic = {"uuid":c["lockId"],"code_id":c["keyboardPwdId"],"startDate":c["startDate"],"endDate":c["endDate"],"type":c["keyboardPwdType"],"passcode":c["keyboardPwd"]}
                c_list.append(dic)
            return Response(c_list, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("(get_passcodes): %s" % e)
            return Response({"error": 'true'})

    @action(detail=False, methods=['post'])
    def add_passcode(self, request):
        try:
            lock_uuid = request.POST["uuid"]
            code = request.POST["code"]
            start_date = datetime.strptime(request.POST.get('start_date', ""), "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(request.POST.get('end_date', ""), "%Y-%m-%d %H:%M")
            lock = Lock.objects.get(uuid=lock_uuid)
            err = lock.set_code(code, start_date, end_date)
            if "Error" in str(err):
                return Response({"error": True, "msg": str(err)})
            else:
                return Response({"error": False, "msg": "Code added successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("(add_passcode): %s" % e)
            return Response({"error": True})

    @action(detail=False, methods=['post'])
    def change_passcode(self, request):
        try:
            lock_uuid = request.POST["uuid"]
            code_id = request.POST["code_id"]
            code = request.POST["code"]
            start_date = datetime.strptime(request.POST.get('start_date', ""), "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(request.POST.get('end_date', ""), "%Y-%m-%d %H:%M")
            lock = Lock.objects.get(uuid=lock_uuid)
            err = lock.change_code(code_id, code, start_date, end_date)
            if "Error" in str(err):
                return Response({"error": True, "msg": str(err)})
            else:
                return Response({"error": False, "msg": "Code changed successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("(add_passcode): %s" % e)
            return Response({"error": True})

    @action(detail=False, methods=['post'])
    def remove_passcode(self, request):
        try:
            lock_uuid = request.POST["uuid"]
            code_id = request.POST["code_id"]
            lock = Lock.objects.get(uuid=lock_uuid)
            err = lock.remove_code(code_id)
            if "Error" in str(err):
                return Response({"error": True, "msg": str(err)})
            else:
                return Response({"error": False, "msg": "Code removed successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("(remove_passcode): %s" % e)
            return Response({"error": True})


    @action(detail=False, methods=['get'])
    def get_cardcodes(self, request):
        try:
            lock = Lock.objects.get(uuid = request.GET["uuid"])
            code_list = lock.get_all_cards()
            c_list = []
            for c in code_list:
                dic = {"uuid":c["lockId"],"code_id":c["cardId"],"startDate":c["startDate"],"endDate":c["endDate"],"cardcode":c["cardNumber"]}
                c_list.append(dic)
            return Response(c_list, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("(get_cardcodes): %s" % e)
            return Response({"error": 'true'})

    @action(detail=False, methods=['post'])
    def add_cardcode(self, request):
        try:
            lock_uuid = request.POST["uuid"]
            code = reverse_cardkey(request.POST["code"])
            start_date = datetime.strptime(request.POST.get('start_date', ""), "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(request.POST.get('end_date', ""), "%Y-%m-%d %H:%M")
            lock = Lock.objects.get(uuid=lock_uuid)
            err = lock.add_card(code, start_date, end_date)
            if "Error" in str(err):
                return Response({"error": True, "msg": str(err)})
            else:
                return Response({"error": False, "msg": "Card added successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("(add_cardcode): %s" % e)
            return Response({"error": True})

    @action(detail=False, methods=['post'])
    def remove_cardcode(self, request):
        try:
            lock_uuid = request.POST["uuid"]
            code_id = request.POST["code_id"]
            lock = Lock.objects.get(uuid=lock_uuid)
            err = lock.remove_card(code_id)
            if "Error" in str(err):
                return Response({"error": True, "msg": str(err)})
            else:
                return Response({"error": False, "msg": "Card removed successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("(remove_cardcode): %s" % e)
            return Response({"error": True})

    @action(detail=False, methods=['post'])
    def change_period_card(self, request):
        try:
            lock_uuid = request.POST["uuid"]
            code_id = request.POST["code_id"]
            start_date = datetime.strptime(request.POST.get('start_date', ""), "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(request.POST.get('end_date', ""), "%Y-%m-%d %H:%M")
            lock = Lock.objects.get(uuid=lock_uuid)
            err = lock.change_period_card(code_id, start_date, end_date)
            if "Error" in str(err):
                return Response({"error": True, "msg": str(err)})
            else:
                return Response({"error": False, "msg": "Card added successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("(add_cardcode): %s" % e)
            return Response({"error": True})


class RoomViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Room.objects.none()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated,]

    def serialize_guest(self, item):
        if item != None:
            return Response(RoomSerializer(item, many=False).data)
        return Response({"error": True})

    def get_queryset(self):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            return Room.objects.filter(project_uuid=pu.project_uuid)
        except:
            return Room.objects.none()

    def create(self, request):
        response = {'message': 'Create function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def retrieve(self, request, pk=None):
        response = {'message': 'Retrieve function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, pk=None):
        response = {'message': 'Destroy function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, pk=None):
        response = {'message': 'Update function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request, pk=None):
        response = {'message': 'Update function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)


