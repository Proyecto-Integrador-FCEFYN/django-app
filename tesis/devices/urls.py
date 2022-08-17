
# -*- coding: utf-8 -*-
from django.conf.urls import url
# Se importan todas las vistas de auth ya que se utilizan la mayoria.
from django.contrib.auth import views as auth_views
# Se importa la funcion unicamente para modificar un atributo de algunas vistas de auth.
from django.urls import reverse_lazy
from . import views

app_name='devices'
urlpatterns=[
	# URL de inicio, pagina redireccionada luego de loguearse. En esta pagina se puede
	# ver el los dispositivos soportados por la categoría del usuario logueado.
	url(r'^inicio/$', views.HomeView.as_view(), name='home'),
	# URLs de las herramientas.
	url(r'^dispositivos/manage/(?P<pk>[0-9]+)/$', views.ManageView.as_view(), name='manage_device'),
	#
	url(r'^dispositivos/ping/(?P<pk>[0-9]+)/$', views.PingDeviceView.as_view(), name='ping_device'),
	url(r'^dispositivos/pingdevices/$', views.PingDevicesView.as_view(), name='ping_devices'),


	url(r'^dispositivos/editar/(?P<pk>[0-9]+)/$', views.DeviceEditView.as_view(), name='device_edit'),
	url(r'^dispositivos/eliminar/(?P<pk>[0-9]+)/$', views.DeviceDeleteView.as_view(),
		name='device_delete'),
    url(r'^dispositivos/crear/$', views.DeviceCreateView.as_view(),
		name='device_create'),
	url(r'^dispositivos/$', views.DevicesListView.as_view(), name='device_list'),
    url(r'^dispositivos/lista/$', views.DevicesListView.as_view(), name='device_list')
]