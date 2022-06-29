# django-app
Aplicación de Django recuperada del proyecto integrador anterior. Se adaptará y modificará para aplicarlo al proyecto actual.


## Pasos de instalación

virtualenv tesis_django
. tesis_django/bin/activate
sudo apt update
pip install bootstrap4
pip install Django==1.11.9
pip install django-bootstrap4==0.0.4
python manage.py makemigrations
pip install Pillow
python manage.py makemigrations
python manage.py migrate
python manage.py runserver

Para acceder a la base:
sqlite3 db.sqlite3
