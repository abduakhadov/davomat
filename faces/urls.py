from django.urls import path

from .views import photo_upload_view, secure_image_view

urlpatterns = [
    path("profile/photo/", photo_upload_view, name="photo_upload"),
    path("faces/<uuid:pk>/image/", secure_image_view, name="secure_image"),
]
