ARG PYTHON_VERSION=3.10-slim-bullseye

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /code

WORKDIR /code

RUN apt-get update && apt-get install -y nodejs npm

RUN apt-get update \
    && apt-get install -y nginx \
    && apt-get install -y curl \
    && apt-get install -y procps \
    && apt-get install -y net-tools \
    && apt-get install -y nano \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
COPY nginx.conf /etc/nginx/nginx.conf

COPY requirements.txt /tmp/requirements.txt
RUN set -ex && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/

COPY package.json package-lock.json ./
RUN npm install
COPY . /code

RUN python manage.py collectstatic --noinput
RUN apt-get update && apt-get install -y build-essential

EXPOSE 8000

COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
