# -*- coding: utf-8 -*-
from django import forms

# Para obtener el modelo de usuario del proyecto.
from django.contrib.auth import get_user_model
# Para reemplazar algunos parametros y metodos del formulario de autenticacion original.
from django.contrib.auth.forms import AuthenticationForm
# Para los formularios basados en modelos.
from django.forms import ModelForm

# Se importan las funciones creadas para esta aplicacion.
from .utils import *

import logging
logger = logging.getLogger("mylogger")

# Para utilizar el usuario modificado en vez del auth.User.
User = get_user_model()



# Alteracion del formulario de autenticacion del usuario.
class ErrorsHandleAuthenticationForm(AuthenticationForm):

    # Se modifica widget para el nombre del usuario por tipo "EmailInput".
    username = forms.CharField(label='Email', widget=forms.EmailInput)
    # Se modifica el mensaje de error en el logueo por defecto.
    error_messages = {
        'invalid_login': 'El usuario y la contraseña no son correctos.',
    }
    
    # Funcion que controla cuando un usuario se puede loguear. Estas
    # Esta funcion se reescribe para agregar el control de las franjas horarias.
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError('El usuario se encuentra inactivo.',
                code='inactive')
        if not user.is_staff:
            if not time_zone_test(user):
                raise forms.ValidationError('No se encuentra dentro de su'
                    ' franja horaria.')


# Formulario para el registro de un nuevo usuario.
class UserCreationForm(forms.ModelForm):
    class Meta:
        # El modelo a utilizar.
        model = User
        # Campos del modelo a mostrar en formulario, el campo "is_active"
        # no se muestra debido a que por defecto se lo pone en "True".
        # Los demas campos se crean en las vistas de los pasos posteriores.

        fields = (
			'first_name',
			'last_name',
			'email',
			'identity',
			'phone',
		)

    # Funcion encargada de registrar el nuevo usuario en la base de datos.
    def save(self, commit=True):
        # Se llama a la implementacion base primero para obtener el contexto.
        # Indicando "commit=False" indica que el objeto no se va a guardar en la
        # base de datos.
        user = super(UserCreationForm, self).save(commit=False)
        if commit:
            # Se fuerza a que el nombre y el apellido esten capitalizados.
            user.first_name = user.first_name.title()
            user.last_name = user.last_name.title()
            # Se almacena efectivamente el nuevo usuario en la base de datos.
            user.save()
        return user

    # Funcion encargada de obtener la clave primaria del usuario en creacion.
    def get_pk(self):
        user = super(UserCreationForm, self).save(commit=False)
        return user.pk

    # Funcion encargada de obtener el atributo "is_staff" del usuario en creacion.
    def get_is_staff(self):
        user = super(UserCreationForm, self).save(commit=False)
        return user.is_staff


# Clase para el widget de selector de fecha.
class DateInput(forms.DateInput):
    input_type = 'date'


# Clase para el widget de selector de hora.
class TimeInput(forms.TimeInput):
    input_type = 'time'


# Formulario para las franjas horarias de los usuarios que no son admin.
class UserTimeZoneForm(forms.ModelForm):

    class Meta:
        # El modelo a utilizar.
        model = User
        # Campos del modelo a mostrar en formulario.
        fields = (
            'expiration_date',
            'monday',
            'tuesday',
            'wednesday',
            'thursday',
            'friday',
            'saturday',
            'sunday',
        )
        # Widget para la fecha limite que permite seleccionar una fecha mediante
        # un calendario.
        widgets = {
            'expiration_date': DateInput()
        }


# Formulario en caso de haber olvidado el usuario, pide unicamente su DNI.
class ForgetUsernameForm(forms.Form):
    identity = forms.CharField(label='DNI', max_length=8)