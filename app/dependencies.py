from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin.auth import (
    ExpiredIdTokenError,
    InvalidIdTokenError,
    verify_id_token,
)
from . import db, logger

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        payload = verify_id_token(credentials.credentials)
        user_doc_ref = db.collection("user").document(payload["sub"]).get()
        if not user_doc_ref.exists:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User profile not exist"
            )
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
