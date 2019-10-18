FROM python:3.7-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY docker/mqtt/entrypoint.sh .

COPY . .

RUN ["chmod", "+x", "./entrypoint.sh"]

RUN python setup.py install

CMD [ "./entrypoint.sh" ]
