from .yolov8.YOLOv8 import YOLOv8

model_path = "./model/best20231112.onnx"
detector = YOLOv8(model_path)
