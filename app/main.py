from fastapi import FastAPI
from starlette.responses import RedirectResponse


from app.graphdb.main import insert2PersonAndSetFriend, deleteFriend
from .routers import image, video, friend_request, me, auth

app = FastAPI()

app.include_router(image.router)
app.include_router(video.router)
app.include_router(friend_request.router)
app.include_router(me.router)
app.include_router(auth.router)


@app.get("/")
def redirect():
    return RedirectResponse(url="/docs")
