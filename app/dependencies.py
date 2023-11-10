from datetime import datetime
import os
import re
import shutil
import aiofiles
from fastapi import Depends, HTTPException, Request, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth
from firebase_admin.auth import ExpiredIdTokenError, InvalidIdTokenError
from app import logger
from . import db

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        payload = auth.verify_id_token(credentials.credentials)
        user_doc_ref = db.collection("user").document(payload["sub"]).get()
        if not user_doc_ref.exists:
            raise HTTPException(status_code=400, detail="User profile not found")
    except ExpiredIdTokenError as e:
        logger.warning(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidIdTokenError as e:
        logger.warning(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValueError as e:
        logger.warning(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def save_upload_video(request: Request, file: UploadFile):
    """
    Check if the file is video and save it to the disk

    Throws:
        400: if file is not a video
    """
    id = str(round(datetime.now().timestamp() * 1000))
    if re.search("^video\/", file.content_type) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be video",
        )

    try:
        os.mkdir(id)
        async with aiofiles.open(os.path.join(id, "input.mp4"), "wb") as out_file:
            while content := await file.read(10 * 1024):
                await out_file.write(content)
        return id
    except Exception as err:
        logger.error(err)
        shutil.rmtree(id)
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be video",
        )
