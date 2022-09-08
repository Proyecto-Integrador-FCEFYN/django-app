# -*- coding: utf-8 -*-
from __future__ import unicode_literals
# Se importa el archivo de configuracion del proyecto para utilizar la variable
# que contiene el path absoluto del mismo en caso de realizar el backup.
from django.conf import settings
# Agregados a las vistas para mayor control, como requerimiento de logueo
# y comprobacion de que el usuario sea admin.
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
# Para crear el "ModelForm" dado un modelo. Se utiliza para agregar widgets
# en la vista de edicion de la franja horaria del sensor de movimiento.
from django.forms.models import modelform_factory
# Para el manejo de las respuestas a los pedidos.
from django.http import HttpResponseRedirect, HttpResponse
# Para renderizar un template rapidamente.
from django.shortcuts import render
# Para redireccionar a una URL.
from django.urls import reverse
# Vista generica a la que hay que definir el manejo completo de los pedidos.
from django.views import View
# Vistas genericas para mostrar informacion de los modelos.
from django.views.generic import TemplateView, ListView, RedirectView
# Vista generica para actualizar campos de los modelos.
from django.views.generic.edit import UpdateView
from pymongo import MongoClient
import bson, sys, os, os.path
import paho.mqtt.publish as publish

# Se importan los modelos de esta aplicacion, que consisten en los eventos.
from .models import *
# Se importan las funciones creadas para esta aplicacion.
from .utils import *

# Se importa el formulario de la aplicacion "users" para el manejo del widget
# del selector de tiempo.
from users.forms import TimeInput
# Se importan los modelos de la aplicacion "users". "TimeZone" para 
# la creacion de las franjas horarias por defecto, al inicializar el sistema.
# Y "User" para manipular datos de los usuarios.
from users.models import TimeZone, User
# Se importa la vista de la aplicacion "users" para la verificacion
# de que el usuario sea admin, osea "is_staff=True".
from users.views import AdminTest

# Se importan estas dos herramientas para obtener una unica lista en caso
# de utilizar dos querysets.
from itertools import chain
from operator import attrgetter

# Para poner el filtro de eventos de usuarios en el dia actual y agregar al nombre del archivo
# de backup la fecha actual.
import datetime
# Para manipular paths en caso de realizar backups.
import os
# Para utilizar como buffer del archivo zip en caso de realizar backups.
from io import BytesIO

# Para crear el archivo zip en caso de realizar backups.
import zipfile
import logging
logger = logging.getLogger(__name__)



#----------------------------------------------------------------------------------------
#		Vistas habilitadas para usuario no admin
#----------------------------------------------------------------------------------------

# Vista inicial del sistema. Cuando se accede a la direccion IP de la placa, se
# verifica si existe algun usuario, en caso de ser cierto redirije a la pagina
# de inicio, y en caso contrario, redirije a la pagina de inicializacion del
# sistema.
class RootView(RedirectView):

	# Funcion que define a que URL redirigir el pedido.
	def get_redirect_url(self, **kwargs):
		# Si hay algun usuario.
		if User.objects.all():
			# Si el usuario se encuentra ya autenticado, significa que ya se
			# encontraba dentro del sitio y cerro la pagina, pero su cuenta
			# sigue todavia activa gracias al sistema de sesiones, por
			# lo que si pretende ingresar nuevamente, no es necesario que
			# se loguee y pasa directamente a la pagina de inicio.
			if self.request.user.is_authenticated:
				return reverse('devices:home')
			# Si el usuario todavia no se logueo, debe hacerlo primero para
			# acceder a la pagina de inicio.
			else:
				return reverse('users:login')
		# Si no existe usuario alguno.
		else:
			return reverse('events:initialize')


