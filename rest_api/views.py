from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.urls import reverse

from .models_serializers import GuestSerializer, LockSerializer, RoomSerializer, GuestCarSerializer, WristbandAccessSerializer

from guest.models import Guest, GuestCar, Regime, GuestRegime, GuestType
from guest.wristband_models import Wristband, WristbandAccess, WristbandAccessPoint, WristbandAccessZone, WristbandType
from bookings.models import GuestUser, Form
#from web.models import ProjectUser, Lock, Room
from web.models import ProjectUser, Room, ProjectLockUser
from web.models_lock import Lock, LockCodeExtId
from web.lock_lib import get_record_type
from sensibo.models import ProjectSensiboUser
from contents.models import PointOfSale
from connector.models import ProjectStripeUser, ProjectCarUser
from padword.commons import new_ui_slug, reverse_cardkey, timestamp_to_date, get_float, get_int, get_or_none
from padword.commons import get_today_ini, get_today_end
from connector.libstripe import ShStripe

from datetime import datetime, timedelta

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
            return Guest.objects.filter(project_id=pu.project_uuid, deleted=False)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Guest.objects.none()

    def create(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            data = {
                "UUID": new_ui_slug(Guest, "UUID"),
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
            lock_code = request.POST.get("lock_code", "")
            plates = request.POST.get("plates", "")
            regime = request.POST.get("regime", "")   

            if len(data["mobile"]) < 9 and lock_code == "":
                msg = "Mobile is required and must be at least 9 characters long!"
                logger.error("[{}]: \"{}\"".format(self.request.user, msg))
                return Response(data={'error': 'true', 'msg': msg}, status=status.HTTP_400_BAD_REQUEST)

            serializer = self.serializer_class(data=data)
            if serializer.is_valid():
                guest = Guest.objects.create(**data)
                logger.info("[{}]: \"Guest {} {} created\"".format(self.request.user, guest.name, guest.surname))

                guest_data = self.serializer_class(guest).data
                lock_code_err = guest.add_all_key_code() if lock_code == "" else guest.add_all_key_code(lock_code)
                guest_data["lock_code_err"] = lock_code_err if "error" in lock_code_err.lower() else "" 
                guest_data["lock_code"] = guest.lock_code 

                #Gestión de matrículas
                guest.add_plates(plates)

                #Gestión de régimen
                guest.update_regime(regime)

                logger.info("[{}]: \"Guest key codes {} {} created\"".format(self.request.user, guest.name, guest.surname))
                return Response(data=guest_data, status=status.HTTP_201_CREATED)
            else:
                logger.error("[{}]: \"Bad request!\"".format(self.request.user))
                return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response(data={'error': 'true', 'msg': "Bad request!"}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        try:
            guest = Guest.objects.get(UUID=pk)
            logger.info("[{}]: \"Guest {} {} retrieved\"".format(self.request.user, guest.name, guest.surname))
            return Response(self.serializer_class(guest).data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response(data={'error': 'true', 'msg': "Bad request!"}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response(data={'error': 'true', 'msg': 'Bad request!'}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        try:
            guest = Guest.objects.get(UUID=pk)
            update_dates = False
            update_codes = False
            data = {}
            if "name" in request.POST:
                guest.name = request.POST["name"]
            if "surname" in request.POST:
                guest.surname = request.POST["surname"]
            if "language" in request.POST:
                guest.language = request.POST["language"]
            if "mobile" in request.POST and request.POST["mobile"] != guest.mobile:
                if len(request.POST["mobile"]) < 9:
                    msg = "Mobile is required and must be at least 9 characters long!"
                    logger.error("[{}]: \"{}\"".format(self.request.user, msg))
                    return Response(data={'error': 'true', 'msg': msg}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    guest.mobile = request.POST["mobile"]
                    update_codes = True
            if "email" in request.POST:
                guest.email = request.POST["email"]
            if "ext_id" in request.POST:
                guest.ext_id = request.POST["ext_id"]
            if "check_in" in request.POST and request.POST["check_in"] != datetime.strftime(guest.check_in, "%Y-%m-%d %H:%M"):
                guest.check_in = datetime.strptime(request.POST["check_in"], "%Y-%m-%d %H:%M")
                update_dates = True
            if "check_out" in request.POST and request.POST["check_out"] != datetime.strftime(guest.check_out, "%Y-%m-%d %H:%M"):
                guest.check_out = datetime.strptime(request.POST["check_out"], "%Y-%m-%d %H:%M")
                update_dates = True
            if "room" in request.POST and request.POST["room"] != guest.room:
                guest.change_room(request.POST["room"])
                #guest.change_sensibo_devices(request.POST["room"])
            guest.save()

            #Gestión de matrículas
            if "plates" in request.POST:
                guest.add_plates(request.POST["plates"])
 
            #Gestión de matrículas
            if "regime" in request.POST:
                guest.update_regime(request.POST["regime"])

            guest_data = self.serializer_class(guest).data
            codes_err = ""
            if update_dates:
                lock_card_err = guest.change_all_key_card_date()
                lock_code_err = guest.change_all_key_code_date()
                guest_data["lock_card_err"] = lock_card_err if "error" in lock_card_err.lower() else ""
                guest_data["lock_code_err"] = lock_code_err if "error" in lock_code_err.lower() else ""
                codes_err = guest_data["lock_code_err"]

            log_str = "[{}]: \"Guest {} {} updated\"".format(self.request.user, guest.name, guest.surname)
            log_str += " (dates modified=\"{}\" - mobile modified=\"{}\" - code err=\"{}\")".format(update_dates, update_codes, codes_err)
            log_str += " <br/>(POST=\"{}\")".format(request.POST)
            logger.info(log_str)
            return Response(guest_data, status=status.HTTP_200_OK)
            #return Response(self.serializer_class(guest).data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response(data={'error': 'true', 'msg': 'Bad request!'}, status=status.HTTP_400_BAD_REQUEST)
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
            return Response({"error": 'true', 'msg': 'Bad request!'})

    @action(detail=False, methods=['post'])
    def update_lock_code(self, request):
        try:
            guest_uuid = request.POST["UUID"]
            code = request.POST["lock_code"]
            guest = Guest.objects.get(UUID=guest_uuid)
            codes_err = guest.change_all_key_code(code)

            if "Error" in codes_err:
                logger.error("[{}]: \"{}\"".format(self.request.user, codes_err))
                return Response(data={'error': 'true', 'msg': codes_err}, status=status.HTTP_400_BAD_REQUEST)

            logger.info("[{}]: \"Update code ({}) to guest {} {}\"".format(self.request.user, code, guest.name, guest.surname))
            return Response(guest.get_locks_passcode_json(), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': 'Bad request!'})

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
            return Response({"error": True, 'msg': 'Bad request!'})

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
            return Response({"error": True, 'msg': 'Bad request!'})

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
            return Response({"error": True, 'msg': 'Bad request!'})

    @action(detail=False, methods=['get'])
    def get_guest_by_ext_id(self, request):
        try:
            guest_ext_id = request.GET["ext_id"]
            guest = Guest.objects.filter(ext_id = guest_ext_id).first()
            if guest == None:
                logger.error("[{}]: \"Guest not found! - ext_id: {}\"".format(self.request.user, guest_ext_id))
                return Response({"error": True, 'msg': 'Guest not found!'})
            if guest.deleted:
                logger.error("[{}]: \"Guest deleted! - ext_id: {}\"".format(self.request.user, guest_ext_id))
                return Response({"error": True, 'msg': 'This guest is removed!'})
            logger.info("[{}]: \"Get guest {} {} by ext_id {}\"".format(self.request.user, guest.name, guest.surname, guest_ext_id))

            guest_data = self.serializer_class(guest).data
            #guest_data["lock_code"] = guest.lock_code 
            return Response(guest_data, status=status.HTTP_200_OK)
            #return Response(self.serializer_class(guest).data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': 'Bad request!'})

    @action(detail=False, methods=['get'])
    def get_all_guest_by_ext_id(self, request):
        try:
            guest_ext_id = request.GET["ext_id"]
            guest_list = Guest.objects.filter(ext_id = guest_ext_id)
            logger.info("[{}]: \"Get all guest by ext_id {}\"".format(self.request.user, guest_ext_id))
            return Response(GuestSerializer(guest_list, many=True).data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': 'Bad request!'})

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
            return Response({"error": 'true', 'msg': 'Bad request!'})

    @action(detail=False, methods=['post'])
    def add_credit(self, request):
        try:
            amount = get_float(request.POST["amount"])
            amount = get_int(round(amount, 2) * 100)
            code = reverse_cardkey(request.POST["card"])

            band = Wristband.objects.filter(code=code).first()
            if band == None:
                logger.error("[{}]: \"Band not found!\"".format(self.request.user))
                return Response({"error": True, 'msg': 'Band not found!'})
            guest = band.guest
            if not guest.have_valid_booking():
                logger.error("[{}]: \"Guest do not have a valid booking!\"".format(self.request.user))
                return Response({"error": True, 'msg': 'Guest do not have a valid booking!'})
            psu = ProjectStripeUser.objects.filter(project_uuid=guest.project_id).first()
            if psu is None:
                logger.error("[{}]: \"Api Key not found!\"".format(self.request.user))
                return Response({"error": True, 'msg': 'Api Key not found!'})

            guest_name = "{} {}".format(guest.name, guest.surname)
            gs = guest.stripe
            gc = guest.card

            st = ShStripe(psu.api_key)
            obj_id = st.create_stripe_payment_intent(gs.stripe_id, gs.payment_method, amount, gc.code, "eur")
            if obj_id == "" or obj_id == None:
                logger.error("[{}]: \"Payment error!\"".format(self.request.user))
                return Response({"error": True, 'msg': 'Payment error!'})

            logger.info("[{}]: \"Added credit to card {} of guest {}\"".format(self.request.user, code, guest_name))
            return Response({"error": False, "msg": "Credit added successfully to guest: {}!".format(guest_name)}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": 'true', 'msg': 'Bad request!'})

    @action(detail=False, methods=['post'])
    def create_with_band(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            name = request.POST.get("name", "")                 #req
            surname = request.POST.get("surname", "")           #opt
            band_code = request.POST.get("band_code", "")       #opt
            user_regime = request.POST.get("user_regime", "")   #req
            user_type = request.POST.get("user_type", "")       #opt
            check_out = request.POST.get('check_out', "")         #opt

            if pu == None or pu.project == None:
                logger.error("[{}]: \"Permission denied!\"".format(self.request.user))
                return Response({"error": True, 'msg': 'Permission denied!'})

            #if name == "" or band_code == "" or user_regime == "":
            if name == "" or user_regime == "":
                logger.error("[{}]: \"name and user_regime are required!\"".format(self.request.user))
                return Response({"error": True, 'msg': 'name, band_code and user_type are required!'})

            reg = Regime.objects.filter(code=user_regime).first()
            if reg == None:
                logger.error("[{}]: \"User regime not found!\"".format(self.request.user))
                return Response({"error": True, 'msg': 'User type not found!'})

            guest_type = ""
            if user_type != "":
                gt = GuestType.objects.filter(code=user_type).first()
                if gt == None:
                    logger.error("[{}]: \"User type not found!\"".format(self.request.user))
                    return Response({"error": True, 'msg': 'User type not found!'})
                guest_type = gt.uuid 

            c_out = datetime.strptime(check_out, "%Y-%m-%d %H:%M:%S") if check_out != "" else get_today_end()
            c_in = pu.project.local_date(datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
            data = { 
                "UUID": new_ui_slug(Guest, "UUID"), 
                "name": name, 
                "surname": surname, 
                "check_in": c_in,
                "check_out": c_out,
                "guest_type": guest_type,
                "project_id": pu.project_uuid, 
            }
            guest = Guest.objects.create(**data)
            logger.info("[{}]: \"Guest {} created\"".format(self.request.user, guest.name))

            gr, created = GuestRegime.objects.get_or_create(regime=reg, guest=guest)
            logger.info("[{}]: \"Guest Regime {} created\"".format(self.request.user, guest.name))

            if band_code != "":
                bt = WristbandType.objects.filter(code="03").first()
                datab = { "code": reverse_cardkey(band_code), "name": name, "guest": guest, "type": bt}
                band = Wristband.objects.create(**datab)
                logger.info("[{}]: \"Band {} created\"".format(self.request.user, guest.name))

            return Response(data={'error': 'false', 'msg': "Band added successfully!"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response(data={'error': 'true', 'msg': "Bad request!"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def close_bands(self, request):
        try:
            from guest.wristband_lib import close_band_by_regime_and_soft_remove

            pu = ProjectUser.objects.get(username=self.request.user.username)
            if pu == None or pu.project == None:
                logger.error("[{}]: \"Permission denied!\"".format(self.request.user))
                return Response({"error": True, 'msg': 'Permission denied!'})

            code = request.GET.get("code", "").replace("/", "")                 #req
            if code == "":
                logger.error("[{}]: \"Code field is required!\"".format(self.request.user))
                return Response({"error": True, 'msg': 'Code field is required!'})

            close_band_by_regime_and_soft_remove(pu.project, code)
            logger.info("[{}]: \"Bands {} closed\"".format(self.request.user, code))
            return Response(data={'error': 'false', 'msg': "Bands closed successfully!"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response(data={'error': 'true', 'msg': "Bad request!"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def bands_daily(self, request):
        try:
            from guest.wristband_lib import get_daily_close_bands
            date = request.POST.get('date', "")         #req
            print(date)

            pu = ProjectUser.objects.get(username=self.request.user.username)
            if pu == None or pu.project == None:
                logger.error("[{}]: \"Permission denied!\"".format(self.request.user))
                return Response({"error": True, 'msg': 'Permission denied!'})

            if date == "":
                logger.error("[{}]: \"Date field is required!\"".format(self.request.user))
                return Response({"error": True, 'msg': 'Date field is required!'})

            band_list = get_daily_close_bands(date)
            logger.info("[{}]: \"Bands {} daily\"".format(self.request.user, date))
            return Response(data={'band_list': band_list,}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response(data={'error': 'true', 'msg': "Bad request!"}, status=status.HTTP_400_BAD_REQUEST)


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
        except Exception as e:
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
            #lock_list = Lock.objects.filter(uuid = request.GET["uuid"], project_uuid=pu.project_uuid)
            #for l in lock_list:
            #    print("{} {}".format(l.project_uuid, l.uuid))
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
            return Response({"error": 'true', 'msg': 'Bad request!'})

    @action(detail=False, methods=['get'])
    def get_passcode_by_ext_id(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            ext_id = request.GET["ext_id"]
            lcei = LockCodeExtId.objects.filter(project_uuid=pu.project_uuid, ext_id=ext_id).first()
            if lcei == None:
                logger.error("[{}]: \"External code not found!\"".format(self.request.user))
                return Response({"error": True, "msg": "External code not found!"})
            lock = Lock.objects.get(uuid = lcei.lock_uuid, project_uuid = pu.project_uuid)
            code_list = lock.get_all_passcodes()
            c_list = []
            for c in code_list:
                if c["keyboardPwd"] == lcei.code:
                    dic = {"uuid":c["lockId"],"code_id":c["keyboardPwdId"],"startDate":c["startDate"],"endDate":c["endDate"],"type":c["keyboardPwdType"],"passcode":c["keyboardPwd"],"ext_id":ext_id}
                    c_list.append(dic)
            logger.info("[{}]: \"Get passcode of lock {}\"".format(self.request.user, lock.uuid))
            return Response(c_list, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": 'true', 'msg': 'Bad request!'})


    @action(detail=False, methods=['post'])
    def add_passcode(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            lock_uuid = request.POST["uuid"]
            code = request.POST["code"]
            name = request.POST["name"] if "name" in request.POST else ""
            start_date = datetime.strptime(request.POST.get('start_date', ""), "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(request.POST.get('end_date', ""), "%Y-%m-%d %H:%M")
            start_date_gmt = pu.project.gmt_date(start_date)
            end_date_gmt = pu.project.gmt_date(end_date)
            lock = Lock.objects.get(uuid=lock_uuid, project_uuid=pu.project_uuid)
            #err = lock.set_code(code, start_date, end_date, name)
            err = lock.set_code(code, start_date_gmt, end_date_gmt, name)

            if "ext_id" in request.POST:
                ext_id = request.POST["ext_id"]
                lcei, created = LockCodeExtId.objects.get_or_create(project_uuid=pu.project_uuid, lock_uuid=lock.uuid, code=code, ext_id=ext_id)

            if "Error" in str(err):
                logger.error("[{}]: \"{}\"".format(self.request.user, str(err)))
                return Response({"error": True, "msg": str(err)})
            else:
                logger.info("[{}]: \"Added passcode to lock {}\"".format(self.request.user, lock_uuid))
                return Response({"error": False, "code_id": err, "msg": "Code added successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': 'Bad request!'})

    @action(detail=False, methods=['post'])
    def change_passcode(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            lock_uuid = request.POST["uuid"]
            code_id = request.POST["code_id"]
            code = request.POST["code"]
            start_date = datetime.strptime(request.POST.get('start_date', ""), "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(request.POST.get('end_date', ""), "%Y-%m-%d %H:%M")
            start_date_gmt = pu.project.gmt_date(start_date)
            end_date_gmt = pu.project.gmt_date(end_date)
            lock = Lock.objects.get(uuid=lock_uuid, project_uuid=pu.project_uuid)
            #err = lock.change_code(code_id, code, start_date, end_date)
            err = lock.change_code(code_id, code, start_date_gmt, end_date_gmt)
            if "Error" in str(err):
                logger.error("[{}]: \"{}\"".format(self.request.user, str(err)))
                return Response({"error": True, "msg": str(err)})
            else:
                logger.info("[{}]: \"Changed passcode to lock {}\"".format(self.request.user, lock_uuid))
                return Response({"error": False, "msg": "Code changed successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': 'Bad request!'})

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
            return Response({"error": True, 'msg': 'Bad request!'})


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
            return Response({"error": 'true', 'msg': 'Bad request!'})

    @action(detail=False, methods=['post'])
    def add_cardcode(self, request):
        try:
            #logger.info("[{}]: \"{}\"".format(self.request.user, request.POST))
            pu = ProjectUser.objects.get(username=self.request.user.username)
            lock_uuid = request.POST["uuid"]
            code = reverse_cardkey(request.POST["code"])
            start_date = datetime.strptime(request.POST.get('start_date', ""), "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(request.POST.get('end_date', ""), "%Y-%m-%d %H:%M")
            start_date_gmt = pu.project.gmt_date(start_date)
            end_date_gmt = pu.project.gmt_date(end_date)
            #lock = Lock.objects.get(uuid=lock_uuid)
            #lock_list = Lock.objects.filter(uuid=lock_uuid, project_uuid=pu.project_uuid)
            #for l in lock_list:
            #    logger.info("[{}]: \"{} {} {}\"".format(self.request.user, l.uuid, l.alias, l.project_uuid))
            #lock = Lock.objects.filter(uuid=lock_uuid, project_uuid=pu.project_uuid).first()
            lock = Lock.objects.get(uuid=lock_uuid, project_uuid=pu.project_uuid)

            #err = lock.add_card(code, start_date, end_date)
            err = lock.add_card(code, start_date_gmt, end_date_gmt)
            if "Error" in str(err):
                logger.error("[{}]: \"{}\"".format(self.request.user, str(err)))
                return Response({"error": True, "msg": str(err)})
            else:
                logger.info("[{}]: \"Add cardcode to lock {}\"".format(self.request.user, lock_uuid))
                return Response({"error": False, "code_id": err, "msg": "Card added successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': 'Bad request!'})

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
            return Response({"error": True, 'msg': 'Bad request!'})

    @action(detail=False, methods=['post'])
    def change_period_card(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            lock_uuid = request.POST["uuid"]
            code_id = request.POST["code_id"]
            start_date = datetime.strptime(request.POST.get('start_date', ""), "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(request.POST.get('end_date', ""), "%Y-%m-%d %H:%M")
            start_date_gmt = pu.project.gmt_date(start_date)
            end_date_gmt = pu.project.gmt_date(end_date)
            lock = Lock.objects.get(uuid=lock_uuid, project_uuid=pu.project_uuid)
            #err = lock.change_period_card(code_id, start_date, end_date)
            err = lock.change_period_card(code_id, start_date_gmt, end_date_gmt)
            if "Error" in str(err):
                logger.error("[{}]: \"{}\"".format(self.request.user, str(err)))
                return Response({"error": True, "msg": str(err)})
            else:
                logger.info("[{}]: \"Change card period of lock {}\"".format(self.request.user, lock_uuid))
                return Response({"error": False, "msg": "Card added successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': 'Bad request!'})

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
            return Response({"error": 'true', 'msg': 'Bad request!'})

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
            return Response({"error": 'true', 'msg': 'Bad request!'})

    @action(detail=False, methods=['get'])
    def refresh_tokens(self, request):
        from django.utils import timezone
        try:
            if not request.user.groups.filter(name='admins').exists():
                logger.info("[{}]: Permission denied!".format(self.request.user))
                return Response( {"error": "true", "msg": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
    
            limit = timezone.now() - timedelta(days=30)
            item_list = ProjectLockUser.objects.filter(last_refresh__lte = limit, auto_refresh=True)
            result = []
            for item in item_list:
                item.get_new_token()
                result.append(item.project.name)

            logger.info("[{}]: Tokens have been updated!".format(self.request.user))
            return Response({"updated_projects": result}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": 'true', 'msg': 'Bad request!'})


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


class SensiboViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for listing or retrieving users.
    """
    def list(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            return Response(pu.project.sensibo_device_list())
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': 'Bad request!'})

    @action(detail=False, methods=['get'])
    def measurement(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            device_uid = request.GET["device_uid"]
            data_values = pu.project.sensibo_get_measurement(device_uid)
            data_values["error"] = "false"
            return Response(data_values)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': 'Bad request!'})

    @action(detail=False, methods=['get'])
    def measurement_history(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            device_uid = request.GET["device_uid"]
            data_values = pu.project.sensibo_get_measurement_history(device_uid)
            data_values["error"] = "false"
            return Response(data_values)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': 'Bad request!'})

    @action(detail=False, methods=['get'])
    def ac_state(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            device_uid = request.GET["device_uid"]
            data_values = pu.project.sensibo_get_ac_state(device_uid)
            data_values["error"] = "false"
            return Response(data_values)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': 'Bad request!'})

class TicketViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for listing or retrieving users.
    """
    @action(detail=False, methods=['POST'])
    def get_tickets(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            #pu = ProjectUser.objects.filter(username=self.request.user.username).first()
            start_date = request.POST["start_date"] if "start_date" in request.POST else ""
            end_date = request.POST["end_date"] if "end_date" in request.POST else ""
            start_id = request.POST["start_id"] if "start_id" in request.POST else ""
            status = request.POST["status"] if "status" in request.POST else "enviado"
            #if start_date != "":
            #    s_date = datetime.strptime(start_date, "%Y-%m-%d_%H:%M")
            #    e_date = datetime.strptime(end_date, "%Y-%m-%d_%H:%M") if end_date != "" else datetime.now()
            form = Form.objects.filter(form_type__code="tpv", form_type__project_uuid=pu.project.uuid).first()
            if form != None:
                return Response(form.to_tickets(start_id, start_date, end_date, status))
            return Response({"error": True, 'msg': 'This project do not have TPV configured!'})
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': 'Bad request!'})

    @action(detail=False, methods=['POST'])
    def get_tickets2(self, request):
        try:
            logger.info("[DEBUG]: ({}) ENTRANDO EN GET TICKETS2: {}".format(request.META.get('REMOTE_ADDR'), request.POST))
            pu = ProjectUser.objects.get(username=self.request.user.username)
            start_date = request.POST["start_date"] if "start_date" in request.POST else ""
            end_date = request.POST["end_date"] if "end_date" in request.POST else ""

            form = Form.objects.filter(form_type__code="tpv", form_type__project_uuid=pu.project.uuid).first()
            if form != None:
                logger.info("[DEBUG]: PROCESANDO")
                res = form.to_tickets2(start_date, end_date)
                logger.info(f'[DEBUG]: PROCESADO')
                for t in res["tickets"]:
                    logger.info(f'[DEBUG]: TICKET {t["ticket numero"]} {t["fecha"]} {t["hora"]}')
                #logger.info("[DEBUG]: PROCESADO {}".format(res["tickets"]))
                return Response(res)
            return Response({"error": True, 'msg': 'This project do not have TPV configured!'})
        except Exception as e:
            logger.info("[DEBUG]: ERROR {}".format(str(e)))
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': str(e)})


    @action(detail=False, methods=['POST'])
    def get_tickets_tpv(self, request):
        try:
            if "tpv" not in request.POST:
                return Response({"error": True, 'msg': 'TPV not found in request!'})

            pu = ProjectUser.objects.get(username=self.request.user.username)
            pos = PointOfSale.objects.filter(project_uuid=pu.project.uuid, ext_code=request.POST["tpv"]).first()
            if pos == None:
                return Response({"error": True, 'msg': 'TPV not found!'})

            start_index = request.POST["start_index"] if "start_index" in request.POST else ""
            form = Form.objects.filter(form_type__code="tpv", form_type__project_uuid=pu.project.uuid).first()
            if form == None:
                return Response({"error": True, 'msg': 'This project do not have TPV configured!'})

            return Response(form.to_tickets_pos(pos.uuid, start_index))
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': 'Bad request!'})


class DepositBoxViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Lock.objects.none()
    serializer_class = LockSerializer
    permission_classes = [IsAuthenticated,]

    def serialize_depositbox(self, item):
        if item != None:
            return Response(LockSerializer(item, many=False).data)
        return Response({"error": True})

    def get_queryset(self):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            logger.info("[{}]: \"Deposit box list\"".format(self.request.user))
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
            lock = Lock.objects.get(uuid = request.GET["uuid"], project_uuid = pu.project_uuid)
            code_list = lock.get_all_passcodes()
            c_list = []
            for c in code_list:
                dic = {"uuid":c["lockId"],"code_id":c["keyboardPwdId"],"startDate":c["startDate"],"endDate":c["endDate"],"type":c["keyboardPwdType"],"passcode":c["keyboardPwd"]}
                c_list.append(dic)
            logger.info("[{}]: \"Get passcode of deposit box {}\"".format(self.request.user, lock.uuid))
            return Response(c_list, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": 'true', 'msg': 'Bad request!'})

    @action(detail=False, methods=['get'])
    def get_passcode_by_ext_id(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            ext_id = request.GET["ext_id"]
            lcei = LockCodeExtId.objects.filter(project_uuid=pu.project_uuid, ext_id=ext_id).first()
            if lcei == None:
                logger.error("[{}]: \"External code not found!\"".format(self.request.user))
                return Response({"error": True, "msg": "External code not found!"})
            lock = Lock.objects.get(uuid = lcei.lock_uuid, project_uuid = pu.project_uuid)
            code_list = lock.get_all_passcodes()
            c_list = []
            for c in code_list:
                if c["keyboardPwd"] == lcei.code:
                    dic = {"uuid":c["lockId"],"code_id":c["keyboardPwdId"],"startDate":c["startDate"],"endDate":c["endDate"],"type":c["keyboardPwdType"],"passcode":c["keyboardPwd"],"ext_id":ext_id}
                    c_list.append(dic)
            logger.info("[{}]: \"Get passcode of deposit box {}\"".format(self.request.user, lock.uuid))
            return Response(c_list, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": 'true', 'msg': 'Bad request!'})


    @action(detail=False, methods=['post'])
    def add_passcode(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            lock_uuid = request.POST["uuid"]
            code = request.POST["code"]
            name = request.POST["name"] if "name" in request.POST else ""
            start_date = datetime.strptime(request.POST.get('start_date', ""), "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(request.POST.get('end_date', ""), "%Y-%m-%d %H:%M")
            start_date_gmt = pu.project.gmt_date(start_date)
            end_date_gmt = pu.project.gmt_date(end_date)
            lock = Lock.objects.get(uuid=lock_uuid, project_uuid=pu.project_uuid)
            #err = lock.set_code(code, start_date, end_date, name)
            err = lock.set_code(code, start_date_gmt, end_date_gmt, name)

            if "ext_id" in request.POST:
                ext_id = request.POST["ext_id"]
                lcei, created = LockCodeExtId.objects.get_or_create(project_uuid=pu.project_uuid, lock_uuid=lock.uuid, code=code, ext_id=ext_id)

            if "Error" in str(err):
                logger.error("[{}]: \"{}\"".format(self.request.user, str(err)))
                return Response({"error": True, "msg": str(err)})
            else:
                logger.info("[{}]: \"Added passcode to deposit box {}\"".format(self.request.user, lock_uuid))
                return Response({"error": False, "code_id": err, "msg": "Code added successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': 'Bad request!'})

    @action(detail=False, methods=['post'])
    def change_passcode(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            lock_uuid = request.POST["uuid"]
            code_id = request.POST["code_id"]
            code = request.POST["code"]
            start_date = datetime.strptime(request.POST.get('start_date', ""), "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(request.POST.get('end_date', ""), "%Y-%m-%d %H:%M")
            start_date_gmt = pu.project.gmt_date(start_date)
            end_date_gmt = pu.project.gmt_date(end_date)
            lock = Lock.objects.get(uuid=lock_uuid, project_uuid=pu.project_uuid)
            #err = lock.change_code(code_id, code, start_date, end_date)
            err = lock.change_code(code_id, code, start_date_gmt, end_date_gmt)
            if "Error" in str(err):
                logger.error("[{}]: \"{}\"".format(self.request.user, str(err)))
                return Response({"error": True, "msg": str(err)})
            else:
                logger.info("[{}]: \"Changed passcode to deposit box {}\"".format(self.request.user, lock_uuid))
                return Response({"error": False, "msg": "Code changed successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': 'Bad request!'})

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
                logger.info("[{}]: \"Removed passcode to deposit box {}\"".format(self.request.user, lock_uuid))
                return Response({"error": False, "msg": "Code removed successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': 'Bad request!'})

class GuestCarViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = GuestCar.objects.none()
    serializer_class = GuestCarSerializer
    permission_classes = [IsAuthenticated,]

    def serialize_guestcar(self, item):
        if item != None:
            return Response(GuestCarSerializer(item, many=False).data)
        return Response({"error": True})

    def get_queryset(self):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            logger.info("[{}]: \"Guest car list\"".format(self.request.user))
            return GuestCar.objects.filter(guest__project_id=pu.project_uuid)
        except:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return GuestCar.objects.none()

    def create(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            pcu = ProjectCarUser.objects.filter(project_uuid=pu.project_uuid).first()
            if pcu == None or pcu.code == "":
                msg = "Camera not found!"
                logger.error("[{}]: \"{}\"".format(self.request.user, msg))
                return Response(data={'error': 'true', 'msg': msg}, status=status.HTTP_400_BAD_REQUEST)

            ext_id = request.POST.get('ext_id', "")
            number = request.POST.get('plate', "")
            guest = Guest.objects.filter(project_id=pu.project_uuid, ext_id=ext_id).first()

            if guest == None:
                msg = "Guest not found!"
                logger.error("[{}]: \"{}\"".format(self.request.user, msg))
                return Response(data={'error': 'true', 'msg': msg}, status=status.HTTP_400_BAD_REQUEST)

            gc, created = GuestCar.objects.get_or_create(number=number, guest=guest)
            logger.info("[{}]: \"Guest Car {} created for guest {} {}\"".format(self.request.user, number, guest.name, guest.surname))
            gc_data = self.serializer_class(gc).data
            return Response(data=gc_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response(data={'error': 'true', 'msg': "Bad request!"}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        logger.error("[{}]: \"Retrieve function is not offered in this path.\"".format(self.request.user))
        response = {'message': 'Retrieve function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, pk=None):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            pcu = ProjectCarUser.objects.filter(project_uuid=pu.project_uuid).first()
            if pcu == None or pcu.code == "":
                msg = "Camera not found!"
                logger.error("[{}]: \"{}\"".format(self.request.user, msg))
                return Response(data={'error': 'true', 'msg': msg}, status=status.HTTP_400_BAD_REQUEST)
            number = request.POST.get("plate", "")
            gc = GuestCar.objects.filter(guest__project_id=pu.project_uuid, guest__ext_id=pk, number=number).first()
            if gc != None:
                gc.delete()
            logger.info("[{}]: \"Guest car {} destroyed\"".format(self.request.user, number))
            return Response(data={'error': 'false'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response(data={'error': 'true', 'msg': 'Bad request!'}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        logger.error("[{}]: \"Update function is not offered in this path.\"".format(self.request.user))
        response = {'message': 'Update function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request, pk=None):
        logger.error("[{}]: \"Partial update function is not offered in this path.\"".format(self.request.user))
        response = {'message': 'Update function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)


class AccessZoneViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for access zones.
    """
    @action(detail=False, methods=['POST'])
    def get_access(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)
            start_date = request.POST["start_date"] if "start_date" in request.POST else ""
            end_date = request.POST["end_date"] if "end_date" in request.POST else ""
            access_zone = request.POST["access_zone"] if "access_zone" in request.POST else ""
            band_code = request.POST["band_code"] if "band_code" in request.POST else ""

            if start_date == "":
                date = datetime.today() + timedelta(days=-7)
                start_date = date.strftime("%Y-%m-%d")
            if end_date == "":
                date = datetime.today() + timedelta(days=7) 
                end_date = date.strftime("%Y-%m-%d")
            start_date = f"{start_date} 00:00:00"
            end_date = f"{end_date} 23:59:59"
            kwargs = {"access_point__zone__project_uuid": pu.project.uuid, "date__range": (start_date, end_date)}
            if access_zone != "":
                kwargs["access_point__zone__uuid"] = access_zone
            if band_code != "":
                kwargs["wristband__code"] = reverse_cardkey(band_code)

            access_list = WristbandAccess.objects.filter(**kwargs)
            return Response(WristbandAccessSerializer(access_list, many=True).data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': 'Bad request!'})


    @action(detail=False, methods=['POST'])
    def access_check(self, request):
        try:
            pu = ProjectUser.objects.get(username=self.request.user.username)

            access_point = request.POST["access_point"] if "access_point" in request.POST else ""
            code = request.POST["band_code"] if "band_code" in request.POST else ""

            ap = get_or_none(WristbandAccessPoint, access_point, "uuid")
            if ap== None:
                msg = "Punto de acceso no encontrado!"
                logger.error("[{}]: \"{}\"".format(self.request.user, msg))
                return Response({"error": True, 'msg': msg})

            band = Wristband.get_active_by_project(pu.project, reverse_cardkey(code))
            if band == None:
                msg = "Pulsera no encontrada!"
                logger.error("[{}]: \"{}\"".format(self.request.user, msg))
                return Response({"error": True, 'msg': msg})

            if not band.can_access_zone(ap.zone):
                msg = "Este usuario no tiene permisos para acceder a esta zona!" 
                logger.error("[{}]: \"{}\"".format(self.request.user, msg))
                return Response({"error": True, 'msg': msg})

            last_access = band.access.all().order_by("-id").first()
            if last_access == None:
                #Primer acceso
                if not ap.in_point:
                    msg = "Este es un punto de salida y no se ha registrado ninguna entrada!"
                    logger.error("[{}]: \"{}\"".format(self.request.user, msg))
                    return Response({"error": True, 'msg': msg})
                else:
                    msg = "Ha entrado correctamente!"
                    WristbandAccess.objects.create(wristband=band, access_point=ap, inside=True)
                    logger.error("[{}]: \"{}\"".format(self.request.user, msg))
                    return Response({"error": False, 'msg': msg})

            else:
                #Esta fuera
                if not last_access.inside:
                    #Punto de salida
                    if not ap.in_point:
                        msg = "Este es un punto de salida y no se ha registrado ninguna entrada"
                        logger.error("[{}]: \"{}\"".format(self.request.user, msg))
                        return Response({"error": True, 'msg': msg})
                    #Punto de entrada
                    else:
                        msg = "Ha entrado correctamente!"
                        WristbandAccess.objects.create(wristband=band, access_point=ap, inside=True)
                        logger.error("[{}]: \"{}\"".format(self.request.user, msg))
                        return Response({"error": False, 'msg': msg})
                #Esta dentro
                else:
                    #Punto de salida
                    if not ap.in_point:
                        msg = "Ha salido correctamente!"
                        WristbandAccess.objects.create(wristband=band, access_point=ap, inside=False)
                        logger.error("[{}]: \"{}\"".format(self.request.user, msg))
                        return Response({"error": False, 'msg': msg})
                    #Punto de entrada
                    else:
                        msg = "Este es un punto de entrada y no se ha registrado ninguna salida"
                        logger.error("[{}]: \"{}\"".format(self.request.user, msg))
                        return Response({"error": True, 'msg': msg})
            return Response({"error": True, 'msg': 'Error!'})
        except Exception as e:
            logger.error("[{}]: \"{}\"".format(self.request.user, str(e)))
            return Response({"error": True, 'msg': 'Bad request!'})


