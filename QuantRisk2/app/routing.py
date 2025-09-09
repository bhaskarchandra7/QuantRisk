from django.urls import re_path
from app.consumers import BinanceConsumer

websocket_urlpatterns = [
    re_path(r'ws/binance/', BinanceConsumer.as_asgi()),
]