# Vista encargada de inicializar el sistema por primera vez. En caso de no existir
# usuario, crea uno por defecto y avisa de su existencia, para permitir que se
# ingrese al sistema con dicho usuario y sea capaz de crear el primer usuario
# mediante el uso del sistema.
class InitializeSystem(TemplateView):

	# El template a utilizar.
	template_name = 'events/init_system.html'

	# Funcion para obtener el contexto a mostrar en la pagina.
	def get_context_data(self):
		context = super(InitializeSystem, self).get_context_data()
		# Si ya existe algun usuario.
		if User.objects.all():
			context['init'] = False
		# Si todavia no se creo el usuario "admin".
		else:
			# Se crea el objecto usuario con los parametros especificados.
			user = User(email='admin@admin', is_staff=True)
			# Se genera una contraseña de numeros aleatorios.
			password = 'admin'
			# Se establece la nueva contraseña del usuario.
			user.set_password(password)
			# Se almacena efectivamente en la base de datos.
			user.save()
			# Se crean las franjas horarias por defecto ("Ninguno", "Mañana", "Tarde"
			# y "Mañana y tarde").
			franja = TimeZone(zone_name='Ninguno', begin='0:0', end='0:0')
			franja.save()
			franja = TimeZone(zone_name='Mañana', begin='8:0', end='13:0')
			franja.save()
			franja = TimeZone(zone_name='Tarde', begin='13:0', end='20:0')
			franja.save()
			franja = TimeZone(zone_name='Mañana y tarde', begin='8:0', end='20:0')
			franja.save()
			# Se crea la franja horaria por defecto del detector de movimiento.
			franja = MovementTimeZone(begin='22:00', end='8:00')
			franja.save()
			# Se establece la duracion de conservacion de los eventos por defecto.
			duration = EventsDuration(year=3, month=0)
			duration.save()
			# Se especifica el contexto a usar por el template.
			context['init'] = True
			context['user'] = user
			context['password'] = password
		return context


# Vista de inicio, en la cual se muestra el stream de la camara y se permite abrir la
# puerta.
# Cuando se solicita la pagina (get) se muestra solamente el template y cuando se
# presiona el boton de "Abrir puerta" se envia la clave (pk) del usuario al programa
# principal mediante socket.
class HomeView(LoginRequiredMixin, View):

	# Funcion que retorna la pagina a mostrar.
	def get(self,request):
		return render(request, 'events/home.html')

	# En caso de precionarse el boton de "Abrir puerta", se crea un socket INET de tipo 
	# STREAM y se conecta al servidor socket, el cual esta en el programa principal,
	# y se envia la clave primaria del usuario que presiono el boton para ser registrado
	# en la base de datos.
	def post(self, request):

		# El numero de placa deberia venir en un selector para elegir
		# por lo tanto deberia haber un registro de placas en la base
		device = 'placanro1'

		topic = f'{device}/boton'
		payload = str(request.user.pk)
		hostname = 'raspi'
		port = 1883
		auth={
			'username': "user",
			'password': "pass"
		}
		publish.single(topic=topic, payload=payload, hostname=hostname, port=port)

		# Se permanece en la misma pagina.
		return HttpResponseRedirect('/inicio')

#----------------------------------------------------------------------------------------



#----------------------------------------------------------------------------------------
#		Herramientas
#----------------------------------------------------------------------------------------

# Vista que permite modificar la franja horaria de la deteccion de movimiento.
class MovementTimeZoneView(AdminTest, UpdateView):

	# El modelo a utilizar.
	model = MovementTimeZone
	# El template a utilizar.
	template_name = 'events/movement_time_zone.html'
	# Se indica el formulario a utilizar.
	# Mediante el metodo "modelform_factory" se crea dicho formulario pasando
	# como parametros el modelo, los campos del mismo y se agregan los widgets
	# para seleecion de un dato de tipo tiempo.
	form_class = modelform_factory(MovementTimeZone,
		fields = [
			'begin',
			'end',
		],
		widgets={
			'begin': TimeInput,
			'end': TimeInput
		})
	# Se especifica el nombre del contexto a utilizar en el template. Este contexto
	# se utiliza para mostrar la franja horaria actual.
	context_object_name = 'movement_time_zone'


# Vista que permite cambiar el tiempo de conservacion de los eventos. El programa
# principal chequea diariamente la antiguedad de los eventos, una vez alcanzado
# este lapso establecido, los borra.
class EventsDurationView(AdminTest, UpdateView):

	# Modelo a utilizar.
	model = EventsDuration
	# Template a utilizar.
	template_name = 'events/events_duration.html'
	# Los campos del modelo a mostrar para su edicion (es obligatorio especificarlos).
	fields = [
		'year',
		'month',
	]
	# Se especifica el nombre del contexto a utilizar en el template. Este contexto
	# se utiliza para mostrar el intervalo actual.
	context_object_name = 'events_duration'


