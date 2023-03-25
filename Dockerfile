FROM python:3.8-bullseye

LABEL maintainer="enzo.candotti@mi.unc.edu.ar"

RUN mkdir "/app"

COPY ./tesis/requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

RUN sed -i '151s/.$//' /usr/local/lib/python3.8/site-packages/django/contrib/admin/widgets.py
RUN sed -i "261s/'%s__iexact' % UserModel.get_email_field_name()/'email'/" /usr/local/lib/python3.8/site-packages/django/contrib/auth/forms.py

COPY ./tesis /app

RUN curl -LJO https://raw.githubusercontent.com/Proyecto-Integrador-FCEFYN/nginx-config-files/master/RootCA.pem
RUN pwd
RUN ls
ENV API_CERT_PATH=/app/RootCA.pem

EXPOSE 80 443 27017

# Este anda
CMD gunicorn tesis.wsgi:application --bind 0.0.0.0:8000
