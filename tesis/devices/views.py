from ipaddress import ip_address
from django.shortcuts import render
# Se importa el archivo de configuracion del proyecto para utilizar la variable
# que contiene el path absoluto del mismo en caso de realizar el backup.
from django.conf import settings
# Se importa la vista de la aplicacion "users" para la verificacion
# de que el usuario sea admin, osea "is_staff=True".
from users.views import AdminTest
# Para realizar querysets mas especificos.
from django.db.models import Q
# Agregados a las vistas para mayor control, como requerimiento de logueo
# y comprobacion de que el usuario sea admin.
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
# Para crear el "ModelForm" dado un modelo. Se utiliza para agregar widgets
# en la vista de edicion de la franja horaria del sensor de movimiento.
from django.forms.models import modelform_factory
from django import forms
# Para el manejo de las respuestas a los pedidos.
from django.http import HttpResponseRedirect, HttpResponse
# Para renderizar un template rapidamente.
from django.shortcuts import render
from django.contrib import messages
# Para redireccionar a una URL.
from django.urls import reverse, reverse_lazy
from django.utils import timezone
# Vista generica a la que hay que definir el manejo completo de los pedidos.
from django.views import View
# Vistas genericas para mostrar informacion de los modelos.
from django.views.generic import CreateView, ListView, UpdateView, DeleteView, RedirectView, DetailView
# Vista generica para actualizar campos de los modelos.
from django.views.generic.edit import UpdateView
import paho.mqtt.publish as publish
from ping3 import ping
from .models import *
from users.models import Category, User
import logging
logger = logging.getLogger(__name__)


# Vista que muestra la lista de los usuarios registrados.
#
# El template por defecto es "user_list.html", por lo que no es necesario
# especificar un "template_name".
# La variable de contexto por defecto es "object_list" o tambien
# "user_list", formado por el nombre del modelo mas "_list", pero se
# la puede cambiar con el atributo "context_object_name".
class DevicesListView(AdminTest, ListView):
	# Se especifica el modelo a utilizar para la ListView, se puede
	# indicar con el atributo "model" o tambien mediante "queryset" donde
	# se puede filtrar la lista de objetos. En este caso se utiliza "model"
	# debido a que no interesa filtrar la lista de objetos y ya esta
	# ordenada por la fecha de alta de los usuarios en el modelo.
	model = Device
	# Se utiliza la paginación.
	#
	# Se pone en veinte dispositivos por pagina.
	paginate_by = 20
	# Se cambia el nombre de la pagina en la url.
	page_kwarg = 'pagina'

	# def get(self, request, *args, **kwargs):
	# 	qs = Device.objects.all()
	# 	self.pingDevices(qs)
	# 	return super().get(request, *args, **kwargs)


	# Funcion encargada de atender solicitudes de tipo "POST", en este caso
	# cuando se presiona el boton "Buscar".
	def post(self, request):
		# Se obtienen las letras ingresadas en el campo de busqueda.
		search = request.POST.get('search_device')
		# Se obtiene el queryset filtrado por los nombres y apellidos de los usuarios
		# que contengan las letras ingresadas en el campo de busqueda.
		qs = Device.objects.filter(
				Q(device_name__icontains=search)
				)
		# Si se presiono el boton de "Buscar" pero no se ingreso alguna letra, se
		# retorna a la pagina principal con la lista completa de usuarios y con
		# paginacion activada.
		if 'search' in request.POST and not search:
			return HttpResponseRedirect(reverse('devices:device_list'))
		else:
			pass
		# Se crea el contexto con el queryset y las letras ingresadas en el campo
		# de busqueda.
		# self.pingDevices(qs)
		context = {
			'device_list' : qs,
			'name_search' : search,
		}
		# Se muestra el template.
		return render(request, 'devices/device_list.html', context)

	# def pingDevices(self, device_list):
	# 	logger.error("Holitas")
	# 	for device in device_list:
	# 		if ping(device.ip_address):
	# 			device.last_ping = timezone.now()
	# 			device.save()
	# 			logger.error("hay")
	# 		else:
	# 			logger.error(" no hay")

#----------------------------------------------------------------------------------------

class DeviceCreateView(AdminTest, CreateView):
	model = Device
	template_name = 'devices/device_create.html'
	form_class = modelform_factory(Device,
		fields = ['device_name', 'ip_address','port', 'MAC_address','type', 'category_list'],
		widgets={
			'category_list': forms.CheckboxSelectMultiple
		})

	
class DeviceEditView(AdminTest, UpdateView):
	model = Device
	template_name = 'devices/device_edit.html'
	form_class = modelform_factory(Device,
		fields = ['device_name', 'ip_address','port' ,'MAC_address','type', 'category_list'],
		widgets={
			'category_list': forms.CheckboxSelectMultiple
		})


class DeviceDeleteView(AdminTest, DeleteView):
	model = Device
	success_url = reverse_lazy('devices:device_list')

# Vista que muestra los dispositivos que pueden ser controlados por usuario actual.
class HomeView(AdminTest, View):
	def get(self, request, **kwargs):
		context = self.get_context_data(**kwargs)
		return render(request, 'devices/homepage.html', context)

	def get_context_data(self, **kwargs):
		user_cat = self.request.user.category_list.all()
		user_name = '{} {}'.format(self.request.user.first_name, self.request.user.last_name)
		categorias = []
		for cat in user_cat:
			categorias.append(cat.id)
		devices = Device.objects.filter(Q(category_list__in=categorias)).distinct()
		logger.error("devicesss: %s", devices)
		context = {'device_list' : devices,
		'user_category': user_cat,
		'user_name': user_name}
		return context

class PingDevicesView(AdminTest, RedirectView):
	def get_redirect_url(self, **kwargs):
		devices = Device.objects.all()
		self.pingDevices(devices)
		return reverse('devices:device_list')
	
	
	def pingDevices(self, device_list):
		for device in device_list:
			if ping(device.ip_address):
				device.last_ping = timezone.now()
				device.save()
				message = '{}:  Fecha de última vez actualizada.'.format(device.device_name)
				messages.success(self.request, message)
			else:
				message = '{}:  No se encuentra el dispositivo.'.format(device.device_name)
				messages.error(self.request, message)
			


class PingDeviceView(AdminTest, RedirectView):
	def get_redirect_url(self, **kwargs):
		device = Device.objects.get(pk=self.kwargs['pk'])
		self.pingDevices(device)
		return reverse('devices:device_list')
	
	
	def pingDevices(self, device):	
		if ping(device.ip_address):
			device.last_ping = timezone.now()
			device.save()
			message = '{}:  Fecha de última vez actualizada.'.format(device.device_name)
			messages.success(self.request, message)
		else:
			message = '{}:  No se encuentra el dispositivo.'.format(device.device_name)
			messages.error(self.request, message)
	
class ManageView(AdminTest, View):
	# Funcion que retorna la pagina a mostrar.
	def get(self,request, **kwargs):
		return render(request, 'devices/device_detail.html')

	def post(self, request, **kwargs):

		device = Device.objects.get(pk=self.kwargs['pk'])
		tipo_device =  device.type # 'placanro1'

		topic = f'{tipo_device}/boton'
		payload = str(request.user.pk)
		hostname = device.ip_address # 'raspi'
		port = device.port # 1883
		auth={
			'username': "user",
			'password': "pass"
		}
		try:
			publish.single(topic=topic, payload=payload, hostname=hostname, port=port)
			messages.success(self.request, "Mensaje enviado.")
		except:
			messages.error(self.request, "No hay comunicación con el dispositivo.")
		
		return HttpResponseRedirect(self.request.path_info)
