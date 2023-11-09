from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.graphdb.main import insert2PersonAndSetFriend, deleteFriend
from .routers import image, video, friend_request, me

app = FastAPI()

app.include_router(image.router)
app.include_router(video.router)
app.include_router(friend_request.router)
app.include_router(me.router)



@app.get("/test")
async def test():
    await insert2PersonAndSetFriend("1", "2")
    await deleteFriend("1", "2")
