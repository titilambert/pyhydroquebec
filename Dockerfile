FROM python:3.7-alpine

RUN apk add --no-cache gcc musl-dev tzdata

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install -r requirements.txt --force-reinstall --no-cache-dir

COPY ./entrypoint.sh .

COPY . .

RUN ["chmod", "+x", "./entrypoint.sh"]

RUN python setup.py install

CMD [ "./entrypoint.sh" ]
