# -*- coding: utf-8 -*-
from django import forms
# Para los formularios basados en modelos.
from django.forms import ModelForm

# Se importan las funciones creadas para esta aplicacion.
from .models import *


import logging
logger = logging.getLogger("mylogger")

class DeviceForm(forms.ModelForm):
    password=forms.CharField(widget=forms.PasswordInput())
    confirmar_password=forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = Device
        fields=('usuario','password')

    def clean(self):
        cleaned_data = super(DeviceForm, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirmar_password")

        if password != confirm_password:
            raise forms.ValidationError(
                "password and confirm_password does not match"
            )
