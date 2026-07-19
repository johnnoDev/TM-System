from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'tienda'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='tienda:clientes'), name='home'),
    path('clientes/', views.clientes, name='clientes'),
    path('clientes/<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    path('clientes/<int:pk>/eliminar/', views.cliente_eliminar, name='cliente_eliminar'),
    path('mascotas/', views.mascotas, name='mascotas'),
    path('mascotas/<int:pk>/editar/', views.mascota_editar, name='mascota_editar'),
    path('mascotas/<int:pk>/eliminar/', views.mascota_eliminar, name='mascota_eliminar'),
    path('citas/', views.citas, name='citas'),
    path('citas/<int:pk>/editar/', views.cita_editar, name='cita_editar'),
    path('citas/<int:pk>/estado/', views.cita_estado, name='cita_estado'),
    path('citas/<int:pk>/eliminar/', views.cita_eliminar, name='cita_eliminar'),
    path('reportes/', views.reportes, name='reportes'),
]
