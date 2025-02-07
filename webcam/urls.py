from django.urls import path
from . import views

urlpatterns = [
    path("",views.WebcamIndexView.as_view(), name='webcam_index'),
    path("webcams/",views.WebcamView.as_view(),name="webcams")
]