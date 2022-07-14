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

Si al correr makemigratinos, migrate o runserver aparece un error como el siguiente:

  File "/home/ecandott/Documentos/tesis/resiale/miprueba/tesis/tesis_django/lib/python3.8/site-packages/django/contrib/admin/widgets.py", line 151
    '%s=%s' % (k, v) for k, v in params.items(),
    
 se debe eliminar la última coma en /tesis_django/lib/python3.8/site-packages/django/contrib/admin/widgets.py linea 151
 
