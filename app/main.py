from typing_extensions import Annotated
from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse

from app.dependencies import get_current_user
from .routers import image, video

def createApp():
    app = FastAPI()
    app.include_router(image.router)
    app.include_router(video.router)

    @app.get("/me")
    def getProfile(current_user: Annotated[any, Depends(get_current_user)]):
        return current_user


    @app.get("/login")
    def getProfile(current_user: Annotated[any, Depends(get_current_user)]):
        return current_user


    @app.get("/", include_in_schema=False)
    def hello():
        response = RedirectResponse(url="/docs")
        return response
createApp()
