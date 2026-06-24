FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /app

WORKDIR /app

RUN apt-get update
RUN apt-get install -y gcc libpq-dev

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./app ./app

RUN mkdir -p /app/uploads

EXPOSE 8000
