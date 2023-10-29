from fastapi import FastAPI
from .routers import image, video


app = FastAPI()

app.include_router(image.router)
app.include_router(video.router)


@app.get("/")
def hello() -> str:
    return "HELLO WORLD"
