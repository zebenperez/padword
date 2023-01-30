from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

import logging
logger = logging.getLogger(__name__)


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']

            if user.groups.filter(name='api').exists():
                token, created = Token.objects.get_or_create(user=user)
                logger.info("[{}]: \"Getting token\"".format(user))
                return Response({ 'token': token.key, })
            else:
                logger.error("[{}]: \"User not valid!\"".format(user))
                return Response({ 'error': 'true', 'msg': 'user not valid'})
        except Exception as e:
            logger.error("\"%s\"" % e)
            return Response({"error": 'true', 'msg': str(e)})
