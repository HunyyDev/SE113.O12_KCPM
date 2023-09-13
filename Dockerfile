FROM python:3.8

COPY install_node.sh .

RUN chmod 777 install_node.sh 

RUN ./install_node.sh

#INSTALL NODEJS DEPENDENCIES
WORKDIR /app/server

COPY server/package*.json .

RUN npm ci --omit=dev

EXPOSE 3000

ENV NODE_ENV=production

#INSTALL PYTHON DEPENDENCIES
WORKDIR /app/worker

COPY worker/requirements.txt .

RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y libgl1

COPY ./worker/libs/image.py /usr/local/lib/python3.8/site-packages/mmcv/visualization/image.py

#COPY SORCE CODE
COPY server /app/server

COPY worker /app/worker/

#COPY START SCRIPT
WORKDIR /app

COPY start.sh .

RUN chmod 777 start.sh worker/start.sh server/start.sh

CMD [ "./start.sh" ]