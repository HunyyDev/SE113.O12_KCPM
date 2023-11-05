from fastapi import APIRouter, File, Response, WebSocket, WebSocketDisconnect
import mmcv
import cv2
import numpy as np
from app.constants import classNames, colors
from app import detector


router = APIRouter(prefix="/image")


@router.post("")
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


@router.websocket("/")
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
