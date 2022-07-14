# -*- coding: utf-8 -*-
# Para el control de las franjas horarias.
from .models import TimeZone

# Para el manejo de los horarios en el test de las franjas horarias.
import datetime



# Funcion que verifica que la hora actual se encuentre comprendida en el
# rango de horario del dia de la franja horaria del usuario correspondiente.
def time_zone_test(user):
    
    # Se obtiene el dia de hoy, en minusculas.
    # La funcion "datetime.datetime.now()" devuelve un tipo de dato
    # datetime.datetime de tipo "naive", y luego mediante "strftime('%A')" 
    # se lo convierte a string y se obtiene unicamente el dia de la semana,
    # y finalmente con "lower()" se lo pone en minusculas.
    today = datetime.datetime.now().strftime('%A').lower()
    # Se obtiene la hora actual.
    # Devuelve un tipo de dato "datetime.time" de tipo "naive".
    time_now = datetime.datetime.now().time()
    # Se obtiene el atributo especificado por el string "today" del usuario, lo
    # que va a dar la franja horaria del dia de hoy.
    user_today_time_zone = getattr(user,today)
    # Se obtiene la franja horaria.
    time_zone = TimeZone.objects.get(zone_name=user_today_time_zone)
    # Se obtiene la hora de principio de la franja.
    begin = time_zone.begin
    # Hora del final de la franja.
    end = time_zone.end
    # Si la hora actual esta dentro de la franja.
    if (begin <= time_now <= end):
        return True
    # En caso de no ser posible verificar la franja se prohibe el acceso.
    else:
        return False