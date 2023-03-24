FROM python:3.8-buster

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir /clockwork_api
WORKDIR /clockwork_api

RUN apt-get update
RUN apt-get install -y default-libmysqlclient-dev apt-transport-https ca-certificates wget dirmngr gnupg software-properties-common

# Install JAVA 8
RUN wget -qO - https://adoptopenjdk.jfrog.io/adoptopenjdk/api/gpg/key/public | apt-key add -
RUN add-apt-repository --yes https://adoptopenjdk.jfrog.io/adoptopenjdk/deb/
RUN apt-get update
RUN apt-get install -y adoptopenjdk-8-hotspot


RUN pip install pip -U
ADD requirements.txt /clockwork_api/
RUN pip install gunicorn && pip install --no-cache-dir -r requirements.txt