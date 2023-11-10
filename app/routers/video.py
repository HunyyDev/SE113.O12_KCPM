import os
import shutil
import cv2

from multiprocessing import Process
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from firebase_admin import messaging
from app import db
from app.dependencies import get_current_user, save_upload_video
from app.routers.image import inferenceImage
from google.cloud.firestore_v1.base_query import FieldFilter
from app import logger
from ..storage.main import upload

router = APIRouter(prefix="/video", tags=["Video"])


class ArtifactStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAIL = "fail"


@router.post("")
async def handleVideoRequest(
    current_user=Depends(get_current_user),
    id: str = Depends(save_upload_video),
    threshold: float = 0.3,
):
    try:
        setArtifact(id, {"user_id": current_user["sub"]})
        Process(target=inferenceVideo, args=(id, threshold)).start()
        return Response(status_code=status.HTTP_200_OK)
    except Exception as err:
        logger.error(err)
        shutil.rmtree(id)
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err
        )


async def inferenceVideo(id: str, threshold: float):
    setArtifact(id, {"name": id + ".mp4", "status": ArtifactStatus.PENDING})
    try:
        setArtifact(id, {"status": ArtifactStatus.PROCESSING})
        firstFrame = inference_each_frame(id, threshold=threshold)
        createThumbnail(firstFrame, id)

        video_url = await upload(f"{id}/result_video", f"{id}/out.mp4", "video/mp4")
        thumbnail_url = await upload(
            f"{id}/result_thumbnail", f"{id}/thumbnail.jpg", "image/jpeg"
        )

        setArtifact(
            id,
            {
                "status": ArtifactStatus.SUCCESS,
                "path": video_url,
                "thumbnailURL": thumbnail_url,
            },
        )
    except Exception as err:
        logger.error(err)
        setArtifact(id, {"status": ArtifactStatus.FAIL, "error": err})
    finally:
        try:
            shutil.rmtree(id)
        except PermissionError as e:
            print(e)


def inference_each_frame(id, threshold: float = 0.3):
    """
    This function is used to inference each frame of video
    The result will be saved in out.mp4

    Args:
        id (str): The id of the video
        threshold (float, optional): The threshold of the model. Defaults to 0.3.

    Returns:
        firstFrame: The first frame of the video
    """
    cap = cv2.VideoCapture(
        filename=os.path.join(id, "input.mp4"), apiPreference=cv2.CAP_FFMPEG
    )
    fps = cap.get(cv2.CAP_PROP_FPS)
    size = (
        int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    )
    result = cv2.VideoWriter(
        filename=os.path.join(id, "out.mp4"),
        fourcc=cv2.VideoWriter_fourcc(*"mp4v"),
        fps=fps,
        frameSize=size,
    )

    firstFrame = None
    while cap.isOpened():
        res, frame = cap.read()
        if firstFrame is None:
            firstFrame = frame

        if res == False:
            break

        resFram = inferenceImage(frame, threshold, False)
        result.write(resFram)

    cap.release()
    result.release()
    del cap
    del result

    return firstFrame


def createThumbnail(img, inputDir):
    """
    This function is used to create thumbnail of the video
    The thumbnail will be saved in thumbnail.jpg
    """
    thumbnail = cv2.resize(src=img, dsize=(160, 160), interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(inputDir, "thumbnail.jpg"), thumbnail)


def setArtifact(artifactId: str, body):
    """
    This function is used to update or create artifact if not exist in firestore
    """
    return db.collection("artifacts").document(artifactId).set(body, merge=True)


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
