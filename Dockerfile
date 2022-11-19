FROM andarius/python:3.10-poetry as builder

COPY pyproject.toml poetry.lock ./
RUN  apk --no-cache add --virtual build-dependencies gcc make make musl-dev libffi-dev libressl-dev cargo && \
     poetry export -f requirements.txt --output requirements.txt "--without-hashes" && \
     pip install -r requirements.txt --target=/python-libs && \
     ls -alh /python-libs && \
     apk del build-dependencies && \
     rm requirements.txt


FROM python:3.10-alpine

RUN apk --no-cache add bash cairo && \
    addgroup user && \
    adduser -s /bin/bash -D -G user user

WORKDIR /app

ADD app_utils/ /app/app_utils
ADD run.py /app

COPY --from=builder /python-libs /home/user/.local/lib/python3.10/site-packages/

RUN chown user:user -R /home/user/

USER user

ENTRYPOINT ["python", "run.py"]
