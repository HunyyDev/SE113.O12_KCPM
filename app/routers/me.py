from fastapi import APIRouter, Depends

from app.dependencies import get_current_user


router = APIRouter(prefix="/me", tags=["Me"])


@router.get("")
def getProfile(current_user=Depends(get_current_user)):
    return current_user


@router.get("/friends")
def getFriends(current_user=Depends(get_current_user)):
    raise NotImplementedError()
