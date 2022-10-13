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

    @action(detail=False, methods=['get'])
    def get_guest(self, request):
        try:
            print(request.GET)
            item = Guest.objects.get(pk = request.GET["id"])
            return self.serialize_guest(item)
        except Exception as e:
            logger.error("(get_guest): %s" % e)
            print(e)
            return Response({"error": True})


