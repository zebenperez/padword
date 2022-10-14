from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .guest_serializers import GuestSerializer

from guest.models import Guest
from web.models import ProjectUser

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
    http_method_names = ['post', 'get',]

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
                "UUID": request.POST.get('uuid', ""),
                "name": request.POST.get('name', ""),
                "surname": request.POST.get('surname', ""),
                "language": request.POST.get('language', ""),
                "mobile": request.POST.get('mobile', ""),
                "email": request.POST.get('email', ""),
                "check_in": request.POST.get('check_in', ""),
                "check_out": request.POST.get('check_out', ""),
                "project_id": pu.project_uuid,
            }
            serializer = self.serializer_class(data=data)
            #serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(data=serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def get_guest(self, request):
        try:
            item = Guest.objects.get(UUID = request.GET["uuid"])
            return self.serialize_guest(item)
        except Exception as e:
            logger.error("(get_guest): %s" % e)
            return Response({"error": True})


