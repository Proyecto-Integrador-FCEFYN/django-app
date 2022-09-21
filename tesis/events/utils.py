# -*- coding: utf-8 -*-
from django.utils import timezone

# Para el manejo de las respuestas a los pedidos.
from django.http import HttpResponse

# Para exportar los eventos en archivos csv.
import csv
# Para el manejo de fechas y horas.
import datetime
# Para las zonas horarias.
import pytz



#----------------------------------------------------------------------------------------
#		Funciones reutilizadas
#----------------------------------------------------------------------------------------

# Funcion encargada de obtener el contexto para los templates de eventos en caso de
# utilizar el filtro. Recibe como parametro la fecha de inicio ("begin") y
# fin ("end") segun se haya ingresado en el filtro, junto al modelo del evento y
# un "user" en caso de tratarse de los eventos del usuario.
def get_event_context_for_filter(begin, end, event_model, user=None):
	# Variables utilizadas para indicar en que rango de fechas se muestran los
	# eventos en la pagina, por defecto son igual a los parametros recibidos.
	# En realidad, si no se selecciona alguna fecha en el filtro y se intenta filtrar,
	# el parametro no seleccionado no se va a mostrar en la pagina, ya que no es de
	# interes.
	begin_formatted = begin
	end_formatted = end
	# Las fechas seleccionadas en el filtro son del tipo unicode, por lo que para
	# comparar con el campo "date_time" del modelo, lo ideal es convertirlo a tipo
	# "datetime", y ademas que sea "aware" (o sea que contenga la zona horaria).
	# Ademas, se da distinto formato a la fecha seleccionada para poder mostrarlo
	# correctamente luego, esto es debido a que el filtro por mas que se vea con
	# el formato "dia-mes-año", en realidad retorna "año-mes-dia".
	#
	# Si es que se selecciono alguna fecha de inicio.
	if begin != '':
		begin_aware = get_aware_datetime_from_unicode(begin)
		begin_formatted = begin_aware.strftime('%d-%m-%Y')
	# Si es que se selecciono alguna fecha de fin.
	if end != '':
		end_aware = get_aware_datetime_from_unicode(end)
		end_formatted = end_aware.strftime('%d-%m-%Y')
	# Hay cuatro posiblidades segun el filtro aplicado. Ademas, en cada caso tambien
	# se agrega el filtro por "user" en caso de tratarse de los eventos del usuario.
	#
	# Si no se selecciona fecha alguna y se presiona filtrar de todas formas, se
	# muestran todos los eventos, al igual que cuando se ingresa por primera vez
	# a la pagina.
	if begin == '' and end == '':
		if user:
			object_list = event_model.objects.filter(user=user)
		else:
			object_list = event_model.objects.all()
	# Si se selecciona unicamente una fecha de fin, se muestran los eventos hasta
	# la fecha solicitada.
	elif begin == '':
		if user:
			object_list = event_model.objects.filter(date_time__lte = end_aware, user=user)
		else:
			object_list = event_model.objects.filter(date_time__lte = end_aware)
	# Si se selecciona unicamente una fecha de inicio, se muestran los eventos a
	# partir de dicha fecha.
	elif end == '':
		if user:
			object_list = event_model.objects.filter(date_time__gte = begin_aware, user=user)
		else:
			object_list = event_model.objects.filter(date_time__gte = begin_aware)
	# Si se seleccionan ambas fechas, se muestran los eventos comprendidos entre
	# dichas fechas.
	else:
		if user:
			object_list = event_model.objects.filter(date_time__range=(begin_aware, end_aware), user=user)
		else:
			object_list = event_model.objects.filter(date_time__range=(begin_aware, end_aware))
	# Se arma el contexto conteniendo la lista de objetos, las fechas elegidas (para
	# mostrar como valores por defecto en las fechas del filtro) y las fechas
	# formateadas en caso de que alguna haya sido seleccionada.
	context = {
		'object_list' : object_list,
		'begin' : begin,
		'end' : end,
		'begin_formatted' : begin_formatted,
		'end_formatted' : end_formatted,
	}
	return context


# Funcion encargada de generar un tipo de dato "datetime.datetime" de tipo "aware"
# dado una fecha en unicode.
def get_aware_datetime_from_unicode(value):
	# Se especifica la franja horaria.
	tz = pytz.timezone('America/Argentina/Cordoba')
	# Se transforma de unicode a "datetime.datetime". Si bien se selecciona un tipo
	# "date", se lo convierte para poder convertir de "naive" a "aware".
	value = datetime.datetime.strptime(value, '%Y-%m-%d')
	# Se convierte a tipo "aware".
	value = timezone.make_aware(value, tz)
	return value


# Funcion encargada de retornar la respuesta en caso de exportar los eventos a un
# archivo csv. Dependiendo del tipo de evento, es el nombre del archivo csv y
# las columnas del mismo.
def get_response(events, event_type):
	# Se especifica el tipo de respuesta.
	response = HttpResponse(content_type='text/csv')
	# Dependiendo del tipo de evento, se especifica la cabecera indicando el nombre
	# del archivo con el que se va a descargar; ademas de ubicar dicho evento
	# dentro de un grupo que separa los eventos que incluyen usuario de los que no.
	if event_type == 'PermittedAccess':
		response['Content-Disposition'] = 'attachment; filename="ingresos con llavero.csv"'
		type = 2
	elif event_type == 'WebOpenDoor':
		response['Content-Disposition'] = 'attachment; filename="aperturas de puerta via web.csv"'
		type = 2
	elif event_type == 'DeniedAccess':
		response['Content-Disposition'] = 'attachment; filename="accesos denegados.csv"'
		type = 1
	elif event_type == 'Button':
		response['Content-Disposition'] = 'attachment; filename="toques de timbre.csv"'
		type = 1
	elif event_type == 'Movement':
		response['Content-Disposition'] = 'attachment; filename="detecciones de movimiento .csv"'
		type = 1
	# Si no se logra determinar el tipo de evento.
	else:
		type = 0
		pass
	# Se crea el objeto escritor responsable de convertir la respuesta
	# en un archivo de tipo csv.
	writer = csv.writer(response)
	# Si el evento consta unicamente de la fecha y hora.
	if type == 1:
		# Se crean los titulos de las columnas.
		writer.writerow(['FECHA Y HORA EN UTC', 'DISPOSITIVO', 'IMAGEN'])
		# Se recorren los usuarios del queryset.
		for event in events:
			# Se escriben las filas del archivo csv con la fecha y hora del evento junto al
			# nombre de la imagen.
			writer.writerow([event.date_time, event.device.device_name, str(event.image)])
	# Si el evento consta de la fecha, hora y el usuario.
	elif type == 2:
		# Se crean los titulos de las columnas.
		writer.writerow(['FECHA Y HORA EN UTC', 'NOMBRE', 'APELLIDO', 'DISPOSITIVO', 'IMAGEN'])
		# Se recorren los usuarios del queryset.
		for event in events:
			# Se escriben las filas del archivo csv con la fecha y hora del evento
			# junto al nombre y apellido del usuario y el nombre de la imagen.
			writer.writerow([event.date_time,
				event.user.first_name,
				event.user.last_name,
				event.device.device_name,
				# Se separa el path relativo de la imagen y se obtiene unicamente el
				# nombre de la misma.
				str(event.image)])
	# Si no se logra determinar el contenido del evento.
	else:
		pass
	# Se retorna la respuesta.
	return response

#----------------------------------------------------------------------------------------