FROM python:3.8

#INSTALL PYTHON DEPENDENCIES
WORKDIR /app

COPY src/requirements.txt .

RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y libgl1

COPY ./src/libs/image.py /usr/local/lib/python3.8/site-packages/mmcv/visualization/image.py

#COPY SORCE CODE
COPY src /app

EXPOSE 3000

CMD [ "gunicorn", "-b", "0.0.0.0:3000", "main:app" ]