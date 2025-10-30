from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard y funcionalidades principales
    path('', views.dashboard, name='dashboard'),
    path('barajas/', views.lista_barajas, name='lista_barajas'),
    path('estudiar/<int:baraja_id>/', views.estudiar_baraja, name='estudiar_baraja'),
    path('calificar/<int:tarjeta_id>/', views.calificar_respuesta, name='calificar_respuesta'),
    path('buscar/', views.buscar_tarjetas, name='buscar_tarjetas'),
    path('importar-csv/', views.importar_csv, name='importar_csv'),
    path('exportar-csv/<int:baraja_id>/', views.exportar_csv, name='exportar_csv'),
    
    # Sistema de clases
    path('clases/', views.mis_clases, name='mis_clases'),
    path('clases/<int:clase_id>/', views.detalle_clase, name='detalle_clase'),
    path('clases/<int:clase_id>/progreso/', views.progreso_clase, name='progreso_clase'),
    path('unirse-clase/', views.unirse_clase, name='unirse_clase'),
    
    # Cambiar rol
    path('cambiar-rol/', views.cambiar_rol, name='cambiar_rol'),
]