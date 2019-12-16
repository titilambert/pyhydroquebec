FROM python:3.7.5-alpine

RUN mkdir -p /usr/pyhydroquebec

RUN mkdir -p /usr/pyhydroquebec/config

WORKDIR /usr/pyhydroquebec

COPY . ./

RUN ls -a config/

RUN apk add --no-cache gcc musl-dev rsync

RUN pip install -r requirements.txt --force-reinstall --no-cache-dir

RUN python setup.py install

RUN chmod +x ./entrypoint.sh

ENV PYHQ_OUTPUT MQTT

ENV CONFIG /usr/pyhydroquebec/config/config.yaml

CMD ./entrypoint.sh
