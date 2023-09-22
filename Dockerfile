FROM python:3.8

#CREATE A USER
RUN useradd -m -u 1000 user

RUN apt-get update && apt-get install -y libgl1 ffmpeg

USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

RUN pip install --no-cache-dir --upgrade pip

#INSTALL & MODIFY DEPENDENCIES 
WORKDIR ${HOME}/app

COPY --chown=user src/requirements.txt .

RUN pip install -r requirements.txt

COPY ./src/libs/image.py /home/user/.local/lib/python3.8/site-packages/mmcv/visualization/image.py

#COPY SORCE CODE
COPY --chown=user src .

EXPOSE 3000

CMD [ "uvicorn", "main:app", "--host" ,"0.0.0.0" ,"--port", "3000"]