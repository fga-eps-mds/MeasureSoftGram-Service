FROM python:3.10-buster

ENV PYTHONUNBUFFERED 1

EXPOSE 80
EXPOSE 8181

RUN mkdir /src
WORKDIR /src
COPY src /src

# RUN pip3 install --upgrade pip==21.* && \
#     pip3 install -r requirements.txt &&


CMD [ "/usr/bin/python3", "manage.py", "runserver", "0.0.0.0:80" ]
