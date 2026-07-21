import datetime

from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.db import DatabaseError, transaction
from django.db.models import Count, F, Max, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .forms import (
    CargoForm, CategoriaForm, ClienteForm, HorarioForm, LoginForm, MascotaForm, ProductoForm, ProveedorForm,
    UsuarioForm,
)
from .models import (
    TmMCliente, TmMHorario, TmMMascota, TmMProducto, TmMProveedor, TmMServicio, TmMUsuario, TmPCargo, TmPCategoria,
    TmPTipopago, TmTCompra, TmTDetallecompra, TmTDetallereserva, TmTDetalleventa, TmTFactura, TmTReserva, TmTVenta,
)

PALETTE = ['#3aa89a', '#5b8fd8', '#d98a5b', '#9b6cc9', '#c9a85b', '#e08a5b']

FACTURA_BADGE_MAP = {
    'Emitida': 'background:#d8f0e4;color:#1f8a5b',
    'Anulada': 'background:#fbe0e0;color:#cf4646',
}

PERIODOS = {'dia': 'Hoy', 'semana': 'Esta semana', 'mes': 'Este mes'}

IVA_PORCENTAJE = 15
DIAS_MAX_RESERVA = 7


def _rango_periodo(periodo, hoy):
    if periodo == 'semana':
        inicio = hoy - datetime.timedelta(days=hoy.weekday())
        fin = inicio + datetime.timedelta(days=7)
    elif periodo == 'mes':
        inicio = hoy.replace(day=1)
        fin = (inicio.replace(year=inicio.year + 1, month=1) if inicio.month == 12
               else inicio.replace(month=inicio.month + 1))
    else:
        inicio = hoy
        fin = hoy + datetime.timedelta(days=1)
    return inicio, fin


def _obtener_o_none(queryset, pk):
    if not pk:
        return None
    try:
        return queryset.filter(pk=pk).first()
    except (ValueError, TypeError):
        return None


def _precio_servicio(servicio):
    if servicio.id_tarifa_servicio_id and servicio.id_tarifa_servicio.precio is not None:
        return servicio.id_tarifa_servicio.precio
    return servicio.precio_base


def _parse_fecha_local(valor):
    if not valor:
        return None
    fecha = parse_datetime(valor)
    if fecha and timezone.is_naive(fecha):
        fecha = timezone.make_aware(fecha)
    return fecha


