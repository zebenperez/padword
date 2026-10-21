from django.urls import path

from . import views


urlpatterns = [
    path('project/<slug:project_uuid>/access/<slug:guest_uuid>/', views.project_access_auto, name='project-pwa-project-access-auto'),
    path('<uuid:pwa_uuid>/', views.public, name='project-pwa-public'),
    path('<uuid:pwa_uuid>/access/', views.access, name='project-pwa-access'),
    path('<uuid:pwa_uuid>/access/<slug:guest_uuid>/', views.access_auto, name='project-pwa-access-auto'),
    path('<uuid:pwa_uuid>/logout/', views.logout, name='project-pwa-logout'),
    path('<uuid:pwa_uuid>/app/', views.app, name='project-pwa-app'),
    path('<uuid:pwa_uuid>/locks/<int:lock_id>/open/', views.open_lock, name='project-pwa-open-lock'),
    path('<uuid:pwa_uuid>/manifest.json', views.manifest, name='project-pwa-manifest'),
    path('<uuid:pwa_uuid>/service-worker.js', views.service_worker, name='project-pwa-service-worker'),
]
