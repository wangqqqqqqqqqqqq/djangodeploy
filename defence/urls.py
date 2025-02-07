from django.urls import path
from . import views


urlpatterns = [
    path("", views.index, name="index"),  # 访问 Django 根路径时加载 Vue
]