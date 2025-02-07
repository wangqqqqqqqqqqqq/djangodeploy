from django.urls import path
from . import views
urlpatterns = [
    path("cloud_ip/", views.get_cloud_ip, name="cloud_ip2"),
    path("process_info/", views.get_process_info, name="process_info"),
    path("syscall_logs/", views.get_syscall_logs, name="syscall_logs"),
]