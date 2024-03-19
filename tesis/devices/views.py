from ipaddress import ip_address
from django.shortcuts import render
# Se importa la vista de la aplicacion "users" para la verificacion
# de que el usuario sea admin, osea "is_staff=True".
from users.views import AdminTest
# Para realizar querysets mas especificos.
from django.db.models import Q
from django.conf import settings
import socket
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
from django.views.generic.edit import *
from .forms import *
# Vista generica para actualizar campos de los modelos.
from django.views.generic.edit import UpdateView
import paho.mqtt.publish as publish
from ping3 import ping
import requests
from .models import *
from events.models import Button
from events.utils import *
import datetime
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

#----------------------------------------------------------------------------------------

class DeviceCreateView(AdminTest, CreateView):
	model = Device
	template_name = 'devices/device_create.html'
	form_class = modelform_factory(Device,
		fields = ['device_name', 'ip_address','port', 'MAC_address','type', 'category_list', 'cert', 'usuario', 'password'],
		widgets={
			'category_list': forms.CheckboxSelectMultiple,
			'password': forms.PasswordInput()
		})


class DeviceEditView(AdminTest, UpdateView):
	model = Device
	template_name = 'devices/device_edit.html'
	form_class = modelform_factory(Device,
		fields = ['device_name', 'ip_address','port' ,'MAC_address','type', 'category_list', 'cert'],
		widgets={
			'category_list': forms.CheckboxSelectMultiple
		})

class ChangePwdView(AdminTest, FormView):
	model = Device
	template_name = 'devices/change_pwd.html'
	form_class = DeviceForm

	def form_valid(self, form, **kwargs):
		device = Device.objects.get(pk=self.kwargs['pk'])
		device.usuario=form.cleaned_data['usuario']
		device.password=form.cleaned_data['password']
		device.save()
		return HttpResponseRedirect(reverse('devices:device_edit', kwargs={'pk':self.kwargs['pk']}))


class DeviceDeleteView(AdminTest, DeleteView):
	model = Device
	success_url = reverse_lazy('devices:device_list')

# Vista que muestra los dispositivos que pueden ser controlados por usuario actual.
class HomeView(View):
	def get(self, request, **kwargs):
		try:
			database = self.test_connection_to_db()
			context = {'database': database}
			context.update(self.get_context_data(**kwargs))
			return render(request, 'devices/homepage.html', context)
		except Exception:
			return HttpResponseRedirect('/')

	def get_context_data(self, **kwargs):
		try:
			user_cat = self.request.user.category_list.all()
			user_name = '{} {}'.format(self.request.user.first_name, self.request.user.last_name)
			categorias = []
			for cat in user_cat:
				categorias.append(cat.id)
			devices = Device.objects.filter(Q(category_list__in=categorias)).distinct()
			button_events = []
			for dev in devices:
				events = Button.objects.filter(device = dev)
				if events:
					current_event = events.order_by('-date_time')[0]
					current_timezone = datetime.datetime.strptime(
						((current_event).date_time).replace('T',' '), '%Y-%m-%d %H:%M:%S.%f')
					current_timezone = current_timezone.strftime('%d-%B-%Y %H:%M')
					current_event.date_time = current_timezone

					if button_events:
						if (button_events[0].date_time < current_timezone):
							button_events.insert(0,current_event)
						else:
							button_events.append(current_event)
					else:
						button_events.append(current_event)

			context = {'device_list' : devices,
			'user_category': user_cat,
			'user_name': user_name,
			'button_events': button_events}
			return context
		except Exception:
			return HttpResponseRedirect('/')

	def test_connection_to_db(self):
		try:
			db_definition = getattr(settings, 'DATABASES')['default']
			s = socket.create_connection((db_definition['my_host'], db_definition['my_port']), 5)
			s.close()
			return 'Default'
		except:
			return 'Backup'

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

class ManageView(DetailView):
	def get(self,request, **kwargs):
		user_cat = self.request.user.category_list.all()
		device = Device.objects.get(pk=self.kwargs['pk'])
		# Para asegurarnos que el usuario loggeado tenga las categorías soportadas para controlar este dispositivo.
		for cat in user_cat:
			if cat in device.category_list.all():
				context = {
					'device' : device.device_name,
					'port': device.port,
					'host': device.ip_address
					}
				return render(request, 'devices/device_detail.html', context)
		return HttpResponseRedirect('/')

	def post(self, request, **kwargs):

		BASE_URL = settings.API_BASE_URL  # 'http://localhost:5000'
		API_USUARIO = settings.API_USUARIO
		API_PASSWORD = settings.API_PASSWORD
		API_CERT_PATH = settings.API_CERT_PATH

		device = Device.objects.get(pk=self.kwargs['pk'])
		print(self.kwargs['pk'])
		tipo_device = device.type  # 'placanro1'

		hostname = device.ip_address  # 'raspi'
		port = device.port
		data = {
			"host": hostname,
			"port": port,
			"user_id": request.user.pk,  # 1,
			"device_id": int(self.kwargs['pk']),
			"usuario": device.usuario,
			"password": device.password
		}
		r = requests.post(url=f"{BASE_URL}/event/webbutton", json=data, auth=(API_USUARIO, API_PASSWORD),
					verify=API_CERT_PATH)
		if r.status_code == 200:
			messages.success(self.request, "Mensaje enviado.")
		else:
			messages.error(self.request, "No hay comunicación con el dispositivo.")

		return HttpResponseRedirect(self.request.path_info)
