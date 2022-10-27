from django.urls import include, path
from rest_framework import routers
from rest_framework.authtoken import views as views_token
from . import views
from .custom_auth import CustomAuthToken

router = routers.DefaultRouter()
router.register(r'guest', views.GuestViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api-token-auth/', CustomAuthToken.as_view())
    #path('api-token-auth/', views_token.obtain_auth_token)
]
