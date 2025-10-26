from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from datetime import date
from .models import Baraja, Clase, Tarea, Tarjeta, Programacion, HistorialRespuesta, Sesion
from .scheduler import SchedulerSM2
from .decorators import rol_requerido, solo_docente

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

# Vista para importar tarjetas desde CSV
@login_required
def importar_csv(request):
    """
    Importa tarjetas desde un archivo CSV.
    Formato esperado: anverso,reverso,etiquetas,baraja_id
    """
    if request.method == 'POST':
        import csv
        from io import StringIO
        
        # Obtener el archivo subido
        csv_file = request.FILES.get('archivo_csv')
        baraja_id = request.POST.get('baraja_id')
        
        if not csv_file:
            return render(request, 'core/importar_csv.html', {
                'error': 'Por favor selecciona un archivo CSV',
                'barajas': Baraja.objects.filter(propietario=request.user)
            })
        
        if not baraja_id:
            return render(request, 'core/importar_csv.html', {
                'error': 'Por favor selecciona una baraja',
                'barajas': Baraja.objects.filter(propietario=request.user)
            })
        
        # Verificar que la baraja pertenece al usuario
        try:
            baraja = Baraja.objects.get(id=baraja_id, propietario=request.user)
        except Baraja.DoesNotExist:
            return render(request, 'core/importar_csv.html', {
                'error': 'Baraja no encontrada',
                'barajas': Baraja.objects.filter(propietario=request.user)
            })
        
        # Leer el archivo CSV
        try:
            # Decodificar el archivo
            file_data = csv_file.read().decode('utf-8')
            csv_data = StringIO(file_data)
            reader = csv.DictReader(csv_data)
            
            tarjetas_creadas = 0
            errores = []
            
            # Procesar cada fila del CSV
            for row_num, row in enumerate(reader, start=2):  # start=2 porque la fila 1 es el encabezado
                try:
                    anverso = row.get('anverso', '').strip()
                    reverso = row.get('reverso', '').strip()
                    etiquetas = row.get('etiquetas', '').strip()
                    
                    # Validar que tenga al menos anverso y reverso
                    if not anverso or not reverso:
                        errores.append(f'Fila {row_num}: Falta anverso o reverso')
                        continue
                    
                    # Crear la tarjeta
                    Tarjeta.objects.create(
                        baraja=baraja,
                        anverso=anverso,
                        reverso=reverso,
                        etiquetas=etiquetas
                    )
                    tarjetas_creadas += 1
                    
                except Exception as e:
                    errores.append(f'Fila {row_num}: {str(e)}')
            
            # Mostrar resultado
            mensaje_exito = f'✅ Se importaron {tarjetas_creadas} tarjetas correctamente'
            return render(request, 'core/importar_csv.html', {
                'exito': mensaje_exito,
                'errores': errores if errores else None,
                'barajas': Baraja.objects.filter(propietario=request.user)
            })
            
        except Exception as e:
            return render(request, 'core/importar_csv.html', {
                'error': f'Error al procesar el archivo: {str(e)}',
                'barajas': Baraja.objects.filter(propietario=request.user)
            })
    
    # GET request - mostrar formulario
    return render(request, 'core/importar_csv.html', {
        'barajas': Baraja.objects.filter(propietario=request.user)
    })

# Vista para exportar tarjetas a CSV
@login_required
def exportar_csv(request, baraja_id):
    """
    Exporta todas las tarjetas de una baraja a formato CSV.
    """
    import csv
    from django.http import HttpResponse
    
    # Obtener la baraja (verificar que pertenece al usuario)
    try:
        baraja = Baraja.objects.get(id=baraja_id, propietario=request.user)
    except Baraja.DoesNotExist:
        return HttpResponse('Baraja no encontrada', status=404)
    
    # Crear la respuesta HTTP como archivo CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{baraja.titulo}.csv"'
    
    # Configurar para usar UTF-8 con BOM (para que Excel lo abra correctamente)
    response.write('\ufeff')  # BOM para UTF-8
    
    # Crear el escritor CSV
    writer = csv.writer(response)
    
    # Escribir encabezados
    writer.writerow(['anverso', 'reverso', 'etiquetas', 'extra', 'tipo'])
    
    # Escribir todas las tarjetas de la baraja
    tarjetas = Tarjeta.objects.filter(baraja=baraja).order_by('fecha_creacion')
    
    for tarjeta in tarjetas:
        writer.writerow([
            tarjeta.anverso,
            tarjeta.reverso,
            tarjeta.etiquetas,
            tarjeta.extra,
            tarjeta.tipo
        ])
    
    return response

# ==================== VISTAS PARA SISTEMA DE CLASES ====================

# Vista para listar clases del docente
@login_required
def mis_clases(request):
    """
    Muestra las clases donde el usuario es docente o alumno.
    """
    # Clases donde soy docente
    clases_docente = Clase.objects.filter(docente=request.user)
    
    # Clases donde soy alumno
    clases_alumno = Clase.objects.filter(alumnos=request.user)
    
    context = {
        'clases_docente': clases_docente,
        'clases_alumno': clases_alumno,
    }
    
    return render(request, 'core/mis_clases.html', context)


# Vista para ver detalles de una clase
@login_required
def detalle_clase(request, clase_id):
    """
    Muestra los detalles de una clase: alumnos, tareas, etc.
    """
    from django.shortcuts import get_object_or_404
    
    clase = get_object_or_404(Clase, id=clase_id)
    
    # Verificar que el usuario es docente o alumno de la clase
    es_docente = clase.docente == request.user
    es_alumno = request.user in clase.alumnos.all()
    
    if not (es_docente or es_alumno):
        return HttpResponse('No tienes acceso a esta clase', status=403)
    
    # Obtener tareas de la clase
    tareas = Tarea.objects.filter(clase=clase).order_by('-fecha_creacion')
    
    context = {
        'clase': clase,
        'es_docente': es_docente,
        'es_alumno': es_alumno,
        'tareas': tareas,
    }
    
    return render(request, 'core/detalle_clase.html', context)


# Vista para unirse a una clase con código
@login_required
def unirse_clase(request):
    """
    Permite a un alumno unirse a una clase usando el código de invitación.
    """
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().upper()
        
        try:
            clase = Clase.objects.get(codigo_invitacion=codigo)
            
            # Verificar que no sea el docente
            if clase.docente == request.user:
                return render(request, 'core/unirse_clase.html', {
                    'error': 'No puedes unirte a tu propia clase como alumno'
                })
            
            # Verificar que no esté ya inscrito
            if request.user in clase.alumnos.all():
                return render(request, 'core/unirse_clase.html', {
                    'error': 'Ya estás inscrito en esta clase'
                })
            
            # Agregar al alumno
            clase.alumnos.add(request.user)
            
            return render(request, 'core/unirse_clase.html', {
                'exito': f'¡Te has unido exitosamente a la clase "{clase.nombre}"!',
                'clase': clase
            })
            
        except Clase.DoesNotExist:
            return render(request, 'core/unirse_clase.html', {
                'error': 'Código de clase inválido'
            })
    
    return render(request, 'core/unirse_clase.html', {})


# Vista para ver progreso de alumnos (solo docentes)
@login_required
@solo_docente
def progreso_clase(request, clase_id):
    """
    Muestra el progreso de todos los alumnos en las tareas de la clase.
    Solo accesible para el docente.
    """
    from django.shortcuts import get_object_or_404
    
    clase = get_object_or_404(Clase, id=clase_id, docente=request.user)
    
    # Obtener todas las tareas de la clase
    tareas = Tarea.objects.filter(clase=clase)
    
    # Obtener progreso de cada alumno
    alumnos_progreso = []
    
    for alumno in clase.alumnos.all():
        # Contar tarjetas estudiadas de cada tarea
        progreso_tareas = []
        
        for tarea in tareas:
            # Contar cuántas tarjetas de la baraja de la tarea ha estudiado el alumno
            tarjetas_estudiadas = HistorialRespuesta.objects.filter(
                usuario=alumno,
                tarjeta__baraja=tarea.baraja,
                fecha_respuesta__gte=tarea.fecha_creacion
            ).values('tarjeta').distinct().count()
            
            total_tarjetas = tarea.baraja.tarjetas.count()
            porcentaje = (tarjetas_estudiadas / total_tarjetas * 100) if total_tarjetas > 0 else 0
            
            progreso_tareas.append({
                'tarea': tarea,
                'estudiadas': tarjetas_estudiadas,
                'total': total_tarjetas,
                'porcentaje': round(porcentaje, 1)
            })
        
        alumnos_progreso.append({
            'alumno': alumno,
            'progreso_tareas': progreso_tareas
        })
    
    context = {
        'clase': clase,
        'tareas': tareas,
        'alumnos_progreso': alumnos_progreso,
    }
    
    return render(request, 'core/progreso_clase.html', context)