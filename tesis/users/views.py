# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Para sacar (desloguear) un usuario si no pasa el "AdminTest".
from django.contrib.auth import logout
# Agregados a las vistas para mayor control, como requerimiento de logueo
# y comprobacion de que el usuario sea admin.
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
# Para el manejo de mails.
from django.core.mail import send_mail
# Para realizar querysets mas especificos.
from django.db.models import Q
# Para crear el "ModelForm" dado un modelo. Se utiliza para agregar widgets
# en la vista de edicion de las franjas horarias.
from django.forms.models import modelform_factory
# Para renderizar un template rapidamente.
from django.shortcuts import render
# Para redireccionar a una URL.
from django.urls import reverse, reverse_lazy
# Vista generica a la que hay que definir el manejo completo de los pedidos.
from django.views import View
# Vistas genericas para mostrar informacion de los modelos.
from django.views.generic import ListView, TemplateView, DetailView, RedirectView
# Se importan todas las vistas genericas de edicion ya que se utilizan todas ("FormView",
# "CreateView", "UpdateView" y "DeleteView").
from django.views.generic.edit import *
# Para el manejo de las respuestas a los pedidos.
from django.http import HttpResponseRedirect, HttpResponse

# Los formularios de la aplicacion actual ("users").
from .forms import *
# Los modelos de la aplicacion actual ("users").
from .models import *

# Para exportar los usuarios como archivo csv.
import csv
# Para la creacion de la contraseña del usuario.
import random
# Para la comunicacion con el programa principal.
import socket




#----------------------------------------------------------------------------------------
#		Tests para las vistas
#----------------------------------------------------------------------------------------

# Esta vista se encarga de verificar que el usuario este logueado
# como asi tambien que sea staff (admin).
# Es necesario reescribir la funcion test_func, en este caso
# para comprobar que el usuario sea staff.
class AdminTest(LoginRequiredMixin, UserPassesTestMixin):

	def test_func(self):
		test = self.request.user.is_staff
		# Si no es admin el usuario, se lo desloguea.
		if not test:
			logout(self.request)
		return test

#----------------------------------------------------------------------------------------



#----------------------------------------------------------------------------------------
#		Registro de usuario
#----------------------------------------------------------------------------------------

# Esta vista es la utilizada para registrar un nuevo usuario,
# es necesario ser staff (admin) para poder registrar un usuario.
# Se especifica el formulario a utilizar como asi tambien el template.
# Y solo se verifica la validacion del formulario.
class UserRegisterStep1View(AdminTest, CreateView):

	form_class = UserCreationForm
	template_name = 'users/user_register_step_1.html'
	# Este metodo es llamado cuando se realiza un POST con informacion
	# valida, deberia de retornar un HttpResponse.

	def form_valid(self, form):
		### aca se deberia preguntar de donde viene y si el usuario que se pretende
		### crear es un admin, en caso de no serlo, volver a la misma pag.
		# Se ejecuta la funcion "save()" del formulario "UserCreationForm".
		form.save()
		# Se obtiene la clave principal del usuario creado para pasar como
		# argumento ("**kwargs") a la proxima etapa de registro de usuario. 
		pk = form.get_pk()
		# Se obtiene el atributo "is_staff" del usuario creado para en caso
		# de ser "admin" se salta el segundo paso, esto es debido a que los
		# admin no tienen franjas horarias.
		admin = form.get_is_staff()
		if (admin):
			# Se redirige a la pagina encargada de obtener el codigo de la tarjeta
			# RFID del usuario (paso 3).
			return HttpResponseRedirect(reverse('users:user_register_step_3', kwargs={'pk':pk}))
		else:
			# Se redirige a la pagina encargada de editar las franjas horarias (paso 2).
			return HttpResponseRedirect(reverse('users:user_register_step_2', kwargs={'pk':pk}))