# Vista que muestra el estado del almacenamiento del sistema.
class StorageView(AdminTest, TemplateView):

	# El template a utilizar.
	template_name = 'events/storage.html'

	# Funcion para obtener el contexto a mostrar en la pagina.
	def get_context_data(self):
		context = super(StorageView, self).get_context_data()
		# Se obtiene la cantidad de bloques de datos del directorio raiz.
		storage = os.statvfs('/')
		# Se convierten los bloques totales a bytes
		total = storage.f_frsize * storage.f_blocks
		# Se convierten los bloques disponibles a bytes.
		free = storage.f_frsize * storage.f_bavail
		# Se obtiene el porcentaje de espacio utilizado para mostrar en la barra.
		used_percentage = int((total - free)/float(total)*100)
		# Se convierten los bytes a GB (redondeados).
		context['total'] = round(total/1024.0/1024.0/1024.0, 2)
		context['free'] = round(free/1024.0/1024.0/1024.0, 2)
		context['used_percentage'] = used_percentage
		return context

#----------------------------------------------------------------------------------------



#----------------------------------------------------------------------------------------
#		Eventos
#----------------------------------------------------------------------------------------

# Vista que muestra los eventos relacionados a un usuario, los cuales son de tipo
# "WebOpenDoor" y "PermittedAccess".
# Se brinda un filtro de tipo de eventos y fechas, donde se puede especificar
# que tipo de evento y en que intervalos de fechas se desea acotar la busqueda.
class UserEventView(AdminTest, View):

	# Funcion que retorna el template a mostrar cuando se visite por primera vez la
	# pagina, es decir, cuando se viene del perfil de usuario. Muestra por defecto
	# ambos eventos ordenados en orden descendiente por la fecha de la ocurrencia
	# de los mismos correspondientes al dia actual.
	def get(self, request, **kwargs):
		# Se obtiene la fecha del dia de hoy para filtrar todos los eventos en
		# un principio por el dia de hoy.
		begin = datetime.datetime.now().date().strftime('%Y-%m-%d')
		# Se obtiene el contexto para el template.
		context = self.get_context_data('all', begin, '', **kwargs)
		# Simplemente se retorna la pagin a mostrar
		return render(request, 'events/user_event_list.html', context)

	# Funcion que genera el contexto para el template. Recibe como parametros, el
	# tipo de evento ("event_type") y las fechas inicio y/o fin del intervalo de
	# busqueda.
	def get_context_data(self, event_type, begin, end, **kwargs):
		# Se obtiene el usuario del argumento "**kwargs", el cual es la clave principal
		# del mismo.
		user = User.objects.get(pk=self.kwargs['pk'])
		# Dependiendo del tipo de evento que se selecciona en el filtro, es el modelo
		# a utilizar en la funcion "get_event_context_for_filter".
		# Independientemente del tipo de evento, tambien se pasa como parametro a la
		# funcion "get_event_context_for_filter" el usuario, para que ademas de
		# filtrar por el intervalo de fechas, tambien lo haga con el usuario en
		# cuestion.
		#
		# En caso de seleccionar "Todos" se genera primero un contexto con un modelo,
		# se guarda la lista de los objectos ("object_list") del mismo y luego se
		# vuelve a generar el contexto pero para el segundo modelo. Finalmente
		# se ordenan ambas listas de objetos ("sorted") por el atributo "date_time"
		# en orden invertido ("reverse=True").
		if event_type == 'all':
			context = get_event_context_for_filter(begin, end, PermittedAccess, user)
			context_temp = context.get('object_list')
			context = get_event_context_for_filter(begin, end, WebOpenDoor, user)
			context['object_list'] = sorted(chain(context_temp, context.get('object_list')),
												key=attrgetter('date_time'),
												reverse=True)
		# En caso de seleccionar "Ingresos con llavero".
		elif event_type == 'key':
			context = get_event_context_for_filter(begin, end, PermittedAccess, user)
		# En caso de seleccionar "Aperturas de puerta via web".
		elif event_type == 'web':
			context = get_event_context_for_filter(begin, end, WebOpenDoor, user)
		# No hay otra opcion, por lo que no deberia de llegarse a esta instancia.
		else:
			context = None
		# Se agrega al contexto ya creado el tipo de evento que se selecciono, con el
		# fin de poder mostrar como opcion por defecto el evento ya seleccionado,
		# el nombre del usuario completo para nombrarlo en el titulo y la fecha
		# del dia de hoy convertida a string para indicar en la pagina si los
		# eventos mostrados se tratan del dia de hoy.
		context['event_selected'] = event_type
		context['user_name'] = user.get_full_name()
		context['date_today'] = datetime.datetime.now().date().strftime('%Y-%m-%d')
		return context

	# Funcion encargada de responder cuando se presiona el boton de "Filtrar".
	# Obtiene los valores ingresados en las fechas junto al evento seleccionado y
	# pasa estos valores a la funcion encargada de generar el contexto. Finalmente
	# utiliza el contexto generado para mostrar la nueva pagina.
	def post(self, request, **kwargs):
		begin = request.POST.get('begin_date')
		end = request.POST.get('end_date')
		event_selected = request.POST.get('event_selected')
		context = self.get_context_data(event_selected, begin, end, **kwargs)
		return render(request, 'events/user_event_list.html', context)


