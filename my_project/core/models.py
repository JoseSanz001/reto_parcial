from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Modelo de Baraja
class Baraja(models.Model):
    VISIBILIDAD_CHOICES = [
        ('privada', 'Privada'),
        ('enlace', 'Por Enlace'),
        ('publica', 'Pública'),
    ]
    
    propietario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='barajas')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    visibilidad = models.CharField(max_length=10, choices=VISIBILIDAD_CHOICES, default='privada')
    portada = models.ImageField(upload_to='portadas/', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.titulo
    
    class Meta:
        verbose_name = 'Baraja'
        verbose_name_plural = 'Barajas'


# Modelo de Tarjeta
class Tarjeta(models.Model):
    TIPO_CHOICES = [
        ('anverso_reverso', 'Anverso/Reverso'),
        ('cloze', 'Cloze (Relleno de huecos)'),
        ('imagen_oculta', 'Imagen Oculta'),
        ('audio', 'Audio'),
        ('pareo', 'Pareo'),
    ]
    
    baraja = models.ForeignKey(Baraja, on_delete=models.CASCADE, related_name='tarjetas')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='anverso_reverso')
    anverso = models.TextField()
    reverso = models.TextField()
    extra = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='tarjetas/', blank=True, null=True)
    audio = models.FileField(upload_to='audios/', blank=True, null=True)
    etiquetas = models.CharField(max_length=500, blank=True, help_text='Separadas por comas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.baraja.titulo} - {self.anverso[:50]}"
    
    class Meta:
        verbose_name = 'Tarjeta'
        verbose_name_plural = 'Tarjetas'


# Modelo de Programación (Scheduler SM-2)
class Programacion(models.Model):
    tarjeta = models.OneToOneField(Tarjeta, on_delete=models.CASCADE, related_name='programacion')
    ease_factor = models.FloatField(default=2.5)  # Factor de facilidad
    intervalo = models.IntegerField(default=1)  # Días hasta próxima revisión
    repeticiones = models.IntegerField(default=0)
    proximo_estudio = models.DateField(default=timezone.now)
    
    def __str__(self):
        return f"Programación: {self.tarjeta.anverso[:30]}"
    
    class Meta:
        verbose_name = 'Programación'
        verbose_name_plural = 'Programaciones'


# Modelo de Sesión de Estudio
class Sesion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sesiones')
    baraja = models.ForeignKey(Baraja, on_delete=models.CASCADE, related_name='sesiones')
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    duracion_minutos = models.IntegerField(default=0)
    tarjetas_estudiadas = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.usuario.username} - {self.baraja.titulo} - {self.fecha_inicio}"
    
    class Meta:
        verbose_name = 'Sesión'
        verbose_name_plural = 'Sesiones'
