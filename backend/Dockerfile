# syntax = docker/dockerfile:1.2
FROM python:3.7-alpine
EXPOSE 5000

# Set up base platform
ENV LC_CTYPE=C.UTF-8
RUN set -x && apk add --update --no-cache curl

# Install python environment
RUN --mount=type=cache,target=/root/.cache \
  pip install --upgrade pip setuptools
WORKDIR /app
COPY ./ckan-xsearch/requirements.txt /app/
RUN --mount=type=cache,target=/root/.cache \
  pip install -r requirements.txt

# Set up Django application
ENV XCKAN_DB_ENGINE=django.db.backends.sqlite3 \
  XCKAN_DB_NAME=/ext/xckan.sq3 \
  XCKAN_ALLOWED_HOSTS=localhost \
  XCKAN_CACHEDIR=/ext/cache \
  XCKAN_LOGFILE=/ext/xckan.log \
  XCKAN_QUERYLOGDIR=/ext/query_log \
  XCKAN_SOLR=http://solr:8983/solr/ckan-xsearch

ARG DJANGO_SUPERUSER_USERNAME=xckan \
  DJANGO_SUPERUSER_PASSWORD=xckan \
  DJANGO_SUPERUSER_EMAIL=xckan@example.com
ENV DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME} \
  DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD} \
  DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL}

# Prepare source codes
COPY . /app/

# Run script
WORKDIR /app/ckan-xsearch/django-backend
COPY entrypoint.sh /tmp
ENTRYPOINT ["/bin/sh", "/tmp/entrypoint.sh"]
