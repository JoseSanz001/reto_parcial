from datetime import date, timedelta
from .models import Programacion

class SchedulerSM2:
    """
    Implementación del algoritmo SM-2 (SuperMemo 2) para repetición espaciada.
    Este algoritmo calcula cuándo debe mostrarse la siguiente tarjeta según
    qué tan bien el usuario la recordó.
    """
    
    @staticmethod
    def calcular_siguiente_revision(programacion, calificacion):
        """
        Calcula la próxima fecha de revisión basada en la calificación del usuario.
        
        Parámetros:
        - programacion: objeto Programacion de la tarjeta
        - calificacion: int (1=Otra vez, 2=Difícil, 3=Bien, 4=Fácil)
        
        Retorna: objeto Programacion actualizado
        """
        
        # Si la calificación es "Otra vez" (1), reiniciar
        if calificacion == 1:
            programacion.repeticiones = 0
            programacion.intervalo = 1  # Volver a mostrar mañana
            programacion.ease_factor = max(1.3, programacion.ease_factor - 0.2)  # Reducir facilidad (min 1.3)
        
        # Si es "Difícil" (2)
        elif calificacion == 2:
            programacion.repeticiones = max(0, programacion.repeticiones - 1)  # Retroceder una repetición
            programacion.intervalo = max(1, int(programacion.intervalo * 0.5))  # Reducir intervalo a la mitad
            programacion.ease_factor = max(1.3, programacion.ease_factor - 0.15)  # Reducir facilidad un poco
        
        # Si es "Bien" (3) - respuesta correcta con esfuerzo normal
        elif calificacion == 3:
            if programacion.repeticiones == 0:
                programacion.intervalo = 1  # Primera vez: 1 día
            elif programacion.repeticiones == 1:
                programacion.intervalo = 6  # Segunda vez: 6 días
            else:
                # A partir de la tercera vez: intervalo anterior × ease_factor
                programacion.intervalo = int(programacion.intervalo * programacion.ease_factor)
            
            programacion.repeticiones += 1
            # Mantener ease_factor igual (no cambia con "Bien")
        
        # Si es "Fácil" (4) - respuesta muy fácil
        elif calificacion == 4:
            if programacion.repeticiones == 0:
                programacion.intervalo = 4  # Primera vez fácil: 4 días
            elif programacion.repeticiones == 1:
                programacion.intervalo = 10  # Segunda vez fácil: 10 días
            else:
                # Aumentar intervalo × (ease_factor + bonus)
                programacion.intervalo = int(programacion.intervalo * (programacion.ease_factor + 0.5))
            
            programacion.repeticiones += 1
            programacion.ease_factor = min(2.5, programacion.ease_factor + 0.15)  # Aumentar facilidad (max 2.5)
        
        # Calcular la próxima fecha de estudio
        programacion.proximo_estudio = date.today() + timedelta(days=programacion.intervalo)
        
        # Guardar cambios en la base de datos
        programacion.save()
        
        return programacion
    
    @staticmethod
    def obtener_tarjetas_pendientes(usuario, baraja):
        """
        Obtiene las tarjetas que deben estudiarse hoy para una baraja específica.
        
        Retorna: lista de tarjetas cuyo próximo_estudio <= hoy
        """
        from .models import Tarjeta
        
        hoy = date.today()
        
        # Obtener tarjetas de la baraja que tienen programación y están listas para hoy
        tarjetas_pendientes = Tarjeta.objects.filter(
            baraja=baraja,
            programacion__proximo_estudio__lte=hoy  # Fecha <= hoy
        ).select_related('programacion')  # Optimización: cargar programación en la misma consulta
        
        return tarjetas_pendientes