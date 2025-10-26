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
]