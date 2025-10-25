from django.contrib import admin
from .models import Baraja, Tarjeta, Programacion, Sesion, PerfilUsuario, Clase, Tarea, HistorialRespuesta

@admin.register(Baraja)
class BarajaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'propietario', 'visibilidad', 'fecha_creacion')
    list_filter = ('visibilidad', 'fecha_creacion')
    search_fields = ('titulo', 'descripcion')

@admin.register(Tarjeta)
class TarjetaAdmin(admin.ModelAdmin):
    list_display = ('baraja', 'tipo', 'anverso', 'fecha_creacion')
    list_filter = ('tipo', 'baraja')
    search_fields = ('anverso', 'reverso', 'etiquetas')

@admin.register(Programacion)
class ProgramacionAdmin(admin.ModelAdmin):
    list_display = ('tarjeta', 'ease_factor', 'intervalo', 'proximo_estudio')
    list_filter = ('proximo_estudio',)

@admin.register(Sesion)
class SesionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'baraja', 'fecha_inicio', 'duracion_minutos', 'tarjetas_estudiadas')
    list_filter = ('fecha_inicio', 'usuario')

# Registro de Perfil de Usuario en el admin
@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol', 'idioma', 'racha_dias', 'modo_oscuro')  # Columnas a mostrar
    list_filter = ('rol', 'idioma', 'modo_oscuro')  # Filtros laterales
    search_fields = ('usuario__username', 'usuario__email')  # Búsqueda por usuario

# Registro de Clase en el admin
@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'docente', 'codigo_invitacion', 'fecha_creacion')  # Columnas visibles
    list_filter = ('fecha_creacion',)  # Filtro por fecha
    search_fields = ('nombre', 'descripcion', 'docente__username')  # Búsqueda
    filter_horizontal = ('alumnos',)  # Interfaz para seleccionar múltiples alumnos fácilmente

# Registro de Tarea en el admin
@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'clase', 'baraja', 'fecha_limite', 'fecha_creacion')  # Columnas
    list_filter = ('fecha_limite', 'clase')  # Filtros
    search_fields = ('titulo', 'descripcion')  # Búsqueda

# Registro de Historial de Respuestas en el admin
@admin.register(HistorialRespuesta)
class HistorialRespuestaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tarjeta', 'calificacion', 'fecha_respuesta', 'tiempo_respuesta_segundos')  # Columnas
    list_filter = ('calificacion', 'fecha_respuesta', 'usuario')  # Filtros
    search_fields = ('usuario__username', 'tarjeta__anverso')  # Búsqueda
    readonly_fields = ('fecha_respuesta',)  # Campo de solo lectura (no editable)