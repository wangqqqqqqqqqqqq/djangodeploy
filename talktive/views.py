from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class WebcamIndexView(LoginRequiredMixin, TemplateView):
    """只有登录用户才能访问"""
    template_name = 'welcomepage/welcome.html'
    login_url = '/logins/login/'  # 未登录时跳转到的登录页面