# En esta vista se crean las franjas horarias y se especifica la fecha
# limite de la actividad del usuario. Simplemente una vez que se verifica
# que el formulario sea valido, se modifican los campos del usuario con
# los cargados en el formulario.
class UserRegisterStep2View(AdminTest, FormView):

	form_class = UserTimeZoneForm
	template_name = 'users/user_register_step_2.html'

	# Funcion que genera el contexto para el template, en este caso se
	# agrega al contexto todos los objectos del modelo "TimeZone"
	# para poder mostrar informacion acerca de los horarios de las franjas
	# en la pagina.
	def get_context_data(self, **kwargs):
		context = super(UserRegisterStep2View, self).get_context_data(**kwargs)
		context['time_zone'] = TimeZone.objects.all()
		return context

	# Funcion que es llamada una vez que el formulario contenga informacion
	# valida. Se asignan los campos del usuario con el contenido del
	# formulario.
	def form_valid(self, form, **kwargs):
		user = User.objects.get(pk=self.kwargs['pk'])
		user.expiration_date=form.cleaned_data['expiration_date']
		user.monday=form.cleaned_data['monday']
		user.tuesday=form.cleaned_data['tuesday']
		user.wednesday=form.cleaned_data['wednesday']
		user.thursday=form.cleaned_data['thursday']
		user.friday=form.cleaned_data['friday']
		user.saturday=form.cleaned_data['saturday']
		user.sunday=form.cleaned_data['sunday']
		user.save()
		return HttpResponseRedirect(reverse('users:user_register_step_3', kwargs={'pk':self.kwargs['pk']}))