# Vista que muestra los eventos de movimiento en cercanias de la puerta en horarios
# extraescolares, es decir que cuando se detecta movimiento entre las 24 y 08 hs
# se captura una foto del exterior del laboratorio.
class MovementEventView(AdminTest, ListView):

	# El template por defecto es "movement_list.html".
	# El modelo a utilizar
	model = Movement
	# Se activa la paginacion para los eventos no filtrados.
	#
	# Se especifica que por pagina muestre veinte eventos.
	paginate_by = 20
	# Se cambia el nombre en la url de la pagina.
	page_kwarg = 'pagina'

	# Funcion encargada de manejar el pedido cuando se presiona el boton del filtro.
	def post(self, request):
		# Si se presiona el boton de "Filtrar".
		if 'date_filter' in request.POST:
			# Se obtiene la fecha de inicio seleccionada.
			begin = request.POST.get('begin_date')
			# Se obtiene la fecha de fin seleccionada.
			end = request.POST.get('end_date')
			# Si no se ingreso ni principio ni fin en el filtro, se vuelve a cargar la
			# pagina principal, con el objetivo que haga la paginacion.
			if begin == '' and end == '':
				return HttpResponseRedirect(reverse('events:movement'))
			# Se crea el contexto a mostrar.
			context = get_event_context_for_filter(begin, end, Movement)
			# Se muestra la pagina manteniendose en la URL.
			return render(request, 'events/movement_list.html', context)
		# Si se presiona el boton de "Exportar eventos".
		elif 'export_filtered_events' in request.POST:
			# Se obtiene la fecha de inicio que ya se encuentra seleccionada en el filtro.
			begin = request.POST.get('begin_export')
			# Se obtiene la fecha de finalizacion que ya se encuentra seleccionada en
			# el filtro.
			end = request.POST.get('end_export')
			# Si ambas fechas son vacias, se vuelve a cargar la pagina principal.
			if begin == '' and end == '':
				return HttpResponseRedirect(reverse('events:movement'))
			# Se obtiene el contexto para las fechas seleccionadas en el filtro.
			context = get_event_context_for_filter(begin, end, Movement)
			# Se retorna la respuesta incluyendo la descarga del archivo csv,
			# pasando como parametros la lista de objetos junto al tipo de evento.
			return get_response(context['object_list'], 'Movement')
		elif 'export_all_events' in request.POST:
			# Se setea como fecha de inicio una cadena vacia.
			begin = ''
			# Se setea como fecha de finalizacion una cadena vacia.
			end = ''
			# Se obtiene el contexto para las fechas seleccionadas en el filtro.
			context = get_event_context_for_filter(begin, end, Movement)
			# Se retorna la respuesta incluyendo la descarga del archivo csv,
			# pasando como parametros la lista de objetos junto al tipo de evento.
			return get_response(context['object_list'], 'Movement')


