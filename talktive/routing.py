from django.urls import path, re_path
from webcam.StreamConsumer import StreamConsumer
from defence.views import PacketCapture
websocket_urlpatterns = [
    re_path(r'ws/chat/$', StreamConsumer.as_asgi()),
    re_path(r'ws/capture/$',PacketCapture.as_asgi())
]