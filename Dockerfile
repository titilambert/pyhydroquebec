FROM python:3.6-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN ["chmod", "+x", "./entrypoint.sh"]

RUN python setup.py install

CMD [ "./entrypoint.sh" ]