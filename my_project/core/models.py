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

# Modelo de Perfil de Usuario (extiende el User de Django)
class PerfilUsuario(models.Model):
    ROL_CHOICES = [
        ('estudiante', 'Estudiante'),
        ('docente', 'Docente/Coach'),
        ('colaborador', 'Colaborador/Editor'),
        ('administrador', 'Administrador'),
    ]
    
    # Relación uno a uno con el usuario de Django
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='estudiante')
    idioma = models.CharField(max_length=10, default='es')  # Idioma preferido
    modo_oscuro = models.BooleanField(default=False)  # Preferencia de tema
    racha_dias = models.IntegerField(default=0)  # Días consecutivos estudiando
    
    def __str__(self):
        return f"{self.usuario.username} - {self.rol}"
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'


# Modelo de Clase/Grupo (para docentes)
class Clase(models.Model):
    nombre = models.CharField(max_length=200)  # Nombre de la clase
    descripcion = models.TextField(blank=True)
    docente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clases_docente')  # Profesor que crea la clase
    alumnos = models.ManyToManyField(User, related_name='clases_alumno', blank=True)  # Estudiantes inscritos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    codigo_invitacion = models.CharField(max_length=10, unique=True, blank=True)  # Código para unirse a la clase
    
    def __str__(self):
        return f"{self.nombre} - Prof. {self.docente.username}"
    
    class Meta:
        verbose_name = 'Clase'
        verbose_name_plural = 'Clases'


# Modelo de Tarea (asignaciones de barajas a clases)
class Tarea(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_progreso', 'En Progreso'),
        ('completada', 'Completada'),
        ('atrasada', 'Atrasada'),
    ]
    
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE, related_name='tareas')  # Clase a la que pertenece
    baraja = models.ForeignKey(Baraja, on_delete=models.CASCADE, related_name='tareas')  # Baraja asignada
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    fecha_limite = models.DateField()  # Fecha límite para completar
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.titulo} - {self.clase.nombre}"
    
    class Meta:
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas'


# Modelo de Historial de Respuestas (para tracking del scheduler SM-2)
class HistorialRespuesta(models.Model):
    CALIFICACION_CHOICES = [
        (1, 'Otra vez'),
        (2, 'Difícil'),
        (3, 'Bien'),
        (4, 'Fácil'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='historial')  # Usuario que estudió
    tarjeta = models.ForeignKey(Tarjeta, on_delete=models.CASCADE, related_name='historial')  # Tarjeta estudiada
    calificacion = models.IntegerField(choices=CALIFICACION_CHOICES)  # Qué tan bien recordó (1-4)
    fecha_respuesta = models.DateTimeField(auto_now_add=True)  # Cuándo respondió
    tiempo_respuesta_segundos = models.IntegerField(default=0)  # Cuánto tardó en responder
    
    def __str__(self):
        return f"{self.usuario.username} - {self.tarjeta.anverso[:30]} - {self.get_calificacion_display()}"
    
    class Meta:
        verbose_name = 'Historial de Respuesta'
        verbose_name_plural = 'Historial de Respuestas'
        ordering = ['-fecha_respuesta']  # Ordenar por más reciente primero