from fastapi import APIRouter, Depends

from app.dependencies import get_current_user


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
def login(email: str, password: str):
    pass
