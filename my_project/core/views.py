from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import date
from .models import Baraja, Tarjeta, Programacion, HistorialRespuesta, Sesion
from .scheduler import SchedulerSM2

# Vista principal - Lista de barajas del usuario
@login_required  # Requiere que el usuario esté autenticado
def lista_barajas(request):
    """
    Muestra todas las barajas del usuario actual.
    """
    barajas = Baraja.objects.filter(propietario=request.user)  # Filtrar barajas del usuario
    return render(request, 'core/lista_barajas.html', {'barajas': barajas})


# Vista para estudiar una baraja
@login_required
def estudiar_baraja(request, baraja_id):
    """
    Muestra las tarjetas pendientes de una baraja para estudiar hoy.
    """
    baraja = get_object_or_404(Baraja, id=baraja_id)  # Obtener baraja o error 404
    
    # Obtener tarjetas pendientes para hoy usando el scheduler
    tarjetas_pendientes = SchedulerSM2.obtener_tarjetas_pendientes(request.user, baraja)
    
    context = {
        'baraja': baraja,
        'tarjetas': tarjetas_pendientes,
        'total_pendientes': tarjetas_pendientes.count()
    }
    
    return render(request, 'core/estudiar_baraja.html', context)


# Vista para calificar una respuesta (AJAX)
@login_required
def calificar_respuesta(request, tarjeta_id):
    """
    Procesa la calificación de una tarjeta y actualiza el scheduler SM-2.
    """
    if request.method == 'POST':
        tarjeta = get_object_or_404(Tarjeta, id=tarjeta_id)
        calificacion = int(request.POST.get('calificacion'))  # 1, 2, 3 o 4
        tiempo_respuesta = int(request.POST.get('tiempo', 0))  # Segundos que tardó
        
        # Obtener o crear la programación de la tarjeta
        programacion, created = Programacion.objects.get_or_create(
            tarjeta=tarjeta,
            defaults={'proximo_estudio': date.today()}
        )
        
        # Aplicar el algoritmo SM-2
        programacion = SchedulerSM2.calcular_siguiente_revision(programacion, calificacion)
        
        # Guardar el historial de respuesta
        HistorialRespuesta.objects.create(
            usuario=request.user,
            tarjeta=tarjeta,
            calificacion=calificacion,
            tiempo_respuesta_segundos=tiempo_respuesta
        )
        
        # Retornar respuesta JSON con la info actualizada
        return JsonResponse({
            'success': True,
            'proximo_estudio': programacion.proximo_estudio.strftime('%Y-%m-%d'),
            'intervalo': programacion.intervalo,
            'ease_factor': programacion.ease_factor
        })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


# Vista del dashboard del usuario
@login_required
def dashboard(request):
    """
    Muestra estadísticas generales del usuario: barajas, tarjetas estudiadas, racha, etc.
    """
    # Obtener todas las barajas del usuario
    barajas = Baraja.objects.filter(propietario=request.user)
    
    # Total de tarjetas en todas las barajas
    total_tarjetas = Tarjeta.objects.filter(baraja__propietario=request.user).count()
    
    # Tarjetas pendientes hoy (en todas las barajas)
    hoy = date.today()
    tarjetas_pendientes = Programacion.objects.filter(
        tarjeta__baraja__propietario=request.user,
        proximo_estudio__lte=hoy
    ).count()
    
    # Tarjetas estudiadas hoy (contar respuestas de hoy)
    from datetime import datetime
    tarjetas_estudiadas_hoy = HistorialRespuesta.objects.filter(
        usuario=request.user,
        fecha_respuesta__date=hoy
    ).count()
    
    # Sesiones recientes (últimas 5)
    sesiones_recientes = Sesion.objects.filter(usuario=request.user).order_by('-fecha_inicio')[:5]
    
    # Obtener perfil del usuario para la racha
    perfil = request.user.perfil if hasattr(request.user, 'perfil') else None
    
    # Calcular estadísticas de respuestas de hoy
    respuestas_hoy = HistorialRespuesta.objects.filter(
        usuario=request.user,
        fecha_respuesta__date=hoy
    )
    
    # Contar por tipo de calificación
    otra_vez = respuestas_hoy.filter(calificacion=1).count()
    dificil = respuestas_hoy.filter(calificacion=2).count()
    bien = respuestas_hoy.filter(calificacion=3).count()
    facil = respuestas_hoy.filter(calificacion=4).count()
    
    context = {
        'total_barajas': barajas.count(),
        'total_tarjetas': total_tarjetas,
        'tarjetas_pendientes': tarjetas_pendientes,
        'tarjetas_estudiadas_hoy': tarjetas_estudiadas_hoy,
        'sesiones_recientes': sesiones_recientes,
        'racha_dias': perfil.racha_dias if perfil else 0,
        'estadisticas_hoy': {
            'otra_vez': otra_vez,
            'dificil': dificil,
            'bien': bien,
            'facil': facil,
        }
    }
    
    return render(request, 'core/dashboard.html', context)

# Vista para buscar tarjetas
@login_required
def buscar_tarjetas(request):
    """
    Busca tarjetas por texto en anverso/reverso o por etiquetas.
    """
    query = request.GET.get('q', '')  # Obtener el término de búsqueda de la URL
    resultados = []
    
    if query:
        # Buscar en tarjetas del usuario (en anverso, reverso o etiquetas)
        resultados = Tarjeta.objects.filter(
            baraja__propietario=request.user  # Solo tarjetas del usuario
        ).filter(
            # Buscar en anverso O reverso O etiquetas
            anverso__icontains=query  # icontains = insensible a mayúsculas
        ) | Tarjeta.objects.filter(
            baraja__propietario=request.user
        ).filter(
            reverso__icontains=query
        ) | Tarjeta.objects.filter(
            baraja__propietario=request.user
        ).filter(
            etiquetas__icontains=query
        )
        
        # Eliminar duplicados y ordenar
        resultados = resultados.distinct().order_by('baraja__titulo', 'anverso')
    
    context = {
        'query': query,
        'resultados': resultados,
        'total_resultados': resultados.count() if resultados else 0
    }
    
    return render(request, 'core/buscar_tarjetas.html', context)