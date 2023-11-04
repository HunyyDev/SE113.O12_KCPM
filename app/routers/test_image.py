import os
import mmcv
import numpy as np
from app.routers.image import inferenceImage
from app.routers.image import handleImageRequest
import requests
import pytest
from io import StringIO

class TestImageRoute:
    img = mmcv.imread("demo.jpg")
    url = "http://0.0.0.0:3000"
    def test_inferenceImage(self):
        bboxes, labels = inferenceImage(self.img, 0.3, True)
        assert len(bboxes.tolist()) > 0 and len(labels.tolist()) > 0 and len(bboxes.tolist()) == len(labels.tolist())
        result = inferenceImage(self.img, 0.3)
        assert type(result) is np.ndarray and result.shape == self.img.shape
    def test_ImageAPI(self):
        with pytest.raises(NotImplementedError):
            payload = {}
            files=[
            ('file',('demo.jpg',open('demo.jpg','rb'),'image/jpeg'))
            ]
            headers = {
            'accept': 'application/json'
            }
            response = requests.request("POST", self.url, headers=headers, data=payload, files=files)
            assert response.status_code == 200
            assert response.content

