from django.shortcuts import redirect

from .models import TmMUsuario

RUTAS_EXENTAS = ('/login/', '/admin/', '/static/')


class LoginRequeridoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.usuario = None
        usuario_id = request.session.get('usuario_id')

        if usuario_id:
            request.usuario = TmMUsuario.objects.filter(pk=usuario_id, activo=True).select_related('id_cargo').first()
            if request.usuario is None:
                del request.session['usuario_id']

        if request.usuario is None and not request.path.startswith(RUTAS_EXENTAS):
            return redirect('tienda:login')

        return self.get_response(request)
