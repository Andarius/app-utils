FROM python:3.10-alpine

RUN apk --no-cache add bash cairo && \
    addgroup user && \
    adduser -s /bin/bash -D -G user user

WORKDIR /app

ADD requirements.txt .

RUN  apk --no-cache add --virtual build-dependencies gcc make make musl-dev libffi-dev libressl-dev cargo && \
     pip install -r requirements.txt && \
     apk del build-dependencies && \
     rm requirements.txt

ADD app_utils/ /app/app_utils
ADD run.py /app

USER user

ENTRYPOINT ["python", "run.py"]
