from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from app import logger
from firebase_admin import auth

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = auth.verify_id_token(credentials.credentials)
    except InvalidTokenError as e:
        logger.info(e)
        raise credentials_exception
    except ValueError as e:
        logger.info(e)
        raise credentials_exception
    except Exception as e:
        logger.info(e)
        print(e)
        raise credentials_exception

    return payload