# Vista encargada del manejo del codigo RFID del llavero
class UserRegisterStep3View(AdminTest, View):

	# Funcion que brinda la pagina una vez que se accede a la URL.
	# Dependiendo de que URL se acceda, carga distinto template.
	def get(self,request,**kwargs):
		# Se obtiene la URL desde la cual se accedio (URL previa).
		referer = self.request.META.get('HTTP_REFERER')
		# Si se viene del perfil del usuario.
		if 'perfil' in referer:
			return render(request, 'users/user_edit_code.html')
		# Si se viene de dar de baja un usuario, recordar que la vista "UserUnsubscribeView"
		# es de tipo "RedirectView", por lo que su "referer" es la pagina desde la cual
		# se accede a dicha vista.
		elif 'registro-paso-3' in referer:
			return HttpResponseRedirect(reverse('users:user_register_step_4', kwargs={'pk':self.kwargs['pk']}))
		# En casos contrarios, como ser que se venga del primer o segundo paso.
		else :
			return render(request, 'users/user_register_step_3.html')

	# Funcion encargada de procesar los formularios.
	def post(self,request,**kwargs):
		# Se obtiene la clave principal que se pasa como argumento "**kwargs".
		pk = self.kwargs['pk']
		# Si se presiona el boton "Obtener codigo" u "Obtener otro codigo" en caso de conflicto.
		if 'get_code' in request.POST:
			# Se obtiene el codigo del llavero RFID.
			code = self.get_code()
			# Se obtiene el usuario activo con el codigo solicitado o None en caso
			# de no existir.
			user = self.get_active_user(code)
			# Se obtiene ademas la variable 'edit' del contexto, la cual existe unicamente
			# si se trata de una edicion de usuario, en caso contrario es "None".
			edit = request.POST.get('edit')
			# Si el codigo obtenido por el metodo "get_code()" es un string vacio, significa
			# que no se capturo algun codigo RFID con el lector, por lo que se muestra una
			# pagina donde da la posibilidad de seguir intentando.
			if code == '':
				# Se pasa "edit" como contexto para distinguir entre un registro de un
				# nuevo usuario o una edicion de uno ya existente.
				context = {'edit':edit}
				return render(request, 'users/user_get_code_error.html', context)
			# Si existe el usuario, quiere decir que el llavero RFID ya pertenece a un
			# usuario activo del sistema, por lo se muestra una pagina en la que se brindan
			# tres alternativas: obtener otro codigo (otro llavero), dar de baja al usuario
			# en conflicto (al viejo) u omitir para que el usuario no tenga un codigo RFID,
			# esto significa que el usuario solo puede utilizar el sistema web.
			if user:
				# Se crea el contexto para el template, interesa el nombre completo del
				# usuario en conflicto, su clave en caso de darlo de baja y el codigo para
				# en caso de darlo de baja, guardarlo al usuario.
				# Tambien interesa si es que se esta editando el usuario, es por esto la
				# variable de contexto "edit", que se obtiene del template "user_edit_code.html".
				context = {'user':user.get_full_name(), 'user_pk':user.id, 'user_code':code, 'edit':edit}
				return render(request, 'users/user_register_step_3_error.html', context)
			# En caso contrario, se procede a guardar el usuario con el codigo obtenido.
			else:
				# Se guarda el usuario con el codigo obtenido.
				self.set_user_code(pk,code)
				# Si se edita un usuario se redirige al resultado de una edicion de codigo
				# RFID exitosa.
				if edit == '1':
					return HttpResponseRedirect(reverse('users:user_edit_code_success'))
				# En caso de ser una creacion de usuario, se redirecciona a la pagina de 
				# finalizacion de la tarea.
				return HttpResponseRedirect(reverse('users:user_register_step_4', kwargs={'pk':pk}))
		# Si se presiona el boton "Omitir".
		elif 'omit' in request.POST:
			# Se redirecciona a la pagina de finalizacion de la tarea, no se asigna codigo RFID
			# al usuario, por lo que se trata de un usuario unicamente web.
			# Si se esta editando un usuario se procede a la finalizacion de edicion, en caso
			# contrario a la finalizacion de creacion.
			if request.POST.get('edit') == '1':
				return HttpResponseRedirect(reverse('users:user_edit_code_success'))
			else :
				return HttpResponseRedirect(reverse('users:user_register_step_4', kwargs={'pk':pk}))
		# Si se presiona el boton "Eliminar codigo actual" en caso de editar el usuario.
		elif 'delete_code' in request.POST:
			# Se establece un string vacio como nuevo codigo.
			self.set_user_code(pk, '')
			# Se muestra la pagina indicando que la operacion fue exitosa.
			return HttpResponseRedirect(reverse('users:user_edit_code_success'))
		# Si se presiona el boton "Dar de baja al usuario en conflicto".
		elif 'unsubscribe' in request.POST:
			# Se guarda el usuario con el codigo obtenido.
			self.set_user_code(pk,request.POST.get('user_code'))
			# Se redirecciona a la vista encargada de dar de baja al usuario en conflicto.
			# Si se esta editando un usuario, se pasa como segundo argumento ("pk_alt") el valor
			# '0', esto no corresponde a una clave, sino que es un valor establecido solamente
			# para distinguir el tipo de operacion a realizar cuando se da de baja al usuario.
			# En caso que sea una creacion, se pasa como segundo argumento '1'.
			if request.POST.get('edit') == '1':
				return HttpResponseRedirect(reverse('users:user_unsubscribe', kwargs={'pk':request.POST.get('user_pk'), 'pk_alt':0}))
			else:
				return HttpResponseRedirect(reverse('users:user_unsubscribe', kwargs={'pk':request.POST.get('user_pk'), 'pk_alt':1}))
		# Si se presiona el boton "Cancelar operacion" en la pagina de error de obtencion del
		# codigo mediante el lector RFID. Se redirige a la pagina principal ("home").
		elif 'abort' in request.POST:
			return HttpResponseRedirect(reverse('events:home'))

	# Funcion encargada de obtener el codigo RFID del llavero. Crea un socket de tipo
	# INET y se conecta al servidor que reside en el programa principal, establece un
	# tiempo de espera y vencido el tiempo, retorna un string vacio indicando de que
	# no se obtuvo un codigo leido por el lector RFID.
	def get_code(self):
		HOST = '127.0.1.1'
		PORT = 50001
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((HOST, PORT))
		try:
			s.settimeout(10)
			code = s.recv(16)
			s.close()
			return code
		except:
			s.close()
			return ''

	# Funcion encargada de retornar un usuario activo y con el codigo pasado como
	# parametro, en caso de encontrar lo devuelve y en caso contrario retorna None.
	def get_active_user(self,code):
		try:
			user = User.objects.get(code=code, is_active=True)
		except:
			user = None
		return user

	# Funcion encargada de modificar el campo "code" del usuario solicitado.
	def set_user_code(self,pk,code):
		user = User.objects.get(pk=pk)
		user.code = code
		user.save()


# Vista para la finalizacion del registro de un usuario.
class UserRegisterStep4View(AdminTest, View):

	# Funcion encargada de mostrar la pagina al acceder a la vista.
	def get(self,request,**kwargs):
		# Primero se crea y establece la contraseña del usuario.
		self.set_user_password(self.kwargs['pk'])
		return render(request, 'users/user_register_step_4.html')

	# Funcion encargada de crear, guardar y avisar la contraseña del usuario.
	def set_user_password(self,pk):
		# Se obtiene el usuario a modificar.
		user = User.objects.get(pk=pk)
		# Se crea la contraseña, que consiste en las dos primeras letras del nombre y
		# del apellido seguido de cuatro numeros generados al azar.
		password = "%s%s%s" % (user.get_short_name()[0:2], user.get_last_name()[0:2], 
			str(random.randint(0000,9999)))
		# Se utiliza la funcion "set_password(password)" que se encarga de realizar
		# el hash de la contreseña previamente creada y lo guarda en el campo del
		# usuario.
		user.set_password(password)
		# Se graban los cambios hechos en el usuario.
		user.save()
		# Mensaje a enviar via email.
		message = 'Usuario registrado correctamente.\n\n-Usuario: %s\n-Codigo de acceso: %s' % (user, password)
		# Se envia el email al usuario indicando su nombre de usuario y su contraseña.
		send_mail('Control de acceso al LAC - Codigo de acceso', message, 'accesolac@gmail.com', [user], 
			fail_silently=True)

#----------------------------------------------------------------------------------------


#----------------------------------------------------------------------------------------
#		Habilitar e inhabilitar usuario
#----------------------------------------------------------------------------------------

# Vista encargada de dar de baja a un usuario.
class UserUnsubscribeView(AdminTest, RedirectView):

	# Funcion que define a que URL redirigir el pedido, en este caso
	# se realiza el trabajo y luego se redirige.
	def get_redirect_url(self, **kwargs):
		# Se obtiene la URL desde la cual se realiza la llamada.
		referer = self.request.META.get('HTTP_REFERER')
		# Se obtiene el usuario dada la clave pasada como parametro
		# "**kwargs".
		user = User.objects.get(pk=self.kwargs['pk'])
		# Si el usuario pretende darse de baja a si mismo.
		if (user==self.request.user):
			return self.request.META.get('HTTP_REFERER')
		# Si el usuario esta activo, simplemente se lo pone en inactivo
		# ("is_active=False").
		if (user.is_active):
			user.is_active = False
			user.save()
		# Si ademas, se viene de la vista de error en alta de usuario,
		# se da de alta al usuario que se pretendia dar de alta en un
		# principio. Para este caso se utiliza el segundo argumento
		# "pk_alt" que consiste en la clave principal del usuario en
		# cuestion (el que se pretendia dar de alta).
		if 'dar-alta/error' in referer:
			return reverse('users:user_subscribe', kwargs={'pk':self.kwargs['pk_alt']})
		# Si se viene de editar el codigo RFID de un usuario.
		# En el segundo argumento ("pk_alt") se pasa un '0' en caso de
		# estar editando el usuario, en caso de creacion se pasa un '1'.
		if self.kwargs['pk_alt'] == '0':
			return reverse('users:user_edit_code_success')
		# En casos contrarios, se retorna de donde se realiza el pedido,
		# ignorando el pedido en caso de que se haya dado de baja, ya
		# que el usuario se encuentra en dicho estado actualmente.
		return self.request.META.get('HTTP_REFERER')


# Vista encargada de dar de alta a un usuario.
class UserSubscribeView(AdminTest, RedirectView):

	# Funcion que define a que URL redirigir el pedido, en este caso
	# se realiza el trabajo y luego se redirige.
	def get_redirect_url(self, **kwargs):
		# Se obtiene el usuario actual, es decir, el que se pretende
		# dar de alta, mediante el la clave pasada como argumento
		# en "**kwargs".
		actual_user = User.objects.get(pk=self.kwargs['pk'])
		# Se obtiene el codigo de la tarjeta RFID del usuario actual.
		code = actual_user.code
		# Se llama a la funcion "get_active_user" para obtener un
		# usuario con el mismo codigo de tarjeta y que se encuentre
		# activo (usuario comparado).
		compare_user = self.get_active_user(code)
		# Si el usuario actual se encuentra ya activo, se ignora el
		# pedido y se retorna a la url desde la cual se vino.
		if (actual_user.is_active):
			return self.request.META.get('HTTP_REFERER')
		# Si el usuario comparado existe y ademas se trata de un
		# usuario que no es de tipo web (usuario sin llavero RFID),
		# se obtiene su clave y se pasa como parametro "**kwargs" a
		# junto con la clave del usuario actual a la url
		# "user_subscribe_error" para el posterior tratamiento.
		elif (compare_user and code != ''):
			pk_alt = compare_user.id
			return reverse('users:user_subscribe_error', 
				kwargs={'pk':self.kwargs['pk'], 'pk_alt':pk_alt})
		# En caso de que el usuario actual sea el unico con el codigo
		# RFID e inactivo, se lo da de alta y se retorna a la lista
		# de usuarios.
		else:
			actual_user.is_active = True
			actual_user.save()
			#return self.request.META.get('HTTP_REFERER')
			return reverse('users:users_list')

	# Funcion que recibe como parametro el codigo RFID y devuelve
	# un usuario en caso de haber alguno con dicho codigo y que
	# ademas se encuentre activo, en caso contrario devuelve
	# None.
	def get_active_user(self,code):
		try:
			user = User.objects.get(code=code, is_active=True)
		except:
			user = None
		return user


