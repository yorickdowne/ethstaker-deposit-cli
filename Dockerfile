# This image is from python:3.14-slim-trixie (https://hub.docker.com/_/python)
FROM python@sha256:be8ccd085666c34273c9dc5607c9842f8b2e3116128aae45148ce164c07ce09d

WORKDIR /app

COPY requirements.txt ./

COPY ethstaker_deposit ./ethstaker_deposit

RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3", "-m", "ethstaker_deposit" ]
