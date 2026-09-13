from django.urls import path

from . import views


urlpatterns = [
    path('projects/<slug:project_uuid>/pwas/', views.list, name='project-pwa-list'),
    path('projects/<slug:project_uuid>/pwas/new/', views.create, name='project-pwa-create'),
    path('projects/<slug:project_uuid>/pwas/<uuid:pwa_uuid>/edit/', views.edit, name='project-pwa-edit'),
    path('projects/<slug:project_uuid>/pwas/<uuid:pwa_uuid>/publish/', views.publish, name='project-pwa-publish'),
    path('projects/<slug:project_uuid>/pwas/<uuid:pwa_uuid>/unpublish/', views.unpublish, name='project-pwa-unpublish'),
]