# Vista encargada de solucionar el inconveniente en caso de pretender
# dar de alta a un usuario que tiene el mismo codigo RFID que otro y
# que ademas, este otro este activo. Se brinda la posibilidad de dar
# de baja al usuario comparado como asi tambien la posibilidad de
# acceder a los perfiles de los usuarios en cuestion para mayor
# informacion de los mismos.
class UserSubscribeErrorView(AdminTest, TemplateView):

	# El template (HTML) a utilizar.
	template_name = 'users/user_subscribe_error.html'

	# Funcion para obtener el contexto a mostrar en la pagina.
	def get_context_data(self, **kwargs):
		# Se obtiene el usuario actual con el primer argumento.
		actual_user = User.objects.get(pk=self.kwargs['pk'])
		# Se obtiene el usuario comparado con el segundo argumento.
		compare_user = User.objects.get(pk=self.kwargs['pk_alt'])
		# Se agregan los campos al contexto para luego poder
		# utilizarlos en el template. Los campos de interes son
		# tanto las claves como los nombres completos de ambos
		# usuarios.
		context = super(UserSubscribeErrorView, self).get_context_data(**kwargs)
		context['actual_user'] = actual_user.get_full_name()
		context['actual_user_id'] = actual_user.id
		context['compare_user'] = compare_user.get_full_name()
		context['compare_user_id'] = compare_user.id
		return context

#----------------------------------------------------------------------------------------


#----------------------------------------------------------------------------------------
#		Perfil y lista de usuarios
#----------------------------------------------------------------------------------------

# Vista que muestra el perfil del usuario.
class UserDetailView(AdminTest, DetailView):
	model = User


# Vista que muestra la lista de los usuarios registrados.
#
# El template por defecto es "user_list.html", por lo que no es necesario
# especificar un "template_name".
# La variable de contexto por defecto es "object_list" o tambien
# "user_list", formado por el nombre del modelo mas "_list", pero se
# la puede cambiar con el atributo "context_object_name".
class UsersListView(AdminTest, ListView):

	# Se especifica el modelo a utilizar para la ListView, se puede
	# indicar con el atributo "model" o tambien mediante "queryset" donde
	# se puede filtrar la lista de objetos. En este caso se utiliza "model"
	# debido a que no interesa filtrar la lista de objetos y ya esta
	# ordenada por la fecha de alta de los usuarios en el modelo.
	model = User
	# Se utiliza la paginacion para la lista de usuarios sin filtro aplicado.
	#
	# Se pone en veinte usuarios por pagina.
	paginate_by = 20
	# Se cambia el nombre de la pagina en la url.
	page_kwarg = 'pagina'

	# Funcion encargada de eliminar el usuario admin creado en la inicializacion
	# del sistema. Una vez que se loguea un usuario distinto que el admin y
	# acceda a ver la lista de usuarios, borra al admin.
	def dispatch(self, request):
		try:
			user = User.objects.get(pk='1')
			if (request.user != user):
				user.delete()
		except:
			pass
		return super(UsersListView, self).dispatch(request)

	# Funcion encargada de atender solicitudes de tipo "POST", en este caso
	# cuando se presiona el boton "Buscar" o los botones de exportar usuarios.
	def post(self, request):
		# Se obtienen las letras ingresadas en el campo de busqueda.
		search = request.POST.get('search_user')
		# Se obtiene el queryset filtrado por los nombres y apellidos de los usuarios
		# que contengan las letras ingresadas en el campo de busqueda.
		qs = User.objects.filter(
				Q(first_name__icontains=search)|Q(last_name__icontains=search)
				)
		# Si se presiono el boton de "Buscar" pero no se ingreso alguna letra, se
		# retorna a la pagina principal con la lista completa de usuarios y con
		# paginacion activada.
		if 'search' in request.POST and not search:
			return HttpResponseRedirect(reverse('users:users_list'))
		# Si se presiono el boton de "Exportar todos los usuarios".
		elif 'export_all' in request.POST:
			# Los usuarios a exportar son todos.
			users = User.objects.all()
			# Se llama a la funcion encargada de retornar la respuesta.
			return self.get_response(users)
		# Si se presiono el boton de "Exportar los usuarios activos".
		elif 'export_active' in request.POST:
			# Los usuarios a exportar son los activos ("is_active=True").
			users = User.objects.all().filter(is_active=True)
			# Se llama a la funcion encargada de retornar la respuesta.
			return self.get_response(users)
		# En caso de no reconocer la orden.
		else:
			pass
		# Se crea el contexto con el queryset y las letras ingresadas en el campo
		# de busqueda.
		context = {
			'user_list' : qs,
			'name_search' : search,
		}
		# Se muestra el template.
		return render(request, 'users/user_list.html', context)

	# Funcion encargada de generar una respuesta en funcion de un queryset.
	# Esta funcion permite la descarga del archivo csv conteniendo los
	# usuarios pasados en el queryset.
	def get_response(self, users):
		# Se indica al explorador que trate a la respuesta como un archivo
		# adjunto. Se indica el formato mediante "content_type".
		response = HttpResponse(content_type='text/csv')
		# Se especifica la cabecera indicando el nombre del archivo con el
		# que se va a descargar.
		response['Content-Disposition'] = 'attachment; filename="usuarios.csv"'
		# Se crea el objeto escritor responsable de convertir la respuesta
		# en un archivo de tipo csv.
		writer = csv.writer(response)
		# Se crean los titulos de las columnas.
		writer.writerow(['NOMBRE', 'APELLIDO', 'DNI', 'EMAIL', 'TELEFONO'])
		# Se recorren los usuarios del queryset.
		for user in users:
			# Se escriben las filas del archivo csv con el nombre y el
			# apellido del usuario, ambos codificados, y el resto de los campos
			writer.writerow([user.first_name.encode('utf-8'), 
				user.last_name.encode('utf-8'),
				user.identity,
				user.email,
				user.phone])
		# Se retorna la respuesta.
		return response

