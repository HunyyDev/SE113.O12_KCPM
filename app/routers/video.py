import asyncio
import json
from multiprocessing import Process
import os
import re
import shutil
import time
import aiofiles
import cv2
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    BackgroundTasks,
    status,
)
import requests
from app import supabase
from app.dependencies import get_current_user
from app.routers.image import inferenceImage

router = APIRouter(prefix="/video", tags=["Video"])


@router.post("/{artifactId}")
async def handleVideoRequest(
    artifactId: str,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    threshold: float = 0.3,
    _=Depends(get_current_user),
):
    if re.search("^video\/", file.content_type) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be video",
        )

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
