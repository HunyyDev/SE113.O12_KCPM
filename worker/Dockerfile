FROM python:3.8

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install libgl1 -y

COPY libs/image.py /usr/local/lib/python3.8/site-packages/mmcv/visualization/image.py

COPY . .

EXPOSE 5555

CMD [ "python3", "worker.py" ]