import datetime
import io
import qrcode

from fastapi.responses import StreamingResponse
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
def getFriendRequest(current_user=Depends(get_current_user)):
    friend_requests = (
        db.collection(COLLECTION_NAME)
        .where("inviter", "==", current_user["sub"])
        .stream()
    )

    return {
        "friend_requests": [
            {**Request.to_dict(), "id": Request.id} for Request in friend_requests
        ]
    }


@router.post("")
def createRequest(user=Depends(get_current_user)):
    _, fr_ref = db.collection(COLLECTION_NAME).add(
        {
            "inviter": user["sub"],
            "status": RequestStatus.WAITING_INVITEE.value,
            "expire_at": datetime.datetime.now(tz=datetime.timezone.utc)
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
async def acceptRequest(RequestId: str, user=Depends(get_current_user)):
    fr_ref = db.collection(COLLECTION_NAME).document(RequestId)
    fr = fr_ref.get()

    if not fr.exists:
        raise HTTPException(status_code=404, detail="Friend request not found")

    fr = fr.to_dict()

    if isRequestExpired(fr):
        raise HTTPException(status_code=400, detail="Friend request expired")

    if isRequestDone(fr):
        raise HTTPException(status_code=400, detail="Friend request already done")

    if isInviter(user, fr):
        if isInviteeEmpty(fr):
            raise HTTPException(status_code=400, detail="Invitee is empty")
        fr_ref.update({"status": RequestStatus.COMPLETE.value})
        await makeFriend(fr["invitee"], fr["inviter"])
        return {"status": "OK"}

    if isInviteeEmpty(fr) and not isInviter(user, fr):
        fr_ref.update(
            {"invitee": user["sub"], "status": RequestStatus.WAITING_INVITER.value}
        )
        sendNotificationToInviter(fr["inviter"], user)
        return {"status": "OK"}


def sendNotificationToInviter(inviterId: str, invitee):
    return HTTPException(status_code=501, detail="Not implemented yet")


async def makeFriend(inviteeId: str, inviterId: str):
    await insert2PersonAndSetFriend(inviteeId, inviterId)


@router.delete("/{RequestId}")
def deleteRequest(RequestId: str, user=Depends(get_current_user)):
    Request_ref = db.collection(COLLECTION_NAME).document(RequestId)
    Request = Request_ref.get()

    if not Request.exists:
        raise HTTPException(status_code=404, detail="Friend request not found")
    Request = Request.to_dict()
    if isInviter(user, Request):
        Request_ref.delete()
        return {"status": "OK"}
    else:
        raise HTTPException(status_code=400, detail="You are not inviter")


def isRequestExpired(request):
    return request["expire_at"] < datetime.datetime.now(tz=datetime.timezone.utc)


def isInviter(user, Request):
    return Request["inviter"] == user["sub"]


def isRequestDone(Request):
    return Request["status"] == RequestStatus.COMPLETE.value


def isInviteeEmpty(Request):
    return True if Request.get("invitee", None) is None else False
