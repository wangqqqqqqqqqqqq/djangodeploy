from django.urls import path
from . import views
urlpatterns = [
    path("login/",views.login_view,name="login"),
    path("register/",views.register_view,name="register"),
    path("user/",views.home_view,name="home"),
    path("logout/",views.logout_view,name="logout")
]