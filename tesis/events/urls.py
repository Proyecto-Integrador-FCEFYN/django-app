from django.conf.urls import url

from . import views

app_name = 'events'
urlpatterns = [
	# URL raiz, redirije a iniciar el sistema o al inicio segun corresponda.
	url(r'^$', views.RootView.as_view(), name='root'),
	# URL para inicializar el sistema por primera vez.
	url(r'^inicializar-sistema/$', views.InitializeSystem.as_view(), name='initialize'),

	# URL de inicio, pagina redireccionada luego de loguearse. En esta pagina se puede
	# ver el stream y abrir la puerta, tanto un usuario que es admin como uno que no.
	# URLs de las herramientas.
	# url(r'^control/(?P<pk>[0-9]+)/$', views.HomeView.as_view(), name='control'),
	#
	# Para realizar el backup.
	url(r'^herramientas/copia-seguridad/$', views.BackupView.as_view(), name='backup'),
	url(r'^herramientas/sensor-movimiento/(?P<pk>[0-9]+)/$', views.MovementTimeZoneView.as_view(), 
		name='movement_time_zone'),
	url(r'^herramientas/borrado-eventos/(?P<pk>[0-9]+)/$', views.EventsDurationView.as_view(), 
		name='events_duration'),
	url(r'^herramientas/almacenamiento/$', views.StorageView.as_view(), name='storage'),

	# URLs de los eventos.
	#
	# Eventos de un usuario en particular. Estos eventos son de dos tipos, ingresos
	# con llavero y apertura de puerta via web.
	url(r'^eventos/usuario/(?P<pk>[0-9]+)/$', views.UserEventView.as_view(),
		name='user_event'),
	# Eventos del tipo movimiento en horarios extraescolares.
	url(r'^eventos/movimiento/$', views.MovementEventView.as_view(),
		name='movement'),
	# Eventos del tipo toque de timbre.
	url(r'^eventos/timbre/$', views.ButtonEventView.as_view(),
		name='button'),
	# Eventos del tipo prohibicion de acceso, o sea cuando se pasa un llavero que
	# no esta habilitado para el ingreso.
	url(r'^eventos/acceso-denegado/$', views.DeniedAccessEventView.as_view(),
		name='denied_access'),
	# Eventos del tipo apertura de puerta via web, mediante un usuario logueado
	# en el sistema.
	url(r'^eventos/apertura-web/$', views.WebOpenDoorEventView.as_view(),
		name='web_open_door'),
	# Eventos del tipo ingreso con llavero, mediante un usuario activo y que
	# este dentro de su franja horaria permitida.
	url(r'^eventos/acceso-permitido/$', views.PermittedAccessEventView.as_view(),
		name='permitted_access'),
]