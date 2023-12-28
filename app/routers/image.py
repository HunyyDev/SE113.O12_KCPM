import cv2

from fastapi import APIRouter, File, Response
from app.detector import detector
from mmcv import imfrombytes
from app import logger

router = APIRouter(prefix="/image", tags=["Image"])


@router.post("")
async def handleImageRequest(
    file: bytes = File(...),
    threshold: float = 0.3,
):
    try:
        img = imfrombytes(file, cv2.IMREAD_COLOR)

        img = inference_image(img, threshold)
    except Exception as e:
        logger.error(e)
        return Response(content="Failed to read image", status_code=400)

    ret, jpeg = cv2.imencode(".jpg", img)

    if not ret:
        return Response(content="Failed to encode image", status_code=500)
    jpeg_bytes: bytes = jpeg.tobytes()

    return Response(content=jpeg_bytes, media_type="image/jpeg")


def inference_image(img, threshold):
    detector.set_conf_threshold(threshold)
    detector(img)
    return detector.draw_detections(img)