#----------------------------------------------------------------------------------------



#----------------------------------------------------------------------------------------
#		Franjas horarias
#----------------------------------------------------------------------------------------

# Vista que muestra las franjas horarias actuales.
class TimeZoneListView(AdminTest, ListView):
	# El template por defecto es "timezone_list.html", por lo que se utiliza
	# dicho nombre para el template.
	# Las variables de contexto por defecto es "object_list" o tambien
	# "timezone_list", al igual que el template por defecto.
	# Se indica el modelo a utilizar.
	model = TimeZone


# Vista que permite editar una franja.
class TimeZoneEditView(AdminTest, UpdateView):

	# Modelo a utilizar.
	model = TimeZone
	# Template a utilizar, no se usa el por defecto por cuestion de preferencia
	# de nombre nada mas.
	template_name = 'users/timezone_edit.html'
	# Se indica el formulario a utilizar.
	# Mediante el metodo "modelform_factory" se crea dicho formulario pasando
	# como parametros el modelo, los campos del mismo y se agregan los widgets
	# para seleecion de un dato de tipo tiempo.
	form_class = modelform_factory(TimeZone,
		fields = [
		'zone_name',
		'begin',
		'end',
		],
		widgets={
			'begin': TimeInput,
			'end': TimeInput
		})


# Vista encargada de eliminar una franja, solo pregunta en la pagina
# si se esta seguro que se desea eliminar el elemento.
class TimeZoneDeleteView(AdminTest, DeleteView):

	# El template por defecto es "timezone_confirm_delete.html", por lo que
	# se crea el template con el mismo nombre.
	model = TimeZone
	# Si se elimina el objecto, se vuelve a la lista de franjas horarias.
	success_url = reverse_lazy('users:time_zone_list')

	# Funcion para obtener el contexto a mostrar en la pagina. Se verifica que
	# no sea el turno que se utiliza por defecto ("Ninguno") el que es pretende
	# eliminar.
	def get_context_data(self, **kwargs):
		context = super(TimeZoneDeleteView, self).get_context_data(**kwargs)
		if (self.kwargs['pk'] == '1'):
			context['valid_delete'] = False
		else:
			context['valid_delete'] = True
		return context



