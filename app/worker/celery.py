from celery import Celery

app = Celery("worker", broker="redis://localhost:6379", include=["worker.tasks"])

if __name__ == "__main__":
    app.start()