def _registrar_venta(usuario, cliente, tipo_pago, fecha_servicio, srv_mascotas, srv_servicios, prod_ids, prod_cantidades):
    items_servicio = []
    for mascota_id, servicio_id in zip(srv_mascotas, srv_servicios):
        mascota = _obtener_o_none(TmMMascota.objects, mascota_id)
        servicio = _obtener_o_none(TmMServicio.objects.select_related('id_tarifa_servicio'), servicio_id)
        if mascota is None or servicio is None:
            raise ValueError('Uno de los servicios del carrito ya no existe.')
        if mascota.id_cliente_id != cliente.id_cliente:
            raise ValueError(f'{mascota.nombre} no pertenece al cliente seleccionado.')
        items_servicio.append((mascota, servicio))

    items_producto = []
    for producto_id, cantidad_raw in zip(prod_ids, prod_cantidades):
        producto = _obtener_o_none(TmMProducto.objects, producto_id)
        if producto is None:
            raise ValueError('Uno de los productos del carrito ya no existe.')
        try:
            cantidad = int(cantidad_raw)
        except (TypeError, ValueError):
            cantidad = 0
        if cantidad <= 0:
            raise ValueError(f'Cantidad inválida para {producto.nombre_producto}.')
        actualizados = TmMProducto.objects.filter(pk=producto.pk, stock_actual__gte=cantidad).update(
            stock_actual=F('stock_actual') - cantidad
        )
        if not actualizados:
            raise ValueError(f'Stock insuficiente para {producto.nombre_producto}.')
        items_producto.append((producto, cantidad))

    subtotal = 0

    reserva = None
    if items_servicio:
        fecha_reserva = _parse_fecha_local(fecha_servicio)
        if fecha_reserva is None:
            fecha_reserva = timezone.now()
        else:
            ahora = timezone.now()
            limite = ahora + datetime.timedelta(days=DIAS_MAX_RESERVA)
            if fecha_reserva < ahora - datetime.timedelta(minutes=5):
                raise ValueError('La fecha del servicio no puede ser anterior a hoy.')
            if fecha_reserva > limite:
                raise ValueError(f'La fecha del servicio no puede superar los próximos {DIAS_MAX_RESERVA} días.')
        reserva = TmTReserva.objects.create(
            id_cliente=cliente, id_usuario=usuario, fecha_hora_reserva=fecha_reserva, estado='Completado'
        )
        for mascota, servicio in items_servicio:
            precio = _precio_servicio(servicio)
            subtotal += precio
            TmTDetallereserva.objects.create(
                id_reserva=reserva,
                id_mascota=mascota,
                id_servicio=servicio,
                cantidad=1,
                precio_aplicado=precio,
                duracion_estimada_min=servicio.duracion_estimada_min,
                estado='Completado',
            )

    venta_obj = None
    if items_producto:
        venta_obj = TmTVenta.objects.create(fecha_hora_venta=timezone.now(), total_venta=0)
        total_productos = 0
        for producto, cantidad in items_producto:
            precio_unitario = producto.precio_venta_actual or 0
            total_productos += precio_unitario * cantidad
            TmTDetalleventa.objects.create(
                id_venta=venta_obj,
                id_producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
            )
        venta_obj.total_venta = total_productos
        venta_obj.save(update_fields=['total_venta'])
        subtotal += total_productos

    iva = round(subtotal * IVA_PORCENTAJE / 100, 2)
    total = subtotal + iva

    factura = TmTFactura.objects.create(
        id_cliente=cliente,
        id_usuario=usuario,
        fecha_emision=timezone.now(),
        subtotal=subtotal,
        iva=iva,
        total=total,
        id_tipo_pago=tipo_pago,
        estado='Emitida',
    )
    factura.numero_factura = f'F-{factura.id_factura:06d}'
    factura.save(update_fields=['numero_factura'])

    if reserva:
        reserva.id_factura = factura
        reserva.save(update_fields=['id_factura'])
    if venta_obj:
        venta_obj.id_factura = factura
        venta_obj.save(update_fields=['id_factura'])

    return factura


def _iniciales(nombre):
    partes = (nombre or '').split()
    if not partes:
        return '?'
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[1][0]).upper()


def iniciar_sesion(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            nombre_usuario = form.cleaned_data['nombre_usuario']
            password = form.cleaned_data['password']
            usuario = TmMUsuario.objects.filter(nombre_usuario=nombre_usuario, activo=True).first()
            if usuario and usuario.contrasena_hash and check_password(password, usuario.contrasena_hash):
                request.session['usuario_id'] = usuario.id_usuario
                return redirect('tienda:dashboard')
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = LoginForm()

    return render(request, 'tienda/login.html', {'form': form})


def cerrar_sesion(request):
    if request.method == 'POST':
        request.session.flush()
    return redirect('tienda:login')


def dashboard(request):
    hoy = timezone.localdate()

    ventas_hoy = (
        TmTFactura.objects
        .filter(fecha_emision__date=hoy)
        .exclude(estado='Anulada')
        .aggregate(total=Sum('total'))['total'] or 0
    )
    facturas_hoy = (
        TmTFactura.objects
        .filter(fecha_emision__date=hoy)
        .exclude(estado='Anulada')
        .count()
    )
    reservas_hoy = TmTReserva.objects.filter(fecha_hora_reserva__date=hoy).count()
    productos_stock_bajo = TmMProducto.objects.filter(stock_actual__lte=F('stock_minimo')).count()

    return render(request, 'tienda/dashboard.html', {
        'ventas_hoy': ventas_hoy,
        'facturas_hoy': facturas_hoy,
        'reservas_hoy': reservas_hoy,
        'productos_stock_bajo': productos_stock_bajo,
        'active_view': 'dashboard',
    })


def configuracion(request):
    return render(request, 'tienda/configuracion.html', {'active_view': 'configuracion'})


def clientes(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente guardado correctamente.')
            return redirect('tienda:clientes')
    else:
        form = ClienteForm()

    qs = TmMCliente.objects.select_related('id_ciudad').order_by('nombre', 'apellido')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q))
    qs = list(qs)
    for i, c in enumerate(qs):
        c.iniciales = _iniciales(c.nombre_completo)
        c.color = PALETTE[i % len(PALETTE)]

    return render(request, 'tienda/clientes.html', {
        'form': form,
        'clientes': qs,
        'q': q,
        'active_view': 'clientes',
    })