# Vista que muestra los eventos de toque de timbre, es decir que cada vez que una
# persona presione el boton del exterior del laboratorio, se genera un evento
# conteniendo la fecha, hora y la foto del exterior del laboratorio.
class ButtonEventView(AdminTest, ListView):

	# El template por defecto es "button_list.html".
	# El modelo a utilizar
	model = Button
	# Se activa la paginacion para los eventos no filtrados.
	#
	# Se especifica que por pagina muestre veinte eventos.
	paginate_by = 20
	# Se cambia el nombre en la url de la pagina.
	page_kwarg = 'pagina'

	# Funcion encargada de manejar el pedido cuando se presiona el boton del filtro.
	def post(self, request):
		# Si se presiona el boton de "Filtrar".
		if 'date_filter' in request.POST:
			# Se obtiene la fecha de inicio seleccionada.
			begin = request.POST.get('begin_date')
			# Se obtiene la fecha de fin seleccionada.
			end = request.POST.get('end_date')
			# Si no se ingreso ni principio ni fin en el filtro, se vuelve a cargar la
			# pagina principal, con el objetivo que haga la paginacion.
			if begin == '' and end == '':
				return HttpResponseRedirect(reverse('events:button'))
			# Se crea el contexto a mostrar.
			context = get_event_context_for_filter(begin, end, Button)
			# Se muestra la pagina manteniendose en la URL.
			return render(request, 'events/button_list.html', context)
		# Si se presiona el boton de "Exportar eventos".
		elif 'export_filtered_events' in request.POST:
			# Se obtiene la fecha de inicio que ya se encuentra seleccionada en el filtro.
			begin = request.POST.get('begin_export')
			# Se obtiene la fecha de finalizacion que ya se encuentra seleccionada en
			# el filtro.
			end = request.POST.get('end_export')
			# Si ambas fechas son vacias, se vuelve a cargar la pagina principal.
			if begin == '' and end == '':
				return HttpResponseRedirect(reverse('events:button'))
			# Se obtiene el contexto para las fechas seleccionadas en el filtro.
			context = get_event_context_for_filter(begin, end, Button)
			# Se retorna la respuesta incluyendo la descarga del archivo csv,
			# pasando como parametros la lista de objetos junto al tipo de evento.
			return get_response(context['object_list'], 'Button')
		elif 'export_all_events' in request.POST:
			# Se setea como fecha de inicio una cadena vacia.
			begin = ''
			# Se setea como fecha de finalizacion una cadena vacia.
			end = ''
			# Se obtiene el contexto para las fechas seleccionadas en el filtro.
			context = get_event_context_for_filter(begin, end, Button)
			# Se retorna la respuesta incluyendo la descarga del archivo csv,
			# pasando como parametros la lista de objetos junto al tipo de evento.
			return get_response(context['object_list'], 'Button')


# Vista que muestra los eventos de accesos denegados, es decir cuando una persona
# no autorizada (ya sea que no fue registrado en el sistema o que esta inactiva)
# acerca el llavero al lector para intentar ingresar al laboratorio.
class DeniedAccessEventView(AdminTest, ListView):

	# El template por defecto es "deniedaccess_list.html".
	# El modelo a utilizar
	model = DeniedAccess
	# Se activa la paginacion para los eventos no filtrados.
	#
	# Se especifica que por pagina muestre veinte eventos.
	paginate_by = 20
	# Se cambia el nombre en la url de la pagina.
	page_kwarg = 'pagina'

	# Funcion encargada de manejar el pedido cuando se presiona el boton del filtro.
	def post(self, request):
		# Si se presiona el boton de "Filtrar".
		if 'date_filter' in request.POST:
			# Se obtiene la fecha de inicio seleccionada.
			begin = request.POST.get('begin_date')
			# Se obtiene la fecha de fin seleccionada.
			end = request.POST.get('end_date')
			# Si no se ingreso ni principio ni fin en el filtro, se vuelve a cargar la
			# pagina principal, con el objetivo que haga la paginacion.
			if begin == '' and end == '':
				return HttpResponseRedirect(reverse('events:denied_access'))
			# Se crea el contexto a mostrar.
			context = get_event_context_for_filter(begin, end, DeniedAccess)
			# Se muestra la pagina manteniendose en la URL.
			return render(request, 'events/deniedaccess_list.html', context)
		# Si se presiona el boton de "Exportar eventos".
		elif 'export_filtered_events' in request.POST:
			# Se obtiene la fecha de inicio que ya se encuentra seleccionada en el filtro.
			begin = request.POST.get('begin_export')
			# Se obtiene la fecha de finalizacion que ya se encuentra seleccionada en
			# el filtro.
			end = request.POST.get('end_export')
			# Si ambas fechas son vacias, se vuelve a cargar la pagina principal.
			if begin == '' and end == '':
				return HttpResponseRedirect(reverse('events:denied_access'))
			# Se obtiene el contexto para las fechas seleccionadas en el filtro.
			context = get_event_context_for_filter(begin, end, DeniedAccess)
			# Se retorna la respuesta incluyendo la descarga del archivo csv,
			# pasando como parametros la lista de objetos junto al tipo de evento.
			return get_response(context['object_list'], 'DeniedAccess')
		elif 'export_all_events' in request.POST:
			# Se setea como fecha de inicio una cadena vacia.
			begin = ''
			# Se setea como fecha de finalizacion una cadena vacia.
			end = ''
			# Se obtiene el contexto para las fechas seleccionadas en el filtro.
			context = get_event_context_for_filter(begin, end, DeniedAccess)
			# Se retorna la respuesta incluyendo la descarga del archivo csv,
			# pasando como parametros la lista de objetos junto al tipo de evento.
			return get_response(context['object_list'], 'DeniedAccess')


