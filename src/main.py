from multiprocessing import Process
import os
import time
import aiofiles
import cv2
import mmcv
import numpy as np
import shutil
import requests
import json

from dotenv import load_dotenv

load_dotenv()

from supabase import create_client, Client
from mmdeploy_runtime import Detector
from fastapi import (
    FastAPI,
    File,
    Response,
    UploadFile,
    BackgroundTasks,
    WebSocket,
    WebSocketDisconnect,
)


model_path = "./model"
detector = Detector(model_path=model_path, device_name="cpu", device_id=0)

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = FastAPI()


@app.get("/")
def hello() -> str:
    return "hello"


def inferenceImage(img, threshold: float, isRaw: bool = False):
    bboxes, labels, _ = detector(img)
    if isRaw:
        removeIndexs = []
        for i, bbox in enumerate(bboxes):
            if bbox[4] < threshold:
                removeIndexs.append(i)

        bboxes = np.delete(bboxes, removeIndexs, axis=0)
        labels = np.delete(labels, removeIndexs)

        return bboxes, labels
    return mmcv.imshow_det_bboxes(
        img=img,
        bboxes=bboxes,
        labels=labels,
        class_names=class_name,
        show=False,
        colors=colors,
        score_thr=threshold,
    )


@app.post("/image")
async def handleImageRequest(
    file: bytes = File(...),
    threshold: float = 0.3,
    raw: bool = False,
):
    img = mmcv.imfrombytes(file, cv2.IMREAD_COLOR)
    if raw:
        bboxes, labels = inferenceImage(img, threshold, raw)
        return {"bboxes": bboxes.tolist(), "labels": labels.tolist()}

    img = inferenceImage(img, threshold, raw)
    ret, jpeg = cv2.imencode(".jpg", img)

    if not ret:
        return Response(content="Failed to encode image", status_code=500)
    jpeg_bytes: bytes = jpeg.tobytes()

    return Response(content=jpeg_bytes, media_type="image/jpeg")


@app.post("/video/{artifactId}")
async def handleVideoRequest(
    artifactId: str,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    threshold: float = 0.3,
):
    try:
        id = str(now())
        os.mkdir(id)
        async with aiofiles.open(os.path.join(id, "input.mp4"), "wb") as out_file:
            while content := await file.read(1024):
                await out_file.write(content)
        background_tasks.add_task(inferenceVideo, artifactId, id, threshold)
        return id + ".mp4"
    except ValueError as err:
        print(err)
        print("Error processing video")
        shutil.rmtree(id)


def now():
    return round(time.time() * 1000)


def inferenceVideo(artifactId: str, inputDir: str, threshold: float):
    try:
        Process(updateArtifact(artifactId, {"status": "processing"})).start()
        cap = cv2.VideoCapture(
            filename=os.path.join(inputDir, "input.mp4"), apiPreference=cv2.CAP_FFMPEG
        )
        fps = cap.get(cv2.CAP_PROP_FPS)
        size = (
            int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
        result = cv2.VideoWriter(
            filename=os.path.join(inputDir, "out.mp4"),
            fourcc=cv2.VideoWriter_fourcc(*"mp4v"),
            fps=fps,
            frameSize=size,
        )

        while cap.isOpened():
            res, frame = cap.read()
            if res == False:
                break

            resFram = inferenceImage(frame, threshold)
            result.write(resFram)

        cap.release()
        result.release()

        with open(os.path.join(inputDir, "out.mp4"), "rb") as f:
            res = supabase.storage.from_("video").upload(
                inputDir + ".mp4", f, {"content-type": "video/mp4"}
            )
        updateArtifact(
            artifactId,
            {
                "status": "success",
                "path": "https://hdfxssmjuydwfwarxnfe.supabase.co/storage/v1/object/public/video/"
                + inputDir
                + ".mp4",
            },
        )
    except:
        Process(
            updateArtifact(
                artifactId,
                {
                    "status": "fail",
                },
            )
        ).start()
    finally:
        shutil.rmtree(inputDir)


def updateArtifact(artifactId: str, body):
    url = "https://firebasetot.onrender.com/artifacts/" + artifactId
    payload = json.dumps(body)
    headers = {"Content-Type": "application/json"}
    requests.request("PATCH", url, headers=headers, data=payload)


@app.websocket("/image")
async def websocketEndpoint(websocket: WebSocket, threshold: float = 0.3):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            img = mmcv.imfrombytes(data, cv2.IMREAD_COLOR)
            bboxes, labels = inferenceImage(img, threshold, True)
            await websocket.send_json(
                {"bboxes": bboxes.tolist(), "labels": labels.tolist()}
            )
    except WebSocketDisconnect:
        pass


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
