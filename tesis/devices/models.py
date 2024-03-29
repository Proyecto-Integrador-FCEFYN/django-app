from django.db import models
from django.core import validators
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from cryptographic_fields.fields import EncryptedCharField
from django.utils.translation import gettext_lazy as _
# from djongo import models
# from django.contrib.postgres.fields import ArrayField

import re

#----------------------------------------------------------------------------------------
#		Dispositivos
#----------------------------------------------------------------------------------------
# Se almacenan los dispositivos.
class Device(models.Model):

	device_name 		= models.CharField(_('Nombre'), max_length=50)
	ip_address 	= models.CharField(_('Dirección IP u hostname'), max_length=50)
	port 		= models.CharField(_('Puerto'), max_length=5,
		# Este validador asegura que el campo contenga numeros unicamente.
		validators=[
			validators.RegexValidator(re.compile('^[0-9]*$'),
				_('Ingrese un número de puerto válido.'))
		])
	MAC_address		= models.CharField(_('Dirección MAC'), max_length=50, unique=True,
		validators=[
			validators.RegexValidator(re.compile('^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'),
				_('Ingrese una dirección MAC válida.'))
		],
		error_messages={
			'unique': _("Ya existe un dispositivo con esa dirección MAC."),
		})
	type = models.CharField(_('Tipo de dispositivo'), max_length=10)
	category_list = models.ManyToManyField('users.Category', blank=True, related_name="device_category_list", verbose_name='Categoria')
	last_ping = models.DateTimeField(_('Fecha y hora de último ping'))
	cert = models.TextField(_('Certificado'), max_length=4096)
	usuario = models.CharField(_('Usuario Autenticación'), max_length=50, default='')
	password = EncryptedCharField(_('Password Autenticación'), max_length=8, default='', blank=True)

	# def get_name(self):
	# 	return 'Device'
	def __str__(self):
		return str(self.device_name)

	# Direccion url de retorno, se utiliza para cuando se edita el modelo.
	def get_absolute_url(self):
		# return reverse('devices:devices_list', kwargs={'pk':1})
		return reverse('devices:device_list')

#-------