def cliente_editar(request, pk):
    cliente = get_object_or_404(TmMCliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado correctamente.')
            return redirect('tienda:clientes')
    else:
        form = ClienteForm(instance=cliente)

    qs = TmMCliente.objects.select_related('id_ciudad').order_by('nombre', 'apellido')
    return render(request, 'tienda/clientes.html', {
        'form': form,
        'clientes': qs,
        'editing': cliente,
        'active_view': 'clientes',
    })


def cliente_eliminar(request, pk):
    cliente = get_object_or_404(TmMCliente, pk=pk)
    if request.method == 'POST':
        try:
            cliente.delete()
            messages.success(request, 'Cliente eliminado.')
        except DatabaseError:
            messages.error(request, 'No se puede eliminar: el cliente tiene mascotas o reservas asociadas.')
    return redirect('tienda:clientes')


def mascotas(request):
    if request.method == 'POST':
        form = MascotaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mascota guardada correctamente.')
            return redirect('tienda:mascotas')
    else:
        form = MascotaForm()

    qs = TmMMascota.objects.select_related('id_cliente', 'id_raza', 'id_raza__id_especie').order_by('nombre')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(nombre__icontains=q)
    qs = list(qs)

    hoy = timezone.localdate()
    for i, m in enumerate(qs):
        if m.fecha_nacimiento:
            years = hoy.year - m.fecha_nacimiento.year - (
                (hoy.month, hoy.day) < (m.fecha_nacimiento.month, m.fecha_nacimiento.day)
            )
            m.edad_display = f'{years} años'
        else:
            m.edad_display = '—'
        m.color = PALETTE[i % len(PALETTE)]

    return render(request, 'tienda/mascotas.html', {
        'form': form,
        'mascotas': qs,
        'q': q,
        'active_view': 'mascotas',
    })


def mascota_editar(request, pk):
    mascota = get_object_or_404(TmMMascota, pk=pk)
    if request.method == 'POST':
        form = MascotaForm(request.POST, instance=mascota)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mascota actualizada correctamente.')
            return redirect('tienda:mascotas')
    else:
        form = MascotaForm(instance=mascota)

    qs = TmMMascota.objects.select_related('id_cliente', 'id_raza', 'id_raza__id_especie').order_by('nombre')
    return render(request, 'tienda/mascotas.html', {
        'form': form,
        'mascotas': qs,
        'editing': mascota,
        'active_view': 'mascotas',
    })


def mascota_eliminar(request, pk):
    mascota = get_object_or_404(TmMMascota, pk=pk)
    if request.method == 'POST':
        try:
            mascota.delete()
            messages.success(request, 'Mascota eliminada.')
        except DatabaseError:
            messages.error(request, 'No se puede eliminar: la mascota tiene reservas asociadas.')
    return redirect('tienda:mascotas')


def productos(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto guardado correctamente.')
            return redirect('tienda:productos')
    else:
        form = ProductoForm()

    qs = TmMProducto.objects.select_related('id_categoria').order_by('nombre_producto')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(nombre_producto__icontains=q)
    categoria_sel = request.GET.get('categoria', '').strip()
    if categoria_sel:
        qs = qs.filter(id_categoria_id=categoria_sel)
    qs = list(qs)
    for i, p in enumerate(qs):
        p.color = PALETTE[i % len(PALETTE)]
        p.stock_bajo = (
            p.stock_actual is not None and p.stock_minimo is not None and p.stock_actual <= p.stock_minimo
        )

    return render(request, 'tienda/productos.html', {
        'form': form,
        'categoria_form': CategoriaForm(),
        'productos': qs,
        'categorias': TmPCategoria.objects.order_by('nombre_categoria'),
        'q': q,
        'categoria_sel': categoria_sel,
        'active_view': 'productos',
    })


def producto_editar(request, pk):
    producto = get_object_or_404(TmMProducto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('tienda:productos')
    else:
        form = ProductoForm(instance=producto)

    qs = TmMProducto.objects.select_related('id_categoria').order_by('nombre_producto')
    qs = list(qs)
    for i, p in enumerate(qs):
        p.color = PALETTE[i % len(PALETTE)]
        p.stock_bajo = (
            p.stock_actual is not None and p.stock_minimo is not None and p.stock_actual <= p.stock_minimo
        )

    return render(request, 'tienda/productos.html', {
        'form': form,
        'categoria_form': CategoriaForm(),
        'productos': qs,
        'categorias': TmPCategoria.objects.order_by('nombre_categoria'),
        'editing': producto,
        'active_view': 'productos',
    })


def producto_eliminar(request, pk):
    producto = get_object_or_404(TmMProducto, pk=pk)
    if request.method == 'POST':
        try:
            producto.delete()
            messages.success(request, 'Producto eliminado.')
        except DatabaseError:
            messages.error(request, 'No se puede eliminar: el producto tiene compras o ventas asociadas.')
    return redirect('tienda:productos')


def categoria_crear(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada correctamente.')
        else:
            messages.error(request, 'No se pudo crear la categoría: revisa los datos.')
    return redirect('tienda:productos')


def categoria_eliminar(request, pk):
    categoria = get_object_or_404(TmPCategoria, pk=pk)
    if request.method == 'POST':
        try:
            categoria.delete()
            messages.success(request, 'Categoría eliminada.')
        except DatabaseError:
            messages.error(request, 'No se puede eliminar: hay productos asociados a esta categoría.')
    return redirect('tienda:productos')


def proveedores(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor guardado correctamente.')
            return redirect('tienda:proveedores')
    else:
        form = ProveedorForm()

    qs = TmMProveedor.objects.select_related('id_ciudad').order_by('razon_social')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(razon_social__icontains=q)
    qs = list(qs)
    for i, p in enumerate(qs):
        p.iniciales = _iniciales(p.razon_social)
        p.color = PALETTE[i % len(PALETTE)]

    return render(request, 'tienda/proveedores.html', {
        'form': form,
        'proveedores': qs,
        'q': q,
        'active_view': 'proveedores',
    })


def proveedor_editar(request, pk):
    proveedor = get_object_or_404(TmMProveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado correctamente.')
            return redirect('tienda:proveedores')
    else:
        form = ProveedorForm(instance=proveedor)

    qs = TmMProveedor.objects.select_related('id_ciudad').order_by('razon_social')
    return render(request, 'tienda/proveedores.html', {
        'form': form,
        'proveedores': qs,
        'editing': proveedor,
        'active_view': 'proveedores',
    })


def proveedor_eliminar(request, pk):
    proveedor = get_object_or_404(TmMProveedor, pk=pk)
    if request.method == 'POST':
        try:
            proveedor.delete()
            messages.success(request, 'Proveedor eliminado.')
        except DatabaseError:
            messages.error(request, 'No se puede eliminar: el proveedor tiene compras asociadas.')
    return redirect('tienda:proveedores')


def usuarios(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Usuario guardado correctamente.')
                return redirect('tienda:usuarios')
            except DatabaseError:
                messages.error(request, 'Ya existe un usuario con ese nombre.')
    else:
        form = UsuarioForm()

    qs = TmMUsuario.objects.select_related('id_cargo').order_by('nombre_usuario')
    return render(request, 'tienda/usuarios.html', {
        'form': form,
        'cargo_form': CargoForm(),
        'usuarios': qs,
        'cargos': TmPCargo.objects.order_by('nombre_cargo'),
        'active_view': 'usuarios',
    })


def usuario_editar(request, pk):
    usuario = get_object_or_404(TmMUsuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Usuario actualizado correctamente.')
                return redirect('tienda:usuarios')
            except DatabaseError:
                messages.error(request, 'Ya existe un usuario con ese nombre.')
    else:
        form = UsuarioForm(instance=usuario)

    qs = TmMUsuario.objects.select_related('id_cargo').order_by('nombre_usuario')
    return render(request, 'tienda/usuarios.html', {
        'form': form,
        'cargo_form': CargoForm(),
        'usuarios': qs,
        'cargos': TmPCargo.objects.order_by('nombre_cargo'),
        'editing': usuario,
        'active_view': 'usuarios',
    })


def usuario_eliminar(request, pk):
    usuario = get_object_or_404(TmMUsuario, pk=pk)
    if request.method == 'POST':
        try:
            usuario.delete()
            messages.success(request, 'Usuario eliminado.')
        except DatabaseError:
            messages.error(request, 'No se puede eliminar: el usuario tiene movimientos asociados.')
    return redirect('tienda:usuarios')


def cargo_crear(request):
    if request.method == 'POST':
        form = CargoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cargo creado correctamente.')
        else:
            messages.error(request, 'No se pudo crear el cargo: revisa los datos.')
    return redirect('tienda:usuarios')


def cargo_eliminar(request, pk):
    cargo = get_object_or_404(TmPCargo, pk=pk)
    if request.method == 'POST':
        try:
            cargo.delete()
            messages.success(request, 'Cargo eliminado.')
        except DatabaseError:
            messages.error(request, 'No se puede eliminar: hay usuarios con este cargo.')
    return redirect('tienda:usuarios')


def horarios(request):
    if request.method == 'POST':
        form = HorarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Horario guardado correctamente.')
            return redirect('tienda:horarios')
    else:
        form = HorarioForm()

    qs = TmMHorario.objects.select_related('id_usuario').order_by('-fecha', 'hora_inicio')
    return render(request, 'tienda/horarios.html', {
        'form': form,
        'horarios': qs,
        'active_view': 'horarios',
    })


def horario_editar(request, pk):
    horario = get_object_or_404(TmMHorario, pk=pk)
    if request.method == 'POST':
        form = HorarioForm(request.POST, instance=horario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Horario actualizado correctamente.')
            return redirect('tienda:horarios')
    else:
        form = HorarioForm(instance=horario)

    qs = TmMHorario.objects.select_related('id_usuario').order_by('-fecha', 'hora_inicio')
    return render(request, 'tienda/horarios.html', {
        'form': form,
        'horarios': qs,
        'editing': horario,
        'active_view': 'horarios',
    })


def horario_eliminar(request, pk):
    horario = get_object_or_404(TmMHorario, pk=pk)
    if request.method == 'POST':
        try:
            horario.delete()
            messages.success(request, 'Horario eliminado.')
        except DatabaseError:
            messages.error(request, 'No se pudo eliminar el horario.')
    return redirect('tienda:horarios')


def compras(request):
    if request.method == 'POST':
        proveedor = _obtener_o_none(TmMProveedor.objects, request.POST.get('proveedor'))
        prod_ids = request.POST.getlist('prod_id')
        prod_cantidades = request.POST.getlist('prod_cantidad')
        prod_costos = request.POST.getlist('prod_costo')

        if proveedor is None:
            messages.error(request, 'Selecciona un proveedor.')
            return redirect('tienda:compras')
        if not prod_ids:
            messages.error(request, 'Agrega al menos un producto al carrito.')
            return redirect('tienda:compras')

        try:
            with transaction.atomic():
                compra = TmTCompra.objects.create(
                    id_proveedor=proveedor, id_usuario=request.usuario, fecha_hora_compra=timezone.now(),
                    total_compra=0,
                )
                total = 0
                for producto_id, cantidad_raw, costo_raw in zip(prod_ids, prod_cantidades, prod_costos):
                    producto = _obtener_o_none(TmMProducto.objects, producto_id)
                    if producto is None:
                        raise ValueError('Uno de los productos del carrito ya no existe.')
                    try:
                        cantidad = int(cantidad_raw)
                    except (TypeError, ValueError):
                        cantidad = 0
                    if cantidad <= 0:
                        raise ValueError(f'Cantidad inválida para {producto.nombre_producto}.')
                    try:
                        costo = float(costo_raw)
                    except (TypeError, ValueError):
                        costo = 0
                    if costo < 0:
                        raise ValueError(f'Costo inválido para {producto.nombre_producto}.')

                    TmTDetallecompra.objects.create(
                        id_compra=compra, id_producto=producto, cantidad=cantidad, precio_costo=costo,
                    )
                    TmMProducto.objects.filter(pk=producto.pk).update(stock_actual=F('stock_actual') + cantidad)
                    total += costo * cantidad

                compra.total_compra = total
                compra.save(update_fields=['total_compra'])
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect('tienda:compras')

        messages.success(request, f'Compra registrada. Total ${compra.total_compra}.')
        return redirect('tienda:compras')

    productos_qs = TmMProducto.objects.order_by('nombre_producto')
    historial = (TmTCompra.objects
                 .select_related('id_proveedor')
                 .prefetch_related('tmtdetallecompra_set__id_producto')
                 .order_by('-fecha_hora_compra')[:30])

    return render(request, 'tienda/compras.html', {
        'proveedores': TmMProveedor.objects.order_by('razon_social'),
        'productos': productos_qs,
        'historial': historial,
        'active_view': 'compras',
    })


def compra_eliminar(request, pk):
    compra = get_object_or_404(TmTCompra, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                for detalle in TmTDetallecompra.objects.filter(id_compra=compra):
                    TmMProducto.objects.filter(pk=detalle.id_producto_id).update(
                        stock_actual=F('stock_actual') - (detalle.cantidad or 0)
                    )
                TmTDetallecompra.objects.filter(id_compra=compra).delete()
                compra.delete()
            messages.success(request, 'Compra eliminada y stock revertido.')
        except DatabaseError:
            messages.error(request, 'No se pudo eliminar la compra.')
    return redirect('tienda:compras')


def venta(request):
    if request.method == 'POST':
        cliente = _obtener_o_none(TmMCliente.objects, request.POST.get('cliente'))
        tipo_pago = _obtener_o_none(TmPTipopago.objects, request.POST.get('id_tipo_pago'))
        fecha_servicio = request.POST.get('fecha_servicio')
        srv_mascotas = request.POST.getlist('srv_mascota')
        srv_servicios = request.POST.getlist('srv_servicio')
        prod_ids = request.POST.getlist('prod_id')
        prod_cantidades = request.POST.getlist('prod_cantidad')

        if cliente is None:
            messages.error(request, 'Selecciona un cliente.')
            return redirect('tienda:venta')
        if tipo_pago is None:
            messages.error(request, 'Selecciona una forma de pago.')
            return redirect('tienda:venta')
        if not srv_mascotas and not prod_ids:
            messages.error(request, 'Agrega al menos un servicio o producto al carrito.')
            return redirect('tienda:venta')

        try:
            with transaction.atomic():
                factura = _registrar_venta(
                    request.usuario, cliente, tipo_pago, fecha_servicio, srv_mascotas, srv_servicios,
                    prod_ids, prod_cantidades,
                )
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect('tienda:venta')

        messages.success(request, f'Venta registrada. Factura {factura.numero_factura} por ${factura.total}.')
        return redirect('tienda:venta')

    servicios = list(TmMServicio.objects.select_related('id_tarifa_servicio').order_by('nombre_servicio'))
    for s in servicios:
        s.precio_actual = _precio_servicio(s)
        s.talla_tarifa = s.id_tarifa_servicio.talla if (s.id_tarifa_servicio_id and s.id_tarifa_servicio.talla) else ''

    historial = (TmTFactura.objects
                 .select_related('id_cliente', 'id_tipo_pago')
                 .prefetch_related(
                     'tmtreserva_set__tmtdetallereserva_set__id_servicio',
                     'tmtreserva_set__tmtdetallereserva_set__id_mascota',
                     'tmtventa_set__tmtdetalleventa_set__id_producto',
                 )
                 .order_by('-fecha_emision')[:30])
    for f in historial:
        f.badge_style = FACTURA_BADGE_MAP.get(f.estado, 'background:#eef3f1;color:#5a6f6b')

    return render(request, 'tienda/venta.html', {
        'clientes': TmMCliente.objects.order_by('nombre', 'apellido'),
        'mascotas': TmMMascota.objects.select_related('id_cliente').order_by('nombre'),
        'servicios': servicios,
        'productos': TmMProducto.objects.filter(stock_actual__gt=0).order_by('nombre_producto'),
        'tipos_pago': TmPTipopago.objects.order_by('nombre'),
        'historial': historial,
        'active_view': 'venta',
    })


def factura_anular(request, pk):
    factura = get_object_or_404(TmTFactura, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                for venta_obj in TmTVenta.objects.filter(id_factura=factura):
                    for detalle in TmTDetalleventa.objects.filter(id_venta=venta_obj):
                        TmMProducto.objects.filter(pk=detalle.id_producto_id).update(
                            stock_actual=F('stock_actual') + (detalle.cantidad or 0)
                        )
                factura.estado = 'Anulada'
                factura.save(update_fields=['estado'])
            messages.success(request, 'Factura anulada y stock repuesto.')
        except DatabaseError:
            messages.error(request, 'No se pudo anular la factura.')
    return redirect('tienda:venta')


def reportes(request):
    hoy_local = timezone.localdate()
    periodo = request.GET.get('periodo', 'dia')
    if periodo not in PERIODOS:
        periodo = 'dia'
    inicio, fin = _rango_periodo(periodo, hoy_local)
    inicio_dt = timezone.make_aware(datetime.datetime.combine(inicio, datetime.time.min))
    fin_dt = timezone.make_aware(datetime.datetime.combine(fin, datetime.time.min))

    servicios_periodo = list(
        TmTDetallereserva.objects
        .filter(id_reserva__fecha_hora_reserva__gte=inicio_dt, id_reserva__fecha_hora_reserva__lt=fin_dt)
        .exclude(id_servicio__isnull=True)
        .values('id_servicio__nombre_servicio')
        .annotate(cantidad_citas=Count('id_detalle_reserva'), total=Sum(F('precio_aplicado') * F('cantidad')))
        .order_by('-cantidad_citas')
    )
    total_citas_periodo = sum(row['cantidad_citas'] for row in servicios_periodo)

    total_facturado_periodo = (
        TmTFactura.objects
        .filter(fecha_emision__gte=inicio_dt, fecha_emision__lt=fin_dt)
        .exclude(estado='Anulada')
        .aggregate(total=Sum('total'))['total'] or 0
    )

    mascotas_qs = TmMMascota.objects.select_related('id_cliente', 'id_raza').order_by('nombre')

    mascota_id = request.GET.get('mascota_id')
    mascota_sel = None
    historial = []
    if mascotas_qs.exists():
        if mascota_id:
            mascota_sel = mascotas_qs.filter(id_mascota=mascota_id).first()
        if mascota_sel is None:
            mascota_sel = mascotas_qs.first()
        historial = (TmTDetallereserva.objects
                     .filter(id_mascota=mascota_sel)
                     .select_related('id_reserva', 'id_servicio')
                     .order_by('-id_reserva__fecha_hora_reserva'))

    ingresos = list(
        TmTDetallereserva.objects
        .exclude(id_servicio__isnull=True)
        .values('id_servicio__nombre_servicio')
        .annotate(total=Sum(F('precio_aplicado') * F('cantidad')))
        .order_by('-total')
    )
    max_monto = ingresos[0]['total'] if ingresos else None
    for row in ingresos:
        row['pct'] = int((row['total'] / max_monto) * 100) if max_monto else 0
    total_general = sum((row['total'] or 0) for row in ingresos)

    productos_vendidos = list(
        TmTDetalleventa.objects
        .exclude(id_producto__isnull=True)
        .values('id_producto__nombre_producto')
        .annotate(cantidad_vendida=Sum('cantidad'), total=Sum(F('precio_unitario') * F('cantidad')))
        .order_by('-total')
    )
    max_monto_prod = productos_vendidos[0]['total'] if productos_vendidos else None
    for row in productos_vendidos:
        row['pct'] = int((row['total'] / max_monto_prod) * 100) if max_monto_prod else 0
    total_general_productos = sum((row['total'] or 0) for row in productos_vendidos)

    frecuentes = (TmMCliente.objects
                  .annotate(visitas=Count('tmtreserva', distinct=True),
                            num_mascotas=Count('tmmmascota', distinct=True))
                  .filter(visitas__gt=0)
                  .order_by('-visitas')[:5])

    limite = timezone.now() - datetime.timedelta(days=90)
    inactivas = (mascotas_qs
                 .select_related('id_cliente')
                 .annotate(ultima_visita=Max('tmtdetallereserva__id_reserva__fecha_hora_reserva'))
                 .filter(Q(ultima_visita__lt=limite) | Q(ultima_visita__isnull=True)))

    return render(request, 'tienda/reportes.html', {
        'active_view': 'reportes',
        'periodo': periodo,
        'periodos': PERIODOS,
        'servicios_periodo': servicios_periodo,
        'total_citas_periodo': total_citas_periodo,
        'total_facturado_periodo': total_facturado_periodo,
        'mascotas': mascotas_qs,
        'mascota_sel': mascota_sel,
        'historial': historial,
        'ingresos': ingresos,
        'total_general': total_general,
        'productos_vendidos': productos_vendidos,
        'total_general_productos': total_general_productos,
        'frecuentes': frecuentes,
        'inactivas': inactivas,
        'hoy': timezone.localdate(),
    })
