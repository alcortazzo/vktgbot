FROM python:3.11-alpine
WORKDIR /code

COPY ./requirements.txt ./

RUN apk update &&\
    apk add --no-cache --virtual .build-deps build-base &&\
    pip install --user -r requirements.txt &&\
    apk del .build-deps &&\
    rm -rf /root/* /tmp/*

COPY ./vktgbot ./vktgbot

CMD python -m vktgbot
