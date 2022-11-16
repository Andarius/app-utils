FROM python:3.10-alpine

RUN apk --no-cache add git gettext openssh libressl coreutils && \
    addgroup user && \
    adduser -s /bin/bash -D -G user user && \
    cp /usr/bin/envsubst /usr/local/bin/envsubst && \
    cp /usr/bin/tee /usr/local/bin/tee

WORKDIR /scripts

ADD requirements.txt .

RUN  apk --no-cache add --virtual build-dependencies gcc make make musl-dev libffi-dev libressl-dev cargo && \
     pip install -r requirements.txt && \
     apk del build-dependencies && \
     rm requirements.txt

RUN mkdir /build /usr/host-bin && chown -R user:user /scripts /tmp /home/user

ADD app_utils/jobs/update_version.py .
#ADD icons.py .
#ADD crop.py .
ADD app/* app/
ADD bin bin/

WORKDIR /home/user

ENV PATH "$PATH:/scripts/bin"
#ENV BUILD_PATH="/home/user"

USER user

#ENTRYPOINT ["upload-android.sh"]
#CMD ["android"]
