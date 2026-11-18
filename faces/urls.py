from django.urls import path

from .views import (
    davomat_check_api,
    davomat_reload_db_api,
    davomat_view,
    photo_upload_view,
    secure_image_view,
)

urlpatterns = [
    path("profile/photo/", photo_upload_view, name="photo_upload"),
    path("faces/<uuid:pk>/image/", secure_image_view, name="secure_image"),
    path("davomat/", davomat_view, name="davomat"),
    path("davomat/check/", davomat_check_api, name="davomat_check_api"),
    path("davomat/reload-db/", davomat_reload_db_api, name="davomat_reload_db_api"),
]
