FROM ubuntu:22.04

WORKDIR /app

COPY . /app

RUN apt update && apt upgrade -y

RUN apt install -y python3 python3-pip 

RUN pip3 install --no-cache --upgrade pip setuptools Django==4.2 pymongo

RUN ls

EXPOSE 8080:8080 

CMD python3 manage.py runserver
