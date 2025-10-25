from django.contrib import admin
from .models import Baraja, Tarjeta, Programacion, Sesion

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