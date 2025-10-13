FROM alpine:latest

ENV RESTORE=false
ENV ARCHIVE_FILE=""

ENV DEV_PACKAGES="gcc libc-dev libffi-dev py3-pip python3-dev"
ENV PACKAGES="bash ca-certificates py3-cffi py3-cryptography py3-six py3-packaging"

WORKDIR /opt/grafana-backup-tool

ADD . /opt/grafana-backup-tool

# Use Python venv
RUN apk add --no-cache ${DEV_PACKAGES} ${PACKAGES} \
    && python3 -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install --no-cache-dir . \
    && chmod -R a+r /opt/grafana-backup-tool \
    && find /opt/grafana-backup-tool -type d -print0 | xargs -0 chmod a+rx \
    && chown -R 1337:1337 /opt/grafana-backup-tool \
    && apk del ${DEV_PACKAGES}

USER 1337

CMD sh -c '. /opt/venv/bin/activate && if [ "$RESTORE" = "true" ]; then \
    if [ ! -z "$AWS_S3_BUCKET_NAME" ] || [ ! -z "$AZURE_STORAGE_CONTAINER_NAME" ] || [ ! -z "$GCS_BUCKET_NAME" ]; then \
        grafana-backup restore $ARCHIVE_FILE; \
    else \
        grafana-backup restore _OUTPUT_/$ARCHIVE_FILE; \
    fi \
else \
    grafana-backup save; \
fi'
