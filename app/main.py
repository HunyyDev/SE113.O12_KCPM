from typing_extensions import Annotated
from fastapi import Depends, FastAPI
from app.dependencies import get_current_user
from .routers import image, video

def createApp():
    app = FastAPI()
    app.include_router(image.router)
    app.include_router(video.router)

    @app.get("/me")
    def getProfile(current_user: Annotated[any, Depends(get_current_user)]):
        return current_user


    @app.post("/login")
    def login(email: str, password: str):
        return "not implemented yet"


    @app.get("/")
    def hello():
        return "Hello World!"
    return app
    
createApp()