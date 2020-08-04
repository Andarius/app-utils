FROM python:3.8-alpine

RUN apk --no-cache add bash gettext && \
    cp /usr/bin/envsubst /usr/local/bin/envsubst && \
    addgroup user && \
    adduser -s /bin/bash -D -G user user

WORKDIR /app

ADD requirements.txt /app
RUN pip install -r requirements.txt && rm requirements.txt

RUN chown -R user:user /app

ADD app app/

USER user