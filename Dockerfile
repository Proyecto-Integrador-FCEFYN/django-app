FROM python:3.8-bullseye

LABEL maintainer="enzo.candotti@mi.unc.edu.ar"

RUN mkdir "/app"

COPY ./tesis/requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

RUN sed -i '151s/.$//' /usr/local/lib/python3.8/site-packages/django/contrib/admin/widgets.py

COPY ./tesis /app

# Este anda
CMD gunicorn tesis.wsgi:application --bind 0.0.0.0:8000
