import json

import msgpack
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from channels.generic.websocket import AsyncWebsocketConsumer

import json
import asyncio
import aioredis
import socket
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime

import httpx
from datetime import datetime


async def fetch_geolocation(ip):
    """通过 ip-api 获取地理位置信息"""
    url = f"http://ip-api.com/json/{ip}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                geo_data = response.json()
                if geo_data.get("status") == "success":
                    return {
                        "country": geo_data.get("country"),
                        "region": geo_data.get("regionName"),
                        "city": geo_data.get("city"),
                        "lat": geo_data.get("lat"),
                        "lon": geo_data.get("lon"),
                        "isp": geo_data.get("isp"),
                    }
        except Exception as e:
            print(f"Error fetching geolocation for {ip}: {e}")
    return None
class PacketCapture(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis = None  # Redis 连接池
        self.channel_name = "packet_cache"  # Redis 缓存的频道名
        self.remote_connections = {}  # 维护多个服务端连接

    async def connect(self):
        # 接收 WebSocket 连接
        await self.accept()
        self.redis = await aioredis.from_url(
            "redis://127.0.0.1:6379",
            decode_responses=True
        )  # 初始化 Redis 连接
        print("Redis connection established.")
    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            try:
                # 解析 JSON 数据
                data = json.loads(text_data)
                # 根据 JSON 数据中的 action 字段处理不同的请求
                action = data.get("command")
                if action == "connect":
                    # 连接到远程监控程序
                    ip = data.get("ip", "127.0.0.1")
                    port = data.get("port", 9999)
                    await self.connect_to_remote(ip, port)
                    await self.send(text_data=json.dumps({"status": "successconnect","ip":ip, "message": f"Connected to {ip}:{port}"}))
                elif action == "disconnect":
                    # 断开所有远程连接
                    await self.disconnect_all_remotes()
                    await self.send(text_data=json.dumps({"status": "successdisconnect", "message": "Disconnected from all servers"}))
                elif action == "send_command":
                    # 将命令转发给所有连接的远程服务端
                    command = data.get("command", {})
                    ip = data.get("ip", "127.0.0.1")
                    port = data.get("port", 9999)
                    responses = await self.send_to_remote(ip,port,data)
                    await self.send(text_data=json.dumps({"status": "success", "responses": responses}))
                elif action == "get_cache":
                    # 从 Redis 获取缓存数据
                    key = data.get("key", self.channel_name)
                    cached_data = await self.redis.zrangebyscore(key, "-inf", "+inf")
                    await self.send(text_data=json.dumps({"status": "cache", "data": cached_data}))
            except json.JSONDecodeError:
                await self.send(text_data=json.dumps({"status": "error", "message": "Invalid JSON format"}))
            except Exception as e:
                await self.send(text_data=json.dumps({"status": "error", "message": str(e)}))
    async def disconnect(self, close_code):
        # 关闭 Redis 和所有远程连接
        if self.redis:
            await self.redis.close()
            print("Redis connection closed.")
        await self.disconnect_all_remotes()
    async def connect_to_remote(self, ip, port):
        """连接到远程监控程序"""
        try:
            # 创建连接到远程监控程序的 socket
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.settimeout(None)
            remote_socket.connect((ip, port))
            # 保存到连接字典中
            self.remote_connections[f"{ip}:{port}"] = remote_socket
            print(f"Connected to remote server: {ip}:{port}")
            await self.send_to_remote(ip,port,{"action":"fetch_next"})
            # 启动一个异步任务，持续接收来自服务端的数据
            asyncio.create_task(self.receive_from_remote(ip, port, remote_socket))
        except Exception as e:
            print(f"Failed to connect to remote server {ip}:{port}: {e}")
            await self.send(json.dumps({"status":"failconnected","ip":ip,"port":port}))
            raise e
    async def disconnect_all_remotes(self):
        """断开所有远程监控程序的连接"""
        for addr, sock in list(self.remote_connections.items()):
            try:
                sock.close()
                print(f"Disconnected from {addr}")
            except Exception as e:
                print(f"Error disconnecting from {addr}: {e}")
        self.remote_connections.clear()

    async def receive_from_remote(self, ip, port, remote_socket):
        """持续接收来自远程监控程序的数据"""
        buffer = ""  # 修改为字符串
        while True:
            data = remote_socket.recv(4096)  # 接收数据
            if not data:
                break  # 如果数据为空，退出
            buffer = data.decode("utf-8").strip()  # 解码并去掉多余的空白字符
            print(buffer)
            if not buffer.endswith("}"):
                while not buffer.endswith("}"):
                    data=remote_socket.recv(4096)
                    buffer+=data.decode("utf-8").strip()
            parsed_data = json.loads(buffer,strict=False)
            print(parsed_data)
                        # 根据数据内容进行处理
            if parsed_data.get("chioce") == "dataPacket":
                print(f"Received from {ip}:{port}: {parsed_data}")
                # 将接收到的数据存储到 Redis 的 ZSET
                timestamp = datetime.now().timestamp()
                redis_key = f"{ip}:{port}_data"
                ip_src = parsed_data.get("ip_src")
                geo_data = await fetch_geolocation(ip_src) if ip_src else None
                print(geo_data)
                        # 将地理位置信息添加到数据中
                if geo_data:
                    parsed_data.update(geo_data)
                await self.redis.zadd(redis_key, {json.dumps(parsed_data): timestamp})
                # 设置过期时间
                await self.redis.expire(redis_key, 7200)
                await self.send(
                        text_data=json.dumps(
                            {
                                "status": "datapacket",
                                "ip":ip,
                                "packet": json.dumps(parsed_data),
                            }
                        )
                    )
            elif parsed_data.get("chioce") == "controldevice":
                await self.send(
                    text_data=json.dumps(
                        {
                            "status": "devicelist",
                            "ip": parsed_data.get("ip"),
                            "device": json.dumps(parsed_data),
                        }
                    )
                )
            elif parsed_data.get("chioce") == "controlstatus":
                await self.send(
                    text_data=json.dumps(
                        {"status": "getstatus", "ip": parsed_data.get("ip"), "device": parsed_data.device}
                    )
                )
            elif parsed_data.get("chioce") == "stops":
                await self.send(text_data=json.dumps({"status": "stopdevice", "ip": parsed_data.get("ip")}))
            elif parsed_data.get("chioce") == "controlerror":
                pass
            elif parsed_data.get("chioce") == "controlswitch":
                pass
            elif parsed_data.get("chioce") == "dataPacketNone":
                await self.send_to_remote(ip, port, {"action": "fetch_next"})
            print("enter sending next")
            await self.send_to_remote(ip, port, {"action": "fetch_next"})
    async def send_to_remote(self, ip, port, command):
        """向指定远程监控程序发送命令并接收响应"""
        addr = f"{ip}:{port}"
        if addr not in self.remote_connections:
            raise ConnectionError(f"Not connected to {addr}")
        remote_socket = self.remote_connections[addr]
        try:
            command_json = json.dumps(command).encode("utf-8")
            remote_socket.sendall(command_json)
            return "ok"
        except Exception as e:
            print(f"Error communicating with {addr}: {e}")
            return {"status": "error", "message": str(e)}
    async def broadcast_to_remotes(self, ip,port,command):
        """向所有远程监控程序发送命令并接收响应"""
        responses = {}
        for addr, remote_socket in self.remote_connections.items():
            try:
                if str(ip)+":"+str(port) == addr:
                    response = await self.send_to_remote(*addr.split(":"), command)
                    responses[addr] = response
            except Exception as e:
                responses[addr] = {"status": "error", "message": str(e)}
        return responses

@login_required
def index(request):
    return redirect("/static/dist/index.html")
