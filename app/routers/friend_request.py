import datetime
import cv2
import qrcode
from fastapi import APIRouter, Depends, HTTPException, Response
from app.dependencies import get_current_user
from app import db
from enum import Enum
from app.graphdb.main import insert2PersonAndSetFriend


router = APIRouter(prefix="/friend_request", tags=["friend_request"])


class RequestStatus(Enum):
    WAITING_INVITEE = "waiting_invitee"
    WAITING_INVITER = "waiting_inviter"
    COMPLETE = "complete"


COLLECTION_NAME = "friend_request"
EXPIRE_MINUTES = 15


@router.get("")
def getFriendRequest(user=Depends(get_current_user)):
    if user.uid is None:
        raise HTTPException(status_code=400, detail="User not found")
    friend_requests = (
        db.collection(COLLECTION_NAME).where("inviter", "==", user.uid).stream()
    )
    return {"friend_requests": [Request.to_dict() for Request in friend_requests]}


@router.post("")
def createRequest(user=Depends(get_current_user)):
    if user.uid is None:
        raise HTTPException(status_code=400, detail="User not found")
    _, fr_ref = db.collection(COLLECTION_NAME).add(
        {
            "invitor": user.uid,
            "status": RequestStatus.WAITING_INVITEE.value,
            "expire_at": datetime.now() + datetime.timedelta(minutes=EXPIRE_MINUTES),
        }
    )
    qr = qrcode.make(fr_ref.id)

    ret, png = cv2.imencode(".jpg", qr)

    if not ret:
        fr_ref.delete()
        return Response(content="Failed to encode image", status_code=500)

    png_bytes = png.tobytes()

    return Response(content=png_bytes, media_type="image/png")


@router.patch("/{RequestId}")
def acceptRequest(RequestId: str, user=Depends(get_current_user)):
    if user.uid is None:
        raise HTTPException(status_code=400, detail="User not found")

    fr_ref = db.collection(COLLECTION_NAME).document(RequestId)
    fr = fr_ref.get()

    if not fr.exists:
        raise HTTPException(status_code=404, detail="Friend request not found")

    if isRequestExpired(fr):
        raise HTTPException(status_code=400, detail="Friend request expired")

    if isRequestDone(fr):
        raise HTTPException(status_code=400, detail="Friend request already done")

    if isInviter(user, fr):
        fr_ref.update({"status": RequestStatus.COMPLETE.value})
        makeFriend(fr.invitee, fr.inviter)
        return {"status": "OK"}

    if isInviteeEmpty(fr) and not isInviter(user, fr):
        fr_ref.update(
            {"invitee": user.uid, "status": RequestStatus.WAITING_INVITER.value}
        )
        sendNotificationToInviter(fr.inviter, user)
        return {"status": "OK"}


async def sendNotificationToInviter(inviterId: str, invitee):
    pass


async def makeFriend(inviteeId: str, inviterId: str):
    await insert2PersonAndSetFriend(inviteeId, inviterId)


@router.delete("/{RequestId}")
def deleteRequest(RequestId: str, user=Depends(get_current_user)):
    if user.uid is None:
        raise HTTPException(status_code=400, detail="User not found")

    Request_ref = db.collection(COLLECTION_NAME).document(RequestId)
    Request = Request_ref.get()

    if not Request.exists:
        raise HTTPException(status_code=404, detail="Friend request not found")

    if isInviter(user, Request):
        Request_ref.delete()
        return {"status": "OK"}
    else:
        raise HTTPException(status_code=400, detail="You are not inviter")


def isRequestExpired(request):
    return request.expire_at < datetime.now()


def isInviter(user, Request):
    return Request.inviter == user.uid


def isRequestDone(Request):
    return Request.status == RequestStatus.COMPLETE.value


def isInviteeEmpty(Request):
    return Request.invitee is None
