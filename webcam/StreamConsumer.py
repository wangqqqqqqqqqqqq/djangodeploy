import json
import cv2
import numpy as np
from ultralytics import YOLO
from channels.generic.websocket import AsyncWebsocketConsumer

class StreamConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 加载模型
        self.model = YOLO('best.pt')  # 替换为你的模型路径

    async def connect(self):
        await self.accept()
        print("WebSocket connection established.")

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data:
            try:
                # 将二进制数据转换为 OpenCV 图像
                nparr = np.frombuffer(bytes_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                # 使用 YOLO 模型进行预测
                results = self.model.predict(source=frame)

                # 获取模型输入尺寸和视频帧尺寸
                model_width, model_height = 640, 384  # YOLO模型的输入尺寸
                frame_width, frame_height = frame.shape[1], frame.shape[0]  # 视频帧的实际尺寸
                print(frame_width)
                print(frame_height)
                # 计算预测框的缩放因子
                scale_x = frame_width / model_width
                scale_y = frame_height / model_height

                # 返回的边界框需要根据缩放因子调整
                predictions = []
                for result in results:
                    for box, confidence, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
                        x_min, y_min, x_max, y_max = box
                        # 缩放边界框
                        x_min = int(x_min * scale_x)
                        y_min = int(y_min * scale_y)
                        x_max = int(x_max * scale_x)
                        y_max = int(y_max * scale_y)
                        class_name = self.model.names[int(cls)]
                        predictions.append({
                            "class_name": class_name,
                            "confidence": float(confidence),
                            "bounding_box": [x_min, y_min, x_max, y_max]
                        })

                # 将结果发送回前端
                await self.send(text_data=json.dumps({
                    "predictions": predictions
                }))
            except Exception as e:
                print(f"Error during prediction: {e}")
        else:
            print("No bytes data received.")

    async def disconnect(self, close_code):
        print("WebSocket connection closed.")