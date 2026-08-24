# This image is from python:3.14.7-slim-trixie (https://hub.docker.com/_/python)
FROM python@sha256:4fad23465a06cc5149a541fbec6f87e234a64dc0550f6bfdd2d290d8f03240df

WORKDIR /app

COPY requirements.txt ./

COPY ethstaker_deposit ./ethstaker_deposit

RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3", "-m", "ethstaker_deposit" ]
