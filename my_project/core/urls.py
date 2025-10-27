from django.urls import path
from . import views

# Nombre de la app para usar en los templates (namespace)
app_name = 'core'

# Definición de todas las rutas de la aplicación
urlpatterns = [
    # Dashboard principal - http://localhost:8000/
    path('', views.dashboard, name='dashboard'),
    
    # Lista de barajas - http://localhost:8000/barajas/
    path('barajas/', views.lista_barajas, name='lista_barajas'),
    
    # Estudiar una baraja específica - http://localhost:8000/estudiar/1/
    path('estudiar/<int:baraja_id>/', views.estudiar_baraja, name='estudiar_baraja'),
    
    # Calificar una respuesta (AJAX) - http://localhost:8000/calificar/1/
    path('calificar/<int:tarjeta_id>/', views.calificar_respuesta, name='calificar_respuesta'),

    # ruta para hacer la busqueda de tarjetas
    path('buscar/', views.buscar_tarjetas, name='buscar_tarjetas'),

    # ruta para importar archivos CSV
    path('importar-csv/', views.importar_csv, name='importar_csv'),

    # Exportacion de CSV
    path('exportar-csv/<int:baraja_id>/', views.exportar_csv, name='exportar_csv'),

        # URLs del sistema de clases
    path('clases/', views.mis_clases, name='mis_clases'),
    path('clases/<int:clase_id>/', views.detalle_clase, name='detalle_clase'),
    path('clases/<int:clase_id>/progreso/', views.progreso_clase, name='progreso_clase'),
    path('unirse-clase/', views.unirse_clase, name='unirse_clase'),

    # Cambiar rol
    path('cambiar-rol/', views.cambiar_rol, name='cambiar_rol'),

]