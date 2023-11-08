import asyncio
import os
import re
import shutil
import time
import aiofiles
import cv2

from multiprocessing import Process
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    BackgroundTasks,
    status,
)
from firebase_admin import messaging
from app import db
from app import supabase
from app.dependencies import get_current_user
from app.routers.image import inferenceImage
from google.cloud.firestore_v1.base_query import FieldFilter

router = APIRouter(prefix="/video", tags=["Video"])


@router.post("")
async def handleVideoRequest(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    threshold: float = 0.3,
    user=Depends(get_current_user),
):
    if re.search("^video\/", file.content_type) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be video",
        )

    try:
        if user["sub"] is None:
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User not found"
            )
        id = str(now())
        _, artifact_ref = db.collection("artifacts").add(
            {"name": id + ".mp4", "status": "pending"}
        )
        os.mkdir(id)
        async with aiofiles.open(os.path.join(id, "input.mp4"), "wb") as out_file:
            while content := await file.read(1024):
                await out_file.write(content)
        background_tasks.add_task(inferenceVideo, artifact_ref.id, id, threshold)
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
    artifact_snapshot = db.collection("artifacts").document(artifactId)
    if not artifact_snapshot.exists:
        artifact_snapshot.update(body)
    sendMessage(artifactId)


# This function cannot be automation test because the requirement of another device to receive notification
def sendMessage(artifactId: str, message: str = None):
    token = []
    artifact = db.collection("artifacts").document(artifactId).get()
    if not artifact.exists:
        return
    user_ref = db.collection("user").where(
        filter=FieldFilter("artifacts", "array-contains", "artifacts/" + artifactId)
    )
    for user in user_ref:
        token.append(user.get().to_dict()["deviceId"])
    if message is not None:
        messaging.MulticastMessage(
            data={
                "notification": {
                    "title": message,
                    "body": "Video "
                    + artifact.name
                    + " has done inference. Click here to see the video",
                },
            },
            android=messaging.AndroidConfig(
                notification=messaging.AndroidNotification(
                    icon="stock_ticker_update", color="#f45342"
                ),
            ),
        )
    else:
        messaging.MulticastMessage(
            data={
                "notification": {
                    "title": "Video " + artifact.name + " has done inference.",
                    "body": "Video "
                    + artifact.name
                    + " has done inference. Click here to see the video",
                },
            },
            android=messaging.AndroidConfig(
                notification=messaging.AndroidNotification(
                    icon="stock_ticker_update", color="#f45342"
                ),
            ),
        )
    response = messaging.send_multicast(message)
    return response.success_count