# Vista que muestra los eventos de apertura de puerta via web, esto es cuando un
# usuario logueado presiona el boton en la pagina para abrir la puerta del
# laboratorio.
class WebOpenDoorEventView(AdminTest, ListView):

	# El template por defecto es "webopendoor_list.html".
	# El modelo a utilizar
	model = WebOpenDoor
	# Se activa la paginacion para los eventos no filtrados.
	#
	# Se especifica que por pagina muestre veinte eventos.
	paginate_by = 20
	# Se cambia el nombre en la url de la pagina.
	page_kwarg = 'pagina'

	# Funcion encargada de manejar el pedido cuando se presiona el boton del filtro.
	def post(self, request):
		# Si se presiona el boton de "Filtrar".
		if 'date_filter' in request.POST:
			# Se obtiene la fecha de inicio seleccionada.
			begin = request.POST.get('begin_date')
			# Se obtiene la fecha de fin seleccionada.
			end = request.POST.get('end_date')
			# Si no se ingreso ni principio ni fin en el filtro, se vuelve a cargar la
			# pagina principal, con el objetivo que haga la paginacion.
			if begin == '' and end == '':
				return HttpResponseRedirect(reverse('events:web_open_door'))
			# Se crea el contexto a mostrar.
			context = get_event_context_for_filter(begin, end, WebOpenDoor)
			# Se muestra la pagina manteniendose en la URL.
			return render(request, 'events/webopendoor_list.html', context)
		# Si se presiona el boton de "Exportar eventos".
		elif 'export_filtered_events' in request.POST:
			# Se obtiene la fecha de inicio que ya se encuentra seleccionada en el filtro.
			begin = request.POST.get('begin_export')
			# Se obtiene la fecha de finalizacion que ya se encuentra seleccionada en
			# el filtro.
			end = request.POST.get('end_export')
			# Si ambas fechas son vacias, se vuelve a cargar la pagina principal.
			if begin == '' and end == '':
				return HttpResponseRedirect(reverse('events:web_open_door'))
			# Se obtiene el contexto para las fechas seleccionadas en el filtro.
			context = get_event_context_for_filter(begin, end, WebOpenDoor)
			# Se retorna la respuesta incluyendo la descarga del archivo csv,
			# pasando como parametros la lista de objetos junto al tipo de evento.
			return get_response(context['object_list'], 'WebOpenDoor')
		elif 'export_all_events' in request.POST:
			# Se setea como fecha de inicio una cadena vacia.
			begin = ''
			# Se setea como fecha de finalizacion una cadena vacia.
			end = ''
			# Se obtiene el contexto para las fechas seleccionadas en el filtro.
			context = get_event_context_for_filter(begin, end, WebOpenDoor)
			# Se retorna la respuesta incluyendo la descarga del archivo csv,
			# pasando como parametros la lista de objetos junto al tipo de evento.
			return get_response(context['object_list'], 'WebOpenDoor')


