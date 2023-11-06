import os
import mmcv
import numpy as np
from app.routers.image import inferenceImage
from app.routers.image import handleImageRequest
import requests
import pytest
from io import StringIO
import pytest
from app.main import createApp
from PIL import Image
from fastapi.testclient import TestClient
@pytest.fixture
def client():
    client = TestClient(createApp(), "http://0.0.0.0:3000")
    yield client
class TestImageRoute():
    url = "http://0.0.0.0:3000/image"
    def test_inferenceImage(self):
        bboxes, labels = inferenceImage(mmcv.imread('demo.jpg'), 0.3, True)
        assert len(bboxes.tolist()) > 0 and len(labels.tolist()) > 0 and len(bboxes.tolist()) == len(labels.tolist())
        result = inferenceImage(self.img, 0.3)
        assert type(result) is np.ndarray and result.shape == self.img.shape
    def test_ImageAPI(self, client):
        payload = {}
        files=[
        ('file',('demo.jpg',open('demo.jpg','rb'),'image/jpeg'))
        ]
        headers = {
        'accept': 'application/json'
        }
        response = client.request("POST", "image", headers=headers, data=payload, files=files)
        result = mmcv.imfrombytes(response.read())
        assert response.status_code == 200 and result.shape == self.img.shape
    # def test_ImageAPI_one_channel_array(self, client):
    #     np.zeros((1,640,640)).dump("one_channel.jpg")
    #     payload = {}
    #     files=[
    #         ('file', ("demo.jpg",open("one_channel.jpg", "rb"),'image/jpeg'))
    #     ]
    #     headers = {
    #     'accept': 'application/json'
    #     }
    #     response = client.request("POST", "image", headers=headers, data=payload, files=files)
    #     assert response.status_code != 200
    def test_ImageAPIWithThresHold(self, client):
        payload = {}
        files=[
        ('file',('demo.jpg',open('demo.jpg','rb'),'image/jpeg'))
        ]
        headers = {
        'accept': 'application/json'
        }
        response = client.request("POST", "image?threshold=1&raw=True", headers=headers, data=payload, files=files)
        assert response.status_code == 200 and len(response.json()["labels"]) == 0

