# -*- coding: utf-8 -*-
from django.contrib.auth import logout
from django.contrib.sessions.models import Session
from django.utils import deprecation

# Se importan las funciones creadas para esta aplicacion.
from .utils import *

from .models import Visitor


# Middleware que evita que esten logueados dos usuarios con el mismo nombre de usuario al
# mismo tiempo. En caso de estar logueado un usuario y pretende loguerse otro con el mismo
# nombre de usuario, lo desloguea al primero cuando este actualice o cambie de pagina.
# Utiliza la llave de la sesion del usuario (la cual se encuentra en las cookies) de la
# aplicacion "sessions" instalada por defecto junto a la instalacion del Django.
#
# Referencia: https://gist.github.com/peterdemin/5829440
#
# Aclaracion: las sesiones son administradas ya por defecto mediante la aplicacion "sessions"
# y el middleware "SessionMiddleware", lo cual agrega un nuevo par llave-datos_de_sesion junto
# a la fecha de expiracion cada vez que un usuario se loguea. Esto es utilizado para recordar
# los datos del usuario, entonces cuando el usuario intente ingresar al sition web en otro
# momento, el servidor ya tiene almacenada su sesion, por lo que el usuario no necesita
# volver a loguearse (mientras no haya vencido la fecha de expiracion, la cual esta seteada
# por defecto en 20 dias). Estas sesiones pueden cambiar en caso que el usuario cambie algun
# dato como por ejemplo su contraseña, la proxima vez que se loguea crea una nueva sesion, ya
# que sus datos_de_sesion de su cache cambiaron. Esto hace que el numero de sesiones aumente
# con el paso del tiempo, porque por mas que se llegue al dia de fecha de expiracion, no se
# elminan (tambien se crean sesiones si el usuario cierra el explorador en vez de cerrar sesion
# antes de salir del sitio). Por lo que se soluciona limpiando estas sesiones caducadas desde
# el programa principal mediante el comando "django-admin clearsessions" ejecutado
# periodicamente.
# Para poder entonces controlar que no puedan estar dos usuarios logueados con el mismo
# nombre de usuario, no es posible mediante esta aplicacion, ya que no asigna estos valores
# de la sesion a cierto usuario, sino que cada usuario posee en sus cookies la llave que
# coincide con la de la base de datos. Es por esto que se crea un nuevo modelo que almacene
# dicha llave junto a la clave principal del usuario, para poder comparar a futuro con un
# nuevo usuario que se loguea.
class PreventConcurrentLoginsMiddleware(deprecation.MiddlewareMixin):

	# Funcion encargada de procesar el pedido.
	def process_request(self, request):
		# Si el usuario esta autenticado, no verifica que este activo ni que posea una
		# sesion valida.
		if request.user.is_authenticated():
			# Se obtiene la llave de la sesion del usuario.
			key_from_cookie = request.session.session_key
			# Si el usuario esta en la tabla del modelo "Visitor".
			if hasattr(request.user, 'visitor'):
				# Obtiene la llave de la sesion almacenada en dicha tabla.
				session_key_in_visitor_db = request.user.visitor.session_key
				# Y compara con la llave del usuario en cuestion.
				if session_key_in_visitor_db != key_from_cookie:
					# De ser distintas, elimina el objecto de "Session" de la tabla.
					Session.objects.filter(session_key = session_key_in_visitor_db).delete()
					# Y se asigna como nueva llave de sesion la actual.
					request.user.visitor.session_key = key_from_cookie
					# Se guarda el objecto en la base de datos.
					request.user.visitor.save()

			# En caso de que el usuario no se encuentra en la tabla, se lo agrega.
			else:
				Visitor.objects.create(
					user=request.user,
					session_key=key_from_cookie
				)


# Middleware que evita que un usuario pueda abrir la puerta estando fuera de su franja horaria.
# Si bien se testea esto cuando el usuario se loguea, una vez logueado, si el usuario excede la
# hora del limite de la franja, no se lo expulsa del sistema y por lo tanto lo puede seguir
# utilizando. Mediante este control se hace nuevamente un testeo para los usuarios que no son
# administradores para cada accion realizada.
class PreventUserActionOutOfTimeZone(deprecation.MiddlewareMixin):

	# Funcion encargada de procesar el pedido.
	def process_request(self, request):
		if request.user.is_authenticated():
			if not request.user.is_staff:
				if not time_zone_test(request.user):
					logout(request)