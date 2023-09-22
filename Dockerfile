FROM python:3.8

#INSTALL & MODIFY DEPENDENCIES 
WORKDIR /app

COPY src/requirements.txt .

RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y libgl1 ffmpeg

COPY ./src/libs/image.py /usr/local/lib/python3.8/site-packages/mmcv/visualization/image.py

#COPY SORCE CODE
COPY src /app

EXPOSE 3000

CMD [ "uvicorn", "main:app", "--host" ,"0.0.0.0" ,"--port", "3000"]