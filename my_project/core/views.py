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
    barajas = Baraja.objects.filter(propietario=request.user)
    total_tarjetas = Tarjeta.objects.filter(baraja__propietario=request.user).count()
    
    # Tarjetas pendientes hoy (en todas las barajas)
    hoy = date.today()
    tarjetas_pendientes = Programacion.objects.filter(
        tarjeta__baraja__propietario=request.user,
        proximo_estudio__lte=hoy
    ).count()
    
    # Sesiones recientes
    sesiones_recientes = Sesion.objects.filter(usuario=request.user).order_by('-fecha_inicio')[:5]
    
    # Obtener perfil del usuario para la racha
    perfil = request.user.perfil if hasattr(request.user, 'perfil') else None
    
    context = {
        'total_barajas': barajas.count(),
        'total_tarjetas': total_tarjetas,
        'tarjetas_pendientes': tarjetas_pendientes,
        'sesiones_recientes': sesiones_recientes,
        'racha_dias': perfil.racha_dias if perfil else 0
    }
    
    return render(request, 'core/dashboard.html', context)