from django.urls import path

from apps.converter import views

app_name = "converter"

urlpatterns = [
    path("", views.convert_home, name="home"),
    path("history/", views.history, name="history"),
    path("jobs/<uuid:job_id>/", views.job_detail, name="job_detail"),
    path("jobs/<uuid:job_id>/status/", views.job_status, name="job_status"),
    path("jobs/<uuid:job_id>/download/", views.download_result, name="download"),
    path("batches/<uuid:batch_id>/", views.batch_detail, name="batch_detail"),
    path("batches/<uuid:batch_id>/status/", views.batch_status, name="batch_status"),
    path(
        "batches/<uuid:batch_id>/download/",
        views.batch_download,
        name="batch_download",
    ),
    path("api/formats/", views.formats_api, name="formats_api"),
]