# Vista que muestra los eventos de accesos permitidos, esto es cuando un usuario
# activo acerca su llavero al lector para ingresar al laboratorio.
class PermittedAccessEventView(AdminTest, ListView):

	# El template por defecto es "permittedaccess_list.html".
	# El modelo a utilizar
	model = PermittedAccess
	# Se activa la paginacion para los eventos no filtrados.
	#
	# Se especifica que por pagina muestre veinte eventos.
	paginate_by = 20
	# Se cambia el nombre en la url de la pagina.
	page_kwarg = 'pagina'

	# Funcion encargada de manejar el pedido cuando se usa el filtro de fechas o
	# se exportan los eventos.
	def post(self, request):
		# Si se presiona el boton de "Filtrar".
		if 'date_filter' in request.POST:
			# Se obtiene la fecha de inicio seleccionada.
			begin = request.POST.get('begin_date')
			# Se obtiene la fecha de fin seleccionada.
			end = request.POST.get('end_date')
			# Si no se ingreso ni principio ni fin en el filtro, se vuelve a cargar la
			# pagina principal, con el objetivo que haga la paginacion.
			if begin == '' and end == '':
				return HttpResponseRedirect(reverse('events:permitted_access'))
			# Se crea el contexto a mostrar.
			context = get_event_context_for_filter(begin, end, PermittedAccess)
			# Se muestra la pagina manteniendose en la URL.
			return render(request, 'events/permittedaccess_list.html', context)
		# Si se presiona el boton de "Exportar eventos".
		elif 'export_filtered_events' in request.POST:
			# Se obtiene la fecha de inicio que ya se encuentra seleccionada en el filtro.
			begin = request.POST.get('begin_export')
			# Se obtiene la fecha de finalizacion que ya se encuentra seleccionada en
			# el filtro.
			end = request.POST.get('end_export')
			# Si ambas fechas son vacias, se vuelve a cargar la pagina principal.
			if begin == '' and end == '':
				return HttpResponseRedirect(reverse('events:permitted_access'))
			# Se obtiene el contexto para las fechas seleccionadas en el filtro.
			context = get_event_context_for_filter(begin, end, PermittedAccess)
			# Se retorna la respuesta incluyendo la descarga del archivo csv,
			# pasando como parametros la lista de objetos junto al tipo de evento.
			return get_response(context['object_list'], 'PermittedAccess')
		elif 'export_all_events' in request.POST:
			# Se setea como fecha de inicio una cadena vacia.
			begin = ''
			# Se setea como fecha de finalizacion una cadena vacia.
			end = ''
			# Se obtiene el contexto para las fechas seleccionadas en el filtro.
			context = get_event_context_for_filter(begin, end, PermittedAccess)
			# Se retorna la respuesta incluyendo la descarga del archivo csv,
			# pasando como parametros la lista de objetos junto al tipo de evento.
			return get_response(context['object_list'], 'PermittedAccess')

#----------------------------------------------------------------------------------------



#----------------------------------------------------------------------------------------
#		Backup
#----------------------------------------------------------------------------------------

