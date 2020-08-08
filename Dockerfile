FROM python:3.8-alpine

RUN apk --no-cache add bash yarn git openjdk11 && \
    addgroup user && \
    adduser -s /bin/bash -D -G user user

WORKDIR /build

ADD requirements.txt .

RUN pip install -r requirements.txt && rm requirements.txt

RUN chown -R user:user /build /tmp

ADD update_version.py .
ADD app/* app/
ADD bin bin/

USER user

ENTRYPOINT ["bin/build.sh"]
CMD ["android"]
