# app/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class BinanceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("binance_group", self.channel_name)
        await self.accept()
        print(" WebSocket connected")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("binance_group", self.channel_name)
        print("WebSocket disconnected")

    async def receive(self, text_data):
        print("Received from client:", text_data)

    async def send_binance_data(self, event):
        data = event['data']
        # print("Send to frontend:", data)
        await self.send(text_data=json.dumps(data))
