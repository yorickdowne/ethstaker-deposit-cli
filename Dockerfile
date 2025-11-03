# This image is from python:3.12.9-slim-bookworm (https://hub.docker.com/_/python)
FROM python@sha256:934873f1360893d07afe0d25b99af46640e916a5900f1677fb86e41f73920253

WORKDIR /app

COPY requirements.txt ./

COPY ethstaker_deposit ./ethstaker_deposit

RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3", "-m", "ethstaker_deposit" ]
