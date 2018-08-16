FROM python:3-slim

COPY . /data-transfer
WORKDIR /data-transfer

RUN pip3 install -e . -r requirements.txt

# Create user and change folder permissions
RUN groupadd -r datatransfer && useradd -r -g datatransfer -u 1000 datatransfer && \
    chown -R datatransfer:datatransfer /data-transfer

USER 1000 

ENV PYTHONPATH /data-transfer

ENTRYPOINT [ "bin/data-transfer" ]
