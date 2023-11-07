from app.custom_mmcv.color import color_val
from app.custom_mmcv.main import imshow_det_bboxes
from app.constants import classNames
import mmcv
import cv2
import numpy as np
import pytest
class TestCustomMMCV():
    def test_color_var(self):
        assert color_val("black") == (0, 0, 0)
        with pytest.raises(KeyError):
            color_val("purple")
        with pytest.raises(AssertionError):
            color_val(300)
        assert color_val(255) == (255,255,255)
        with pytest.raises(AssertionError):
            color_val(300)
        assert color_val(np.array([20,255,40])) == (20,255,40)
        with pytest.raises(AssertionError):
            color_val(np.array([20,350,40]))
        with pytest.raises(AssertionError):
            color_val(np.array([0,200,40,40]))
        with pytest.raises(AssertionError):
            color_val(np.array([-30,0,40,40]))
        with pytest.raises(AssertionError):
            color_val(np.zeros((1,3)))
        with pytest.raises(TypeError):
            color_val(30.5)
    def test_imshow_det_bboxes(self):
        image = mmcv.imread('demo.jpg')
        bboxes = np.ones((1,5))
        labels = np.zeros(1, dtype=np.int32)
        result = imshow_det_bboxes(image, bboxes, labels, class_names=classNames, bbox_color="red", text_color='red')
        assert (result[1,1,:] == (0,0,255)).all()
        with pytest.raises(AssertionError):
            bboxes = np.ones((1,3))
            labels = np.zeros(1, dtype=np.int32)
            result = imshow_det_bboxes(image, bboxes, labels, class_names=classNames, bbox_color="red",text_color="red")
        with pytest.raises(AssertionError):
            bboxes = np.ones((1,7))
            labels = np.zeros(1, dtype=np.int32)
            result = imshow_det_bboxes(image, bboxes, labels, class_names=classNames, bbox_color="red",text_color="red")
        with pytest.raises(AssertionError):
            bboxes = np.ones((1,5))
            labels = np.zeros(4, dtype=np.int32)
            result = imshow_det_bboxes(image, bboxes, labels, class_names=classNames, bbox_color="red",text_color="red")
        with pytest.raises(AssertionError):
            bboxes = np.ones((2,5))
            labels = np.zeros(1, dtype=np.int32)
            result = imshow_det_bboxes(image, bboxes, labels, class_names=classNames, bbox_color="red",text_color="red")
        