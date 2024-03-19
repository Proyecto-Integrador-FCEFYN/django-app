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
from .models import *

import logging
logger = logging.getLogger("mylogger")

class DeviceForm(forms.ModelForm):
    password=forms.CharField(widget=forms.PasswordInput())
    confirm_password=forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = Device
        fields=('username','password')

    def clean(self):
        cleaned_data = super(DeviceForm, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError(
                "password and confirm_password does not match"
            )
