FROM python:3.8

#CREATE A USER
RUN useradd -m -u 1000 user

USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

RUN pip install --no-cache-dir --upgrade pip

#COPY SOURCE CODE
WORKDIR ${HOME}/app

COPY --chown=user ./app/requirements.txt ./app/requirements.txt

RUN pip install -r ./app/requirements.txt

COPY --chown=user . .

EXPOSE 3000

CMD [ "uvicorn", "app.main:app", "--host" ,"0.0.0.0" ,"--port", "3000"]