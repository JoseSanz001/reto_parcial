from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def rol_requerido(*roles_permitidos):
    """
    Decorador que verifica si el usuario tiene uno de los roles permitidos.
    
    Uso:
    @rol_requerido('docente', 'administrador')
    def mi_vista(request):
        ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Verificar que el usuario esté autenticado
            if not request.user.is_authenticated:
                return redirect('admin:login')
            
            # Verificar que tenga perfil
            if not hasattr(request.user, 'perfil'):
                messages.error(request, 'No tienes un perfil asignado. Contacta al administrador.')
                return redirect('core:dashboard')
            
            # Verificar el rol
            rol_usuario = request.user.perfil.rol
            
            if rol_usuario not in roles_permitidos:
                messages.error(
                    request, 
                    f'No tienes permisos para acceder a esta página. Se requiere rol: {", ".join(roles_permitidos)}'
                )
                return redirect('core:dashboard')
            
            # Si todo está bien, ejecutar la vista
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def solo_docente(view_func):
    """
    Decorador simplificado para vistas que solo pueden acceder docentes.
    """
    return rol_requerido('docente', 'administrador')(view_func)


def solo_estudiante(view_func):
    """
    Decorador para vistas exclusivas de estudiantes.
    """
    return rol_requerido('estudiante')(view_func)


def docente_o_colaborador(view_func):
    """
    Decorador para vistas que pueden acceder docentes y colaboradores.
    """
    return rol_requerido('docente', 'colaborador', 'administrador')(view_func)