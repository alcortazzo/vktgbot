FROM python:3.10-alpine
WORKDIR /code

COPY requirements.txt ./

RUN apk update &&\
    apk add --no-cache --virtual .build-deps \
    build-base \
    gcc &&\
    pip install --user -r requirements.txt &&\
    apk del .build-deps &&\
    rm -rf /root/* /tmp/*

COPY . .
ADD vktgbot .

CMD [ "python", "vktgbot" ]
