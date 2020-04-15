
FROM python:3.7.5-alpine3.10
LABEL maintainer="raviteja.nandimandal@sungardas.com"
RUN mkdir -p /sutas
COPY . /sutas
WORKDIR /sutas
RUN apk add --no-cache build-base \
        libressl-dev \
        musl-dev \
        libffi-dev \
        postgresql-dev
RUN dos2unix lib/sutas.py
RUN python setup.py install
RUN dos2unix sutas_test.py
RUN chmod +x sutas_test.py
