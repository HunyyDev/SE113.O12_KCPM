import datetime
import io
import cv2
from fastapi.responses import StreamingResponse
import qrcode
from fastapi import APIRouter, Depends, HTTPException, Response
from app.dependencies import get_current_user
from app import db, logger
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
    if user["sub"] is None:
        raise HTTPException(status_code=400, detail="User not found")
    friend_requests = (
        db.collection(COLLECTION_NAME).where("inviter", "==", user["sub"]).stream()
    )
    return {"friend_requests": [Request.to_dict() for Request in friend_requests]}


@router.post("")
def createRequest(user=Depends(get_current_user)):
    if user["sub"] is None:
        raise HTTPException(status_code=400, detail="User not found")
    _, fr_ref = db.collection(COLLECTION_NAME).add(
        {
            "invitor": user["sub"],
            "status": RequestStatus.WAITING_INVITEE.value,
            "expire_at": datetime.datetime.now()
            + datetime.timedelta(minutes=EXPIRE_MINUTES),
        }
    )

    try:
        qr = qrcode.make(fr_ref.id)
        buf = io.BytesIO()
        qr.save(buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        logger.error(e)
        fr_ref.delete()
        return Response(content="Failed to encode image", status_code=500)


@router.patch("/{RequestId}")
def acceptRequest(RequestId: str, user=Depends(get_current_user)):
    if user["sub"] is None:
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
            {"invitee": user["sub"], "status": RequestStatus.WAITING_INVITER.value}
        )
        sendNotificationToInviter(fr.inviter, user)
        return {"status": "OK"}


async def sendNotificationToInviter(inviterId: str, invitee):
    return HTTPException(status_code=501, detail="Not implemented yet")


async def makeFriend(inviteeId: str, inviterId: str):
    await insert2PersonAndSetFriend(inviteeId, inviterId)


@router.delete("/{RequestId}")
def deleteRequest(RequestId: str, user=Depends(get_current_user)):
    if user["sub"] is None:
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
    return Request.inviter == user["sub"]


def isRequestDone(Request):
    return Request.status == RequestStatus.COMPLETE.value


def isInviteeEmpty(Request):
    return Request.invitee is None
