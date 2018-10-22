FROM alpine:3.8

RUN apk --no-cache add git python3 py3-pip

COPY requirements.txt /app/requirements.txt

RUN apk add --no-cache --virtual .build-deps gcc musl-dev openssl-dev python3-dev py3-pip libffi-dev && \
    pip3 install -r /app/requirements.txt                                                            && \
    apk del .build-deps                                                                              && \
    pip3 uninstall -y pip                                                                            && \
    rm -rf /usr/lib/python3.6/site-packages/setuptools                                               && \
    find /usr/lib/python3.6 -type d -name "__pycache__" -exec rm -rf "{}" \; || true

COPY . /app/

CMD python3 /app/readinglist.py