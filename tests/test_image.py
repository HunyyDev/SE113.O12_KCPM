import os
import mmcv
import numpy as np
from app.routers.image import inference_image
import pytest
import pytest
from fastapi.testclient import TestClient
from fastapi.routing import APIRoute
from app.main import app
def endpoints():
    endpoints = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            endpoints.append(route.path)
    return endpoints
@pytest.fixture
def client():
    client = TestClient(app, "http://0.0.0.0:3000")
    yield client
@pytest.mark.skipif("/image" not in endpoints(), reason="Route not defined")
class TestImageRoute():
    img = mmcv.imread('demo.jpg')
    url = "http://0.0.0.0:3000/image"
    def test_inferenceImage(self):
        bboxes, labels = inference_image(mmcv.imread('demo.jpg'), 0.3, True)
        assert len(bboxes.tolist()) > 0 and len(labels.tolist()) > 0 and len(bboxes.tolist()) == len(labels.tolist())
        result = inference_image(self.img, 0.3, False)
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
    def test_ImageAPI_one_channel_array(self, client):
        np.zeros((1,640,640)).dump("one_channel.jpg")
        payload = {}
        files=[
            ('file', ("demo.jpg",open("one_channel.jpg", "rb"),'image/jpeg'))
        ]
        headers = {
        'accept': 'application/json'
        }
        response = client.request("POST", "image", headers=headers, data=payload, files=files)
        assert response.status_code != 200
    def test_ImageAPIWithThresHold(self, client):
        payload = {}
        files=[
        ('file',('demo.jpg',open('demo.jpg','rb'),'image/jpeg'))
        ]
        headers = {
        'accept': 'application/json'
        }
        response = client.request("POST", "image?threshold=1&raw=True", headers=headers, data=payload, files=files)
        thresHold = 0.4
        assert response.status_code == 200 # The result with threshold equal 0 is 0 
        # No detected object has 100% accuracy
        assert len(response.json()["labels"]) == 0
        payload = {}
        files=[
        ('file',('demo.jpg',open('demo.jpg','rb'),'image/jpeg'))
        ]
        headers = {
        'accept': 'application/json'
        }
        response = client.request("POST", "image?threshold=" + str(thresHold) + "&raw=True", headers=headers, data=payload, files=files)
        assert response.status_code == 200
        for bbox in response.json()['bboxes']:
            assert bbox[4] >= thresHold