# Vista que permite realizar la copia de seguridad del sistema.
class BackupView(AdminTest, View):

	# Funcion que muestra el template cuando se visita la pagina.
	def get(self, request):
		# Simplemente se retorna la pagin a mostrar
		return render(request, 'events/backup.html')

	# Funcion encargada de manejar el pedido cuando se presiona algun boton del formulario.
	def post(self, request):
		# Se crea el buffer de tipo string, tambien llamado archivos de memoria para el archivo
		# zip.
		string_buffer = BytesIO()
		# Se crea el archivo de tipo zip, pasando como primer argumento el buffer de tipo
		# string como objeto de tipo archivo, y el segundo argumento indicando que se va a
		# escribir un nuevo archivo.
		zip_file = zipfile.ZipFile(string_buffer, 'w')
		# Se obtiene la fecha del dia de hoy en el formato especificado ("dia-mes-año") para
		# posterior uso en el nombre del archivo a descargar.
		today = datetime.datetime.now().date().strftime('%d-%m-%Y')
		# Si se presiona el boton de "Copia de seguridad de todo el sistema".
		if 'complete_backup' in request.POST:
			# Se recorre el path del proyecto.
			# En dirpath se obtiene el path al directorio.
			# En dirnames la lista de los subdirectorios de dirpath.
			# En filenames la lista de los archivos en el dirpath.
			for dirpath,dirnames,filenames in os.walk(settings.BASE_DIR):
				# fd = os.path.join(os.path.split(dirpath)[-1])
				# print ('destiny: %s') % fd
				for file in filenames:
					# print f
					# print dirpath
					# Se obtiene el archivo a escribir en el zip, uniendo el path al directorio y
					# el nombre del archivo, resultando en el path absoluto al archivo.
					file_data = os.path.join(dirpath, file)
					# Se obtiene el destino del archivo a escribir en el zip, esto se consigue
					# con el nombre del proyecto mas el path relativo (al proyecto) del archivo.
					# De esta manera se logra que el archivo zip quede estructurado tal cual como
					# el proyecto, logrando que se pueda restituir dicho directorio completo en
					# cualquier dispositivo que tenga instalado Django.
					proyect_name = settings.BASE_DIR.split('/')[-1]
					relative_file_path = file_data.split(settings.BASE_DIR)[-1]
					file_destiny = proyect_name + relative_file_path
					# Se escribe el archivo zip, indicando el archivo (path absoluto) y el lugar
					# dentro del mismo ("file_destiny").
					zip_file.write(file_data, file_destiny)
			# Se crea el nombre del archivo a descargar junto con la fecha del dia actual.
			filename = 'backup del sistema (%s).zip' % today
		# Si se presiona el boton de "Copia de seguridad de la base de datos".
		elif 'database_backup' in request.POST:
			if settings.DATABASES['default']['ENGINE'] == 'djongo':
				# Backup de base default
				mongoUri = settings.DATABASES['default']['HOST']
				conn = MongoClient(mongoUri)
				collections = ['users_user', 'users_visitor', 'users_timezone', 'django_session']
				db_name = settings.DATABASES['default']['NAME']
				try:
					self.dump(collections, conn, db_name, 'respaldo_bd-default')
				except Exception as e:
					logger.error("Error: %s", str(e))

				# Backup de base backup
				mongoUri = settings.DATABASES['backup']['HOST']
				conn = MongoClient(mongoUri)
				db_name = settings.DATABASES['backup']['NAME']
				try:
					self.dump(collections, conn, db_name, 'respaldo_bd-backup')
				except Exception as e:
					logger.error("Error: %s", str(e))
				path = settings.BASE_DIR + '/backups/'
				for root, dirs, files in os.walk(path):
					for file in files:
						zip_file.write(os.path.join(root, file),
						os.path.relpath(os.path.join(root, file),
						os.path.join(path, '..')))
			else:
				# Nombre del archivo (base de datos del proyecto).
				# Se obtiene del diccionario del archivo de configuracion.
				file_name = settings.DATABASES['default']['NAME'].split('/')[-1]
				# Se obtiene el path absoluto de la base de datos del sistema.
				file_data = settings.BASE_DIR + '/' + file_name
				# Se escribe el archivo zip.
				zip_file.write(file_data, file_name)
				# Se crea el nombre del archivo a descargar junto con la fecha del dia actual.
			filename = 'backup de la base de datos (%s).zip' % today
		# Se cierra el archivo zip.
		zip_file.close()
		# Se crea la respuesta, de tipo zip y con datos obtenidos del buffer de tipo string.
		response = HttpResponse(string_buffer.getvalue(), content_type='application/zip')
		# Se indica que se adjunta el archivo.
		response['Content-Disposition'] = 'attachment; filename=%s' % filename
		# Se retorna la respuesta con el archivo zip a descargar.
		return response
	
	def dump(self, collections, conn, db_name, directory):
		"""
		MongoDB Dump
		:param collections: Database collections name
		:param conn: MongoDB client connection
		:param db_name: Database name
		:param path:
		:return:
		
		>>> DB_BACKUP_DIR = '/path/backups/'
		>>> conn = MongoClient("mongodb://admin:admin@127.0.0.1:27017", authSource="admin")
		>>> db_name = 'my_db'
		>>> collections = ['collection_name', 'collection_name1', 'collection_name2']
		>>> dump(collections, conn, db_name, DB_BACKUP_DIR)
		"""
		db = conn[db_name]
		path = settings.BASE_DIR + '/backups/'+ directory
		if not os.path.exists(path):
			os.makedirs(path)
		for coll in collections:
			with open(os.path.join(path , f'{coll}.bson'), 'wb+') as f:
				for doc in db[coll].find():
					f.write(bson.BSON.encode(doc))
