from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        if user.groups.filter(name='api').exists():
            token, created = Token.objects.get_or_create(user=user)
            return Response({ 'token': token.key, })
        else:
            return Response({ 'error': 'true', 'msg': 'user not valid'})