# Vista encargada de la creacion de una nueva franja, genera un formulario
# con los campos que se especifican del modelo.
class TimeZoneCreateView(AdminTest, CreateView):

	# Modelo a utilizar.
	model = TimeZone
	# Template a utilizar.
	template_name = 'users/timezone_create.html'
	# Se indica el formulario a utilizar.
	# Mediante el metodo "modelform_factory" se crea dicho formulario pasando
	# como parametros el modelo, los campos del mismo y se agregan los widgets
	# para seleecion de un dato de tipo tiempo.
	form_class = modelform_factory(TimeZone,
		fields = [
		'zone_name',
		'begin',
		'end',
		],
		widgets={
			'begin': TimeInput,
			'end': TimeInput
		})

#----------------------------------------------------------------------------------------
	


#----------------------------------------------------------------------------------------
#		Otros (edicion y olvido de usuario)
#----------------------------------------------------------------------------------------

# Vista utilizada en caso de haber olvidado el usuario.
# Pide ingresar el DNI al usuario y verifica si existe una cuenta
# asociada a dicho DNI, en caso de ser cierto, informa del
# email de dicha cuenta y el estado actual ("is_active").
class ForgetUsernameView(FormView):

	# Formulario a utilizar.
	form_class = ForgetUsernameForm
	# Template que muestra el formulario.
	template_name = 'users/forget_username_form.html'

	# Una vez que el formulario contiene informacion valida.
	def form_valid(self, form):
		# Valor ingresado en el formulario.
		identity = form.cleaned_data['identity']
		# Se obtiene el objecto "User" para el DNI solicitado, en caso de
		# no encontrar alguno, lo pone en "None".
		try:
			user = User.objects.get(identity=identity)
		except:
			user = None
		# Se crea el contexto inicial para los templates a mostrar.
		context = {'identity':identity,}
		# En caso de que exista un usuario con el DNI, se agrega al contexto
		# el email y el estado del mismo.
		if (user):
			context.update({'email':user.email, 'is_active':user.is_active})
		# Se retorna la pagina a mostrar con el contexto generado.
		return render(self.request, 'users/forget_username_done.html', context)


# Vista que muestra el resultado exitoso de la modificacion del codigo RFID del usuario.
class UserCodeEditSuccessView(AdminTest, TemplateView):

	# Template a utilizar
	template_name = 'users/user_edit_code_success.html'


# Vista que muestra el formulario precargado para editar los datos
# del usuario.
class UserEditView(AdminTest, UpdateView):
	
	# Modelo a utilizar
	model = User
	# Template a utilizar
	template_name = 'users/user_edit.html'
	# Los campos del modelo que se muestran para la edicion.
	fields = [
			'first_name',
			'last_name',
			'email',
			'identity',
			'phone',
			'is_staff',
	]

	# Funcion encargada de definir los campos a mostrar en los formularios
	# dependiendo del tipo de usuario que sea, ya que si no es admin, se
	# tienen que poder editar las franjas y la fecha limite tambien.
	def dispatch(self, request, **kwargs):
		if not User.objects.get(pk=self.kwargs['pk']).is_staff:
			self.fields = [
				'first_name',
				'last_name',
				'email',
				'identity',
				'phone',
				'is_staff',
				'expiration_date',
				'monday',
				'tuesday',
				'wednesday',
				'thursday',
				'friday',
				'saturday',
				'sunday',
			]
		return super(UserEditView, self).dispatch(request, **kwargs)
		

	# Funcion que genera el contexto para el template, en este caso interesa
	# utilizar la clave principal del usuario en caso de querer modificar el
	# codigo RFID del mismo, ya sea que se quiera utilizar otro llavero o
	# eliminar el codigo actual, lo que lo transforma en un usuario web.
	# Tambien se obtiene si el usuario es admin o no para poder modificar
	# los campos del formulario a mostrar en la pagina (se utiliza dicho
	# contexto en el template).
	# Ademas se agrega al contexto todos los objectos del modelo "TimeZone"
	# para poder mostrar informacion acerca de los horarios de las franjas
	# en la pagina.
	def get_context_data(self, **kwargs):
		context = super(UserEditView, self).get_context_data(**kwargs)
		context['user_pk'] = self.kwargs['pk']
		user = User.objects.get(pk=self.kwargs['pk'])
		context['user_is_staff'] = user.is_staff
		context['time_zone'] = TimeZone.objects.all()
		return context

#----------------------------------------------------------------------------------------