# THE ORIGINAL mmcv.imshow_det_bboxes
# Copyright (c) OpenMMLab. All rights reserved.

from typing import List, Optional, Union

import cv2
import numpy as np

from mmcv.image import imread, imwrite
from .color import Color, color_val

# a type alias declares the optional types of color argument
ColorType = Union[Color, str, tuple, int, np.ndarray]


def imshow_det_bboxes(
    img: Union[str, np.ndarray],
    bboxes: np.ndarray,
    labels: np.ndarray,
    class_names: List[str] = [],
    score_thr: float = 0,
    bbox_color: ColorType = "green",
    text_color: ColorType = "green",
    thickness: int = 1,
    font_scale: float = 1,
    out_file: Optional[str] = None,
    colors: np.ndarray = None,
):
    """Draw bboxes and class labels (with scores) on an image.

    Args:
        img (str or ndarray): The image to be displayed.
        bboxes (ndarray): Bounding boxes (with scores), shaped (n, 4) or
            (n, 5).
        labels (ndarray): Labels of bboxes.
        class_names (list[str]): Names of each classes.
        score_thr (float): Minimum score of bboxes to be shown.
        bbox_color (Color or str or tuple or int or ndarray): Color
            of bbox lines.
        text_color (Color or str or tuple or int or ndarray): Color
            of texts.
        thickness (int): Thickness of lines.
        font_scale (float): Font scales of texts.
        out_file (str or None): The filename to write the image.
        colors (array of tuple RGB int): the color of bbox and label of each class

    Returns:
        ndarray: The image with bboxes drawn on it.
    """
    assert bboxes.ndim == 2
    assert labels.ndim == 1
    assert bboxes.shape[0] == labels.shape[0]
    assert bboxes.shape[1] == 4 or bboxes.shape[1] == 5
    img = imread(img)

    if score_thr > 0:
        assert bboxes.shape[1] == 5
        scores = bboxes[:, -1]
        inds = scores > score_thr
        bboxes = bboxes[inds, :]
        labels = labels[inds]

    bbox_color = color_val(bbox_color)
    text_color = color_val(text_color)

    for bbox, label in zip(bboxes, labels):
        bbox_int = bbox.astype(np.int32)
        left_top = (bbox_int[0], bbox_int[1])
        right_bottom = (bbox_int[2], bbox_int[3])
        if colors is not None and len(colors) > 0:
            bbox_color = text_color = color_val(colors[label])
        cv2.rectangle(img, left_top, right_bottom, bbox_color, thickness=thickness)
        label_text = class_names[label] if class_names is not None else f"cls {label}"
        if len(bbox) > 4:
            label_text += f"|{bbox[-1]:.02f}"
        cv2.putText(
            img,
            label_text,
            (bbox_int[0], bbox_int[1] - 2),
            cv2.FONT_HERSHEY_TRIPLEX,
            font_scale,
            text_color,
            4,
        )

    if out_file is not None:
        imwrite(img, out_file)
    return img
