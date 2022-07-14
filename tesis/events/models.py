# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.validators import MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


#----------------------------------------------------------------------------------------
#		Eventos
#----------------------------------------------------------------------------------------

# Todos los modelos tienen los campos por defecto de "date_time" y "image", ya que todos
# los eventos guardan al menos la fecha y hora del evento y la imagen capturada con la
# camara del exterior. Ademas todos los modelos se ordenan por fecha y hora en orden
# descendiente.

# Se almacenan los eventos de deteccion de movimiento en las cercanias de la puerta.
class Movement(models.Model):

	class Meta:
		ordering = ['-date_time']

	date_time 	= models.DateTimeField(_('Fecha y hora'))
	image		= models.ImageField(_('Imagen'))


# Se almacenan los eventos de toque de timbre mediante el pulsador que esta en el
# exterior.
class Button(models.Model):

	class Meta:
		ordering = ['-date_time']

	date_time 	= models.DateTimeField(_('Fecha y hora'))
	image		= models.ImageField(_('Imagen'))


# Eventos de acceso denegado, es decir, cuando se captura un codigo RFID de un llavero
# que no esta habilitado para el ingreso, ya sea un usuario sin registrar o uno registrado
# que se encuentre inactivo.
class DeniedAccess(models.Model):

	class Meta:
		ordering = ['-date_time']

	date_time 	= models.DateTimeField(_('Fecha y hora'))
	image		= models.ImageField(_('Imagen'))


# Eventos de apertura de puerta mediante la pagina, se almacena ademas quien fue el usuario
# que lo hizo. Este evento agrega ademas el usuario que lo ocasiono.
class WebOpenDoor(models.Model):

	class Meta:
		ordering = ['-date_time']

	date_time 	= models.DateTimeField(_('Fecha y hora'))
	user 		= models.ForeignKey('users.User', on_delete=models.CASCADE)
	image		= models.ImageField(_('Imagen'))

	# Funcion que devuelve el nombre del modelo.
	# Se utiliza para poder distinguir entre el modelo "PermittedAccess" cuando
	# se muestran todos los eventos del usuario.
	def get_name(self):
		return 'WebOpenDoor'


# Eventos de acceso con llavero de un usuario registrado activo. Este evento agrega ademas
# el usuario que lo ocasiono.
class PermittedAccess(models.Model):

	class Meta:
		ordering = ['-date_time']

	date_time 	= models.DateTimeField(_('Fecha y hora'))
	user		= models.ForeignKey('users.User', on_delete=models.CASCADE)
	image		= models.ImageField(_('Imagen'))

	# Funcion que devuelve el nombre del modelo.
	# Se utiliza para poder distinguir entre el modelo "WebOpenDoor" cuando
	# se muestran todos los eventos del usuario.
	def get_name(self):
		return 'PermittedAccess'

#----------------------------------------------------------------------------------------



#----------------------------------------------------------------------------------------
#		Herramientas
#----------------------------------------------------------------------------------------

# Franja horaria del sensor de movimiento.
class MovementTimeZone(models.Model):

	# Horario del principio de la franja.
	begin 		= models.TimeField(_('Hora de inicio'))
	# Horario de finalizacion de franja.
	end			= models.TimeField(_('Hora de finalización'))

	# Direccion url de retorno, se utiliza para cuando se crea la franja.
	def get_absolute_url(self):
		return reverse('events:movement_time_zone', kwargs={'pk':1})


# Duracion de conservacion de eventos. Se especifican los años y meses que los
# eventos quedan guardados, pasado el lapso se van borrando diariamente.
class EventsDuration(models.Model):

	# Lista de dos elementos que muestra los posibles años a elegir.
	# En la primer columna van los datos a almacenarse y en la segunda los datos
	# a mostrar al usuario.
	YEARS_CHOICES = (
		(0, '0'),
		(1, '1'),
		(2, '2'),
		(3, '3'),
		(4, '4'),
		(5, '5'),
		(6, '6'),
	)
	# Similar al caso anterior pero con los meses.
	MONTHS_CHOICES = (
		(0, '0'),
		(1, '1'),
		(2, '2'),
		(3, '3'),
		(4, '4'),
		(5, '5'),
		(6, '6'),
		(7, '7'),
		(8, '8'),
		(9, '9'),
		(10, '10'),
		(11, '11'),
	)
	# Año/s.
	year		= models.PositiveSmallIntegerField(_('Año/s'),
		choices=YEARS_CHOICES,
		default=3)
	# Mes/es.
	month		= models.PositiveSmallIntegerField(_('Mes/es'),
		choices=MONTHS_CHOICES,
		default=0)

	# Direccion url de retorno, se utiliza para cuando se edita el modelo.
	def get_absolute_url(self):
		return reverse('events:events_duration', kwargs={'pk':1})

#----------------------------------------------------------------------------------------