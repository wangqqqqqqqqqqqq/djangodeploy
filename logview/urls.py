from django.urls import path
from . import views
urlpatterns = [
    path("app_info/", views.app_info_view, name="app_info"),
    path("ip_info/",views.ip_info_view,name="ip_info"),
    path("stream_logs/", views.stream_log_cloudip, name="stream_log_cloudip"),  # 改为无参数，日期用 `POST`
    path("cloud_ip/", views.cloud_log, name="cloud_log"),
    path("stream_logs_ip/", views.stream_log_ip, name="stream_log_ip"),  # 改为无参数，日期用 `POST`
    path("http_logs_ip/", views.http_log_ip, name="http_log_ip"),
    path("ip_details/<str:ip>/",views.http_details,name="ip_details")
]