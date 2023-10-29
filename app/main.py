import asyncio
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

from constants import classNames, colors
from dotenv import load_dotenv
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

load_dotenv()

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
        class_names=classNames,
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


async def inferenceVideo(artifactId: str, inputDir: str, threshold: float):
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

        isFirstFrame = True
        thumbnail = None
        while cap.isOpened():
            res, frame = cap.read()
            if isFirstFrame:
                isFirstFrame = False
                thumbnail = frame

            if res == False:
                break

            resFram = inferenceImage(frame, threshold)
            result.write(resFram)

        cap.release()
        result.release()

        def createThumbnail(thumbnail):
            thumbnail = cv2.resize(
                src=thumbnail, dsize=(160, 160), interpolation=cv2.INTER_AREA
            )
            cv2.imwrite(os.path.join(inputDir, "thumbnail.jpg"), thumbnail)

        createThumbnail(thumbnail)

        async def uploadVideo():
            async with aiofiles.open(os.path.join(inputDir, "out.mp4"), "rb") as f:
                supabase.storage.from_("video").upload(
                    inputDir + ".mp4", await f.read(), {"content-type": "video/mp4"}
                )

        async def uploadThumbnail():
            async with aiofiles.open(
                os.path.join(inputDir, "thumbnail.jpg"), "rb"
            ) as f:
                supabase.storage.from_("thumbnail").upload(
                    inputDir + ".jpg", await f.read(), {"content-type": "image/jpeg"}
                )

        try:
            n = now()
            _, _ = await asyncio.gather(uploadVideo(), uploadThumbnail())
            print(now() - n)
        except Exception as e:
            print(e)

        updateArtifact(
            artifactId,
            {
                "status": "success",
                "path": "https://hdfxssmjuydwfwarxnfe.supabase.co/storage/v1/object/public/video/"
                + inputDir
                + ".mp4",
                "thumbnailURL": "https://hdfxssmjuydwfwarxnfe.supabase.co/storage/v1/object/public/thumbnail/"
                + inputDir
                + ".jpg",
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
