FROM python:3-slim

COPY . /data-transfer
WORKDIR /data-transfer

RUN pip3 install -e . -r requirements.txt

# Create user and change folder permissions
RUN groupadd -r datatransfer && useradd --no-log-init -r -g datatransfer datatransfer && \
    chown -R datatransfer:datatransfer /data-transfer

ENV PYTHONPATH /data-transfer

ENTRYPOINT [ "bin/data-transfer" ]
