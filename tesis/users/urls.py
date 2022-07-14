# -*- coding: utf-8 -*-
from django.conf.urls import url
# Se importan todas las vistas de auth ya que se utilizan la mayoria.
from django.contrib.auth import views as auth_views
# Se importa la funcion unicamente para modificar un atributo de algunas vistas de auth.
from django.urls import reverse_lazy

from . import views
# Se importa el formulario de la autenticacion del usuario modificado.
from .forms import ErrorsHandleAuthenticationForm

app_name='users'
urlpatterns=[
	# Las URLs para loguearse y salir del sistema. Se utilizan las vistas del sistema
	# de autenticacion del django (auth), y en el caso del logueo se modifica el template
	# a utilizar como asi tambien el formulario, ya que se modifica el formulario original.

	url(r'^acceder/$', auth_views.LoginView.as_view(template_name='users/login.html', authentication_form=ErrorsHandleAuthenticationForm), name='login'),
	url(r'^salir/$', auth_views.LogoutView.as_view(), name='logout'),

	# Las URLs en caso de querer modificar la contraseña. Se utilizan las vistas y formularios del sistema
	# de autenticacion del django (auth), solo se modifican ciertos atributos.
	
	url(r'^usuarios/cambiar-clave/$', auth_views.PasswordChangeView.as_view(
			template_name='users/password_change_form.html',
			success_url=reverse_lazy('users:password_change_done')),
		name='password_change'),
	url(r'^usuarios/cambiar-clave/exito/$', auth_views.PasswordChangeDoneView.as_view(
			template_name='users/password_change_done.html'),
		name='password_change_done'),

	# Las URLs en caso de haber olvidado la contraseña. Se utilizan las vistas y formularios del sistema
	# de autenticacion del django (auth), solo se modifican ciertos atributos.

	# Se pide ingresar el email para enviar el link de validacion.
	url(r'^acceder/olvide-clave/$', auth_views.PasswordResetView.as_view(
			template_name='users/password_reset_form.html', 
			email_template_name='users/password_reset_email.html', 
			subject_template_name='users/password_reset_subject.txt', 
			success_url=reverse_lazy('users:password_reset_done')), 
		name='password_reset'),
	# Una vez enviado el mail, se notifica de los pasos a seguir.
    url(r'^acceder/olvide-clave/notificado/$', auth_views.PasswordResetDoneView.as_view(
    		template_name='users/password_reset_done.html'), 
    	name='password_reset_done'),
    # Una vez que se accede a la URL enviada por mail, se prosigue a la creacion de una nueva
    # contraseña.
    url(r'^acceder/olvide-clave/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', 
    		auth_views.PasswordResetConfirmView.as_view(
    			template_name='users/password_reset_confirm.html', 
    			success_url=reverse_lazy('users:password_reset_complete')), 
    		name='password_reset_confirm'),
    # Una vez que se creo la nueva contraseña, se da por concluida la operacion.
    url(r'^acceder/olvide-clave/exito/$', auth_views.PasswordResetCompleteView.as_view(
    		template_name='users/password_reset_complete.html'), 
    	name='password_reset_complete'),

    # URL para en caso de olvidar el usuario, verifica tambien que este activo.
    url(r'^acceder/olvide-usuario/$', views.ForgetUsernameView.as_view(), name='forget_username'),
    # URLS para la creacion de un nuevo usuario, el paso 3 se reutiliza para editar la clave RFID
    # actual de un usuario previamente creado.
	url(r'^usuarios/registro-paso-1/$', views.UserRegisterStep1View.as_view(),
		name='user_register_step_1'),
	url(r'^usuarios/registro-paso-2/(?P<pk>[0-9]+)/$', views.UserRegisterStep2View.as_view(),
		name='user_register_step_2'),
	url(r'^usuarios/registro-paso-3/(?P<pk>[0-9]+)/$', views.UserRegisterStep3View.as_view(),
		name='user_register_step_3'),
	url(r'^usuarios/registro-paso-4/(?P<pk>[0-9]+)/$', views.UserRegisterStep4View.as_view(),
		name='user_register_step_4'),

	# URLS para dar de baja y alta un usuario.
	url(r'^usuarios/dar-baja/(?P<pk>[0-9]+)-(?P<pk_alt>[0-9]+)/$', views.UserUnsubscribeView.as_view(),
		name='user_unsubscribe'),
	url(r'^usuarios/dar-alta/(?P<pk>[0-9]+)/$', views.UserSubscribeView.as_view(),
		name='user_subscribe'),
	url(r'^usuarios/dar-alta/error/(?P<pk>[0-9]+)-(?P<pk_alt>[0-9]+)/$', views.UserSubscribeErrorView.as_view(),
		name='user_subscribe_error'),

	url(r'^usuarios/editar-codigo/exito/$', views.UserCodeEditSuccessView.as_view(),
		name='user_edit_code_success'),

	# URLS para el manejo de las franjas horarias.
	url(r'^usuarios/franjas-horarias/$', views.TimeZoneListView.as_view(),
		name='time_zone_list'),
	url(r'^usuarios/franjas-horarias/editar/(?P<pk>[0-9]+)/$', views.TimeZoneEditView.as_view(),
		name='time_zone_edit'),
	url(r'^usuarios/franjas-horarias/eliminar/(?P<pk>[0-9]+)/$', views.TimeZoneDeleteView.as_view(),
		name='time_zone_delete'),
	url(r'^usuarios/franjas-horarias/crear/$', views.TimeZoneCreateView.as_view(),
		name='time_zone_create'),

	url(r'^usuarios/lista/$', views.UsersListView.as_view(), name='users_list'),
	url(r'^usuarios/editar/(?P<pk>[0-9]+)/$', views.UserEditView.as_view(), name='user_edit'),
	url(r'^usuarios/perfil/(?P<pk>[0-9]+)/$', views.UserDetailView.as_view(), name='user_detail'),
	
]