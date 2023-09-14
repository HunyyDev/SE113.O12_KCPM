import cv2
import mmcv
import numpy as np
import time

from flask import Flask, Response, request
from mmdeploy_runtime import Detector

def current_milli_time():
    return round(time.time() * 1000)

class_name = [
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "airplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign",
    "parking meter",
    "bench",
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "frisbee",
    "skis",
    "snowboard",
    "sports ball",
    "kite",
    "baseball bat",
    "baseball glove",
    "skateboard",
    "surfboard",
    "tennis racket",
    "bottle",
    "wine glass",
    "cup",
    "fork",
    "knife",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "sandwich",
    "orange",
    "broccoli",
    "carrot",
    "hot dog",
    "pizza",
    "donut",
    "cake",
    "chair",
    "couch",
    "potted plant",
    "bed",
    "dining table",
    "toilet",
    "tv",
    "laptop",
    "mouse",
    "remote",
    "keyboard",
    "cell phone",
    "microwave",
    "oven",
    "toaster",
    "sink",
    "refrigerator",
    "book",
    "clock",
    "vase",
    "scissors",
    "teddy bear",
    "hair drier",
    "toothbrush",
]

colors = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
    (255, 0, 255),
    (0, 255, 255),
    (128, 0, 0),
    (0, 128, 0),
    (0, 0, 128),
    (128, 128, 0),
    (128, 0, 128),
    (0, 128, 128),
    (165, 42, 42),
    (210, 105, 30),
    (218, 165, 32),
    (139, 69, 19),
    (244, 164, 96),
    (255, 99, 71),
    (255, 127, 80),
    (255, 69, 0),
    (255, 140, 0),
    (255, 215, 0),
    (218, 112, 214),
    (255, 182, 193),
    (255, 192, 203),
    (255, 20, 147),
    (199, 21, 133),
    (255, 105, 180),
    (255, 0, 255),
    (255, 250, 205),
    (250, 128, 114),
    (255, 99, 71),
    (255, 69, 0),
    (255, 140, 0),
    (255, 215, 0),
    (255, 223, 0),
    (255, 182, 193),
    (255, 192, 203),
    (255, 20, 147),
    (199, 21, 133),
    (255, 105, 180),
    (255, 0, 255),
    (255, 250, 205),
    (250, 128, 114),
    (255, 99, 71),
    (255, 69, 0),
    (255, 140, 0),
    (255, 215, 0),
    (173, 255, 47),
    (154, 205, 50),
    (85, 107, 47),
    (144, 238, 144),
    (0, 128, 0),
    (0, 255, 0),
    (50, 205, 50),
    (0, 250, 154),
    (0, 255, 127),
    (0, 128, 128),
    (0, 139, 139),
    (0, 206, 209),
    (70, 130, 180),
    (100, 149, 237),
    (0, 0, 128),
    (0, 0, 139),
    (0, 0, 205),
    (0, 0, 255),
    (0, 191, 255),
    (30, 144, 255),
    (135, 206, 235),
    (173, 216, 230),
    (175, 238, 238),
    (240, 248, 255),
    (240, 255, 240),
    (245, 245, 220),
    (255, 228, 196),
    (255, 235, 205),
    (255, 239, 219),
    (255, 245, 238),
    (245, 222, 179),
    (255, 248, 220),
    (255, 250, 240),
    (250, 250, 210),
    (253, 245, 230),
]


UPLOAD_FOLDER = "/uploads"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

model_path = "model"
detector = Detector(model_path=model_path, device_name="cpu", device_id=0)


@app.get("/")
def hello():
    return "hello"


def inferenceImage(img, threshold: float):
    now = current_milli_time()
    bboxes, labels, _ = detector(img)
    print(current_milli_time()-now)
    return mmcv.imshow_det_bboxes(
        img=img,
        bboxes=bboxes,
        labels=labels,
        class_names=class_name,
        show=False,
        colors=colors,
        score_thr=threshold,
        font_scale=2.0,
    )


@app.get("/demo_image")
def inferenceDemoImage():
    image = cv2.imread("demo4.jpg")
    threshold = request.args.get("threshold", default=0.3, type=float)
    image = inferenceImage(image, threshold)
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
    ret, jpeg = cv2.imencode(".jpg", image, encode_param)
    if not ret:
        return "Failed to encode image", 500
    jpeg_bytes = jpeg.tobytes()

    return Response(jpeg_bytes, content_type="image/jpeg")


@app.post("/upload_image")
def inferenceSingleImage():
    if request.data == b"":
        return "The body is empty, expect image", 400

    nparr = np.frombuffer(request.data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    threshold = request.args.get("threshold", default=0.3, type=float)
    image = inferenceImage(image, threshold)
    ret, jpeg = cv2.imencode(".jpg", image)
    if not ret:
        return "Failed to encode image", 500
    jpeg_bytes = jpeg.tobytes()

    return Response(jpeg_bytes, content_type="image/jpeg")
