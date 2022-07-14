# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import AbstractBaseUser, UserManager
from django.core import validators
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

import re



# Modelo de los datos de usuario. Se implementa de la clase AbstractBaseUser y
# tambien de PermissionsMixin para poder utilizar los metodos mandatorios por
# el modulo Admin.
class User(AbstractBaseUser):

	class Meta:
		# Se ordenan los usuarios del mas recientemente al mas antiguamente
		# creado.
		ordering = ["-date_joined"]

	# Todos los campos son por defecto "blank=False", o sea que no pueden
	# estar en blanco, tienen que completarse con un dato valido.
	first_name 		= models.CharField(_('Nombre'), max_length=50)
	last_name 		= models.CharField(_('Apellido'), max_length=50)
	# Este campo es el utilizado como identificador del usuario, por lo que
	# al utilizar el backend de autorizacion por defecto, debe ser unico
	# (unique=True).
	email 			= models.EmailField(_('Email'), max_length=50, unique=True,
		error_messages={
			'unique': _("Ya existe un usuario con ese email."),
		})
	identity 		= models.CharField(_('DNI'), max_length=8, unique=True,
		# Este validador asegura que el campo contenga numeros unicamente.
		validators=[
			validators.RegexValidator(re.compile('^[0-9]*$'),
				_('Ingrese un documento válido (números únicamente).'))
		],
		error_messages={
			'unique': _("Ya existe un usuario con ese DNI.")
		})
	phone 			= models.CharField(_('Número de teléfono'), max_length=20,
		# Este validador asegura que el campo contenga numeros y guiones unicamente.
		validators=[
			validators.RegexValidator(re.compile('^[0-9-]*$'),
				_('Ingrese un teléfono válido (números y guiones únicamente).'))
		])
	# Fecha de vencimiento de la cuenta del usuario, es decir que una vez llegada
	# esta fecha, el programa principal pone el campo "is_active" en "False",
	# impidiendo que el usuario continue utilizando el sistema.
	expiration_date = models.DateField(_('Fecha de finalización'),
		help_text=_('Una vez llegado el día, se da de baja el usuario.'), default=timezone.now)
	# Cabe aclarar que se opta por incluir los dias de la semana en el modelo de
	# usuario debido a que no se brinda la posibilidad de modificacion de dichos
	# dias, lo ideal seria realizar otro modelo que contenga unicamente los dias,
	# y otro que conecte el usuario, con una franja y con un cierto dia.
	#
	# Los dias de la semana los cuales contienen la clave foranea a cierta franja
	# horaria. El atributo "related_name" es debido a las multiples claves a un
	# mismo modelo, es una forma de que el Django pueda diferenciarlos (necesario).
	# El atributo "verbose_name" es el titulo con el cual figura en la pagina, no
	# se puede especificar como los otros campos, debido a que las claves foraneas
	# son casos especiales. Estos campos en los modelos, se comportan como campos
	# de eleccion en la pagina, es decir que permite elegir la franja horaria.
	# Se pone por defecto el primer turno, que corresponde a "Ninguno".
	# En caso de eliminar cierta franja que ya estaba establecida en cierto dia
	# del usuario, se establece como franja la que esta por defecto ("Ninguno").
	monday 			= models.ForeignKey('users.TimeZone',
		on_delete=models.SET_DEFAULT, related_name='monday', verbose_name='Lunes',
		default=1)
	tuesday 		= models.ForeignKey('users.TimeZone',
		on_delete=models.SET_DEFAULT, related_name='tuedsay', verbose_name='Martes',
		default=1)
	wednesday 		= models.ForeignKey('users.TimeZone',
		on_delete=models.SET_DEFAULT, related_name='wendesday', verbose_name='Miércoles',
		default=1)
	thursday 		= models.ForeignKey('users.TimeZone',
		on_delete=models.SET_DEFAULT, related_name='thursday', verbose_name='Jueves',
		default=1)
	friday 			= models.ForeignKey('users.TimeZone',
		on_delete=models.SET_DEFAULT, related_name='friday', verbose_name='Viernes',
		default=1)
	saturday		= models.ForeignKey('users.TimeZone',
		on_delete=models.SET_DEFAULT, related_name='saturday', verbose_name='Sábado',
		default=1)
	sunday			= models.ForeignKey('users.TimeZone',
		on_delete=models.SET_DEFAULT, related_name='sunday', verbose_name='Domingo',
		default=1)
	# Este campo es el codigo de la tarjeta RFID. Se lo va a asignar via socket
	# con el programa principal.
	code 			= models.CharField(_('Código'), max_length=10, default='',
		# Este validador asegura que el codigo este compuesto por numeros 
		# hexadecimales unicamente.
		validators=[
			validators.RegexValidator(re.compile('^[0-9A-Fa-f]*$'),
				_('Código de tarjeta inválido (números hexadecimales únicamente).'))
		])
	# Este campo divide entre profesores ("is_staff=True") y alumnos (is_staff="False").
	is_staff 		= models.BooleanField(_('Administrador'), default=False,
		help_text=_('Determina si el usuario tiene permisos para administrar el sitio'
				' (no posee franjas horarias).'))
	# Este campo el manejador lo pone por defecto en "True".
	is_active 		= models.BooleanField(_('Activo'), default=True,
		help_text=_('Determina si el usuario puede utilizar el sistema o no.'))
	# Este campo indica la fecha y la hora de creacion del usuario.
	date_joined 	= models.DateTimeField(_('Fecha y hora de registro'), default=timezone.now)

	# El manejador de la creacion de usuarios, no es necesario crear uno propio ya que con el
	# "UserManager" que esta por defecto es suficiente. Pone al usuario en activo al
	# crearlo (is_active=True).
	objects 		= UserManager()

	# Se especifica cual campo va a ser el email del usuario, en este caso coincide con el
	# identificador del mismo.
	EMAIL_FIELD 	= 'email'
	# Se especifica cual campo va a ser el identificador del usuario.
	USERNAME_FIELD 	= 'email'
	# Campos requeridos en la creacion de un superusuario por consola (no se utiliza).
	REQUIRED_FIELDS = []

	# Funcion de implementacion necesaria.
	# Devuelve el nombre con el apellido separado por un espacio entremedio.
	def get_full_name(self):
		full_name = '%s %s' % (self.first_name, self.last_name)
		return full_name.strip()

	# Funcion de implementacion necesaria.
	# Devuelve el nombre.
	def get_short_name(self):
		return self.first_name

	# Funcion de implementacion necesaria.
	# Devuelve el apellido.
	def get_last_name(self):
		return self.last_name

	# Esta funcion es utilizada para lograr utilizar el sistema admin por defecto de Django (/admin).
	# Devuelte si el usuario tiene permiso especifico, se devuelve siempre "True".
	def has_perm(self,perm,obj=None):
		return True

	# Esta funcion es utilizada para lograr utilizar el sistema admin por defecto de Django (/admin).
	# Devuelve si el usuario tiene permiso para una aplicacion especifica, se devuelve siempre "True".
	def has_module_perms(self,app_label):
		return True

	# Direccion url de retorno, se utiliza para cuando se edita
	# el usuario, una vez finalizado se va al perfil del mismo,
	# es por esto que se pasa como parametro "kwargs" la clave
	# principal ("pk").
	def get_absolute_url(self):
		return reverse('users:user_detail', kwargs={'pk': self.pk})


# Modelo para las franjas horarias, contiene unicamente el nombre de la franja
# junto a los horarios de inicio y finalizacion de la misma.
class TimeZone(models.Model):

	# Nombre de la franja
	zone_name		= models.CharField(_('Turno'), max_length=20)
	# Horario de principio de franja.
	begin			= models.TimeField(_('Hora de inicio'))
	# Horario de finalizacion de franja.
	end 			= models.TimeField(_('Hora de finalización'))

	# En caso de no especificar algun campo del objecto, por defecto
	# se obtiene el nombre de la franja.
	def __unicode__(self):
		return self.zone_name

	# Direccion url de retorno, se utiliza para cuando se edita
	# o crea la franja.
	def get_absolute_url(self):
		return reverse('users:time_zone_list')


# Modelo para las sesiones de los usuarios. Almacena la clave de un usuario junto
# a la llave de la sesion, la cual se genera cada vez que un usuario se loguea.
class Visitor(models.Model):

	# Clave primaria de un usuario.
	user = models.OneToOneField('users.User', null=False, related_name='visitor', on_delete=models.CASCADE)
	# Llave de la sesion.
	session_key = models.CharField(null=False, max_length=40)
