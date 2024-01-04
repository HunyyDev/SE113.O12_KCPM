#!/bin/bash

cd "$(dirname "$0")"

EXPECTED_CHECKSUM="1282ca01d9dd18fa3632eb6ea27fbfe6"
ACTUAL_CHECKSUM=$(md5sum best20231112.onnx | awk '{print $1}')

if [ "$ACTUAL_CHECKSUM" != "$EXPECTED_CHECKSUM" ]; then
    echo "Checksum mismatch, downloading model"
    if [ -n "$MODEL_URL" ]; then
        echo "Downloading model"
        wget -O best20231112.onnx $MODEL_URL
        exit 0
    else
        echo "ERROR: MODEL_URL not set"
        exit 1
    fi
else
    echo "Model already downloaded"
    exit 0
fi
