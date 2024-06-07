FROM python:alpine3.19

WORKDIR /app

COPY requirements.txt ./

COPY ethstaker_deposit ./ethstaker_deposit

RUN apk add --update gcc libc-dev linux-headers

RUN pip3 install -r requirements.txt

ARG cli_command

ENTRYPOINT [ "python3", "-m", "ethstaker_deposit" ]

CMD [ $cli_command ]
