FROM python:3.7-alpine
RUN apk add --no-cache gcc musl-dev
COPY requirements.txt ./
RUN pip install -r requirements.txt --force-reinstall --no-cache-dir  --user
COPY . .
RUN python setup.py install --user

FROM python:3.7-alpine
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY --chown=appuser:appgroup --from=0 /root/.local/ /home/appuser/.local/

WORKDIR /usr/src/app
COPY --chown=appuser:appgroup ./entrypoint.sh .
RUN mkdir -p /usr/src/app && \
    chown -R appuser:appgroup /home/appuser /usr/src/app

USER appuser
RUN chmod +x ./entrypoint.sh
CMD [ "./entrypoint.sh" ]
