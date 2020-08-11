FROM python:3.8-alpine

RUN apk --no-cache add git && \
    addgroup user && \
    adduser -s /bin/bash -D -G user user

WORKDIR /scripts

ADD requirements.txt .

RUN  apk --no-cache add --virtual build-dependencies gcc make make musl-dev libffi-dev libressl-dev && \
     pip install -r requirements.txt && \
     apk del build-dependencies && \
     rm requirements.txt

RUN mkdir /build /usr/host-bin && chown -R user:user /scripts /tmp

ADD update_version.py .
ADD app/* app/
ADD bin bin/

WORKDIR /home/user

ENV PATH "$PATH:/scripts/bin"
#ENV BUILD_PATH="/home/user"

USER user

#ENTRYPOINT ["upload-android.sh"]
#CMD ["android"]