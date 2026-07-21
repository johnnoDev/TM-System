from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'tienda'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='tienda:venta'), name='home'),
    path('clientes/', views.clientes, name='clientes'),
    path('clientes/<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    path('clientes/<int:pk>/eliminar/', views.cliente_eliminar, name='cliente_eliminar'),
    path('mascotas/', views.mascotas, name='mascotas'),
    path('mascotas/<int:pk>/editar/', views.mascota_editar, name='mascota_editar'),
    path('mascotas/<int:pk>/eliminar/', views.mascota_eliminar, name='mascota_eliminar'),
    path('productos/', views.productos, name='productos'),
    path('productos/<int:pk>/editar/', views.producto_editar, name='producto_editar'),
    path('productos/<int:pk>/eliminar/', views.producto_eliminar, name='producto_eliminar'),
    path('productos/categorias/nueva/', views.categoria_crear, name='categoria_crear'),
    path('productos/categorias/<int:pk>/eliminar/', views.categoria_eliminar, name='categoria_eliminar'),
    path('proveedores/', views.proveedores, name='proveedores'),
    path('proveedores/<int:pk>/editar/', views.proveedor_editar, name='proveedor_editar'),
    path('proveedores/<int:pk>/eliminar/', views.proveedor_eliminar, name='proveedor_eliminar'),
    path('venta/', views.venta, name='venta'),
    path('venta/<int:pk>/anular/', views.factura_anular, name='factura_anular'),
    path('compras/', views.compras, name='compras'),
    path('compras/<int:pk>/eliminar/', views.compra_eliminar, name='compra_eliminar'),
    path('reportes/', views.reportes, name='reportes'),
]
