FROM python:3.10-buster

ENV PYTHONUNBUFFERED 1

EXPOSE 80
EXPOSE 8181

RUN mkdir /src
COPY src /src
COPY requirements.txt /src
WORKDIR /src

RUN pip install -r requirements.txt
