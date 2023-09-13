import zmq
import mmcv
import os
import requests

from mmdeploy_runtime import Detector
from multiprocessing.pool import ThreadPool

class_name = [
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "airplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign",
    "parking meter",
    "bench",
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "frisbee",
    "skis",
    "snowboard",
    "sports ball",
    "kite",
    "baseball bat",
    "baseball glove",
    "skateboard",
    "surfboard",
    "tennis racket",
    "bottle",
    "wine glass",
    "cup",
    "fork",
    "knife",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "sandwich",
    "orange",
    "broccoli",
    "carrot",
    "hot dog",
    "pizza",
    "donut",
    "cake",
    "chair",
    "couch",
    "potted plant",
    "bed",
    "dining table",
    "toilet",
    "tv",
    "laptop",
    "mouse",
    "remote",
    "keyboard",
    "cell phone",
    "microwave",
    "oven",
    "toaster",
    "sink",
    "refrigerator",
    "book",
    "clock",
    "vase",
    "scissors",
    "teddy bear",
    "hair drier",
    "toothbrush",
]

colors = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
    (255, 0, 255),
    (0, 255, 255),
    (128, 0, 0),
    (0, 128, 0),
    (0, 0, 128),
    (128, 128, 0),
    (128, 0, 128),
    (0, 128, 128),
    (165, 42, 42),
    (210, 105, 30),
    (218, 165, 32),
    (139, 69, 19),
    (244, 164, 96),
    (255, 99, 71),
    (255, 127, 80),
    (255, 69, 0),
    (255, 140, 0),
    (255, 215, 0),
    (218, 112, 214),
    (255, 182, 193),
    (255, 192, 203),
    (255, 20, 147),
    (199, 21, 133),
    (255, 105, 180),
    (255, 0, 255),
    (255, 250, 205),
    (250, 128, 114),
    (255, 99, 71),
    (255, 69, 0),
    (255, 140, 0),
    (255, 215, 0),
    (255, 223, 0),
    (255, 182, 193),
    (255, 192, 203),
    (255, 20, 147),
    (199, 21, 133),
    (255, 105, 180),
    (255, 0, 255),
    (255, 250, 205),
    (250, 128, 114),
    (255, 99, 71),
    (255, 69, 0),
    (255, 140, 0),
    (255, 215, 0),
    (173, 255, 47),
    (154, 205, 50),
    (85, 107, 47),
    (144, 238, 144),
    (0, 128, 0),
    (0, 255, 0),
    (50, 205, 50),
    (0, 250, 154),
    (0, 255, 127),
    (0, 128, 128),
    (0, 139, 139),
    (0, 206, 209),
    (70, 130, 180),
    (100, 149, 237),
    (0, 0, 128),
    (0, 0, 139),
    (0, 0, 205),
    (0, 0, 255),
    (0, 191, 255),
    (30, 144, 255),
    (135, 206, 235),
    (173, 216, 230),
    (175, 238, 238),
    (240, 248, 255),
    (240, 255, 240),
    (245, 245, 220),
    (255, 228, 196),
    (255, 235, 205),
    (255, 239, 219),
    (255, 245, 238),
    (245, 222, 179),
    (255, 248, 220),
    (255, 250, 240),
    (250, 250, 210),
    (253, 245, 230),
]

model_path = "model"
detector = Detector(model_path=model_path, device_name="cpu", device_id=0)

def main():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")
    while True:
        type, threshold, path, filename, artifactId = socket.recv_multipart()
        threshold = float(threshold.decode("utf-8"))
        type = type.decode()
        if type == "image":
            inferenceImage(socket, threshold, path.decode())
        if type == "video":
            socket.send_string("ok")
            inferenceVideo(
                socket, threshold, path.decode(), filename.decode(), artifactId.decode()
            )


def inferenceImage(socket: zmq.Socket, threshold: float, path: str):
    img = mmcv.imread(path)
    bboxes, labels, _ = detector(img)
    mmcv.imshow_det_bboxes(
        img=img,
        bboxes=bboxes,
        labels=labels,
        class_names=class_name,
        show=False,
        colors=colors,
        score_thr=threshold,
        out_file="out.jpg",
    )
    path = os.path.join(os.getcwd(), "out.jpg")
    socket.send_string(path)


def detectOneFrame(frame, frame_count, threshold):
    bboxes, labels, _ = detector(frame)
    mmcv.imshow_det_bboxes(
        frame,
        bboxes=bboxes,
        labels=labels,
        class_names=class_name,
        out_file="frame/{:06d}.jpg".format(frame_count),
        show=False,
        score_thr=threshold,
        colors=colors,
    )


def inferenceVideo(
    socket: zmq.Socket, threshold: float, path: str, filename: str, artifactId: str
):
    video_reader = mmcv.VideoReader(path)
    frame_count = 0
    with ThreadPool() as pool:
        for frame in video_reader:
            pool.apply_async(detectOneFrame(frame, frame_count, threshold))
            frame_count += 1
        pool.close()
        pool.join()
    mmcv.video.frames2video(
        fourcc="mp4v",
        frame_dir="frame",
        filename_tmpl="{:06d}.jpg",
        video_file="out.mp4",
        fps=video_reader.fps,
    )
    path = os.path.join(os.getcwd(), "out.mp4")
    uploadFileToStorage(path, filename, artifactId)


def uploadFileToStorage(path: str, filename: str, artifactId: str):
    url = (
        "https://hdfxssmjuydwfwarxnfe.supabase.co/storage/v1/object/video/"
        + filename
        + ".mp4"
    )
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer"
        + " eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkZnhzc21qdXlkd2Z3YXJ4bmZlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTY5Mjc3MjQyMCwiZXhwIjoyMDA4MzQ4NDIwfQ.CSsKUjwRc54W3NbAyO-7q3OJlX_lhRFiCQq-A7n5HAk",
        "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkZnhzc21qdXlkd2Z3YXJ4bmZlIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTI3NzI0MjAsImV4cCI6MjAwODM0ODQyMH0.RbC9lWKG1SR36WOPzGHErlf-i66wgHL4NFqHnSH9eHM",
    }
    file = {"file": open(path, "rb")}
    response = requests.request("POST", url, headers=headers, files=file)
    if response.status_code == 200:
        url = "https://firebasetot.onrender.com/artifacts"
        if artifactId == "undefined":
            print("artifactId is undefined, sending test message")
            testdata = {"id": "testId", "path": "testURL"}
            response = requests.post(url, json=testdata)
        else:
            response = requests.post(
                url,
                json={
                    "id": artifactId,
                    "path": "https://hdfxssmjuydwfwarxnfe.supabase.co"
                    + "/storage/v1/object/public/video/"
                    + filename
                    + ".mp4",
                },
            )


if __name__ == "__main__":
    main()
