import datetime

from django.contrib import messages
from django.db import DatabaseError
from django.db.models import Count, F, Max, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CitaForm, ClienteForm, MascotaForm
from .models import TmMCliente, TmMMascota, TmPTipopago, TmTDetallereserva, TmTFactura, TmTReserva

PALETTE = ['#3aa89a', '#5b8fd8', '#d98a5b', '#9b6cc9', '#c9a85b', '#e08a5b']

BADGE_MAP = {
    'Pendiente': 'background:#fbeed3;color:#bd8623',
    'Completado': 'background:#d8f0e4;color:#1f8a5b',
    'Cancelado': 'background:#fbe0e0;color:#cf4646',
}

PERIODOS = {'dia': 'Hoy', 'semana': 'Esta semana', 'mes': 'Este mes'}

IVA_PORCENTAJE = 15


def _con_badges(detalles):
    for d in detalles:
        d.badge_style = BADGE_MAP.get(d.estado, 'background:#eef3f1;color:#5a6f6b')
    return detalles


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


def _precio_servicio(servicio):
    if servicio.id_tarifa_servicio_id and servicio.id_tarifa_servicio.precio is not None:
        return servicio.id_tarifa_servicio.precio
    return servicio.precio_base


def _facturar_reserva(reserva, tipo_pago):
    detalles = TmTDetallereserva.objects.filter(id_reserva=reserva).exclude(estado='Cancelado')
    subtotal = sum((d.precio_aplicado or 0) * (d.cantidad or 1) for d in detalles)
    iva = round(subtotal * IVA_PORCENTAJE / 100, 2)
    total = subtotal + iva

    factura = TmTFactura.objects.create(
        id_cliente=reserva.id_cliente,
        fecha_emision=timezone.now(),
        subtotal=subtotal,
        iva=iva,
        total=total,
        id_tipo_pago=tipo_pago,
        estado='Emitida',
    )
    factura.numero_factura = f'F-{factura.id_factura:06d}'
    factura.save(update_fields=['numero_factura'])
    reserva.id_factura = factura


def _iniciales(nombre):
    partes = (nombre or '').split()
    if not partes:
        return '?'
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[1][0]).upper()


def clientes(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente guardado correctamente.')
            return redirect('tienda:clientes')
    else:
        form = ClienteForm()

    qs = TmMCliente.objects.select_related('id_ciudad').order_by('nombre_razon_social')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(nombre_razon_social__icontains=q)
    qs = list(qs)
    for i, c in enumerate(qs):
        c.iniciales = _iniciales(c.nombre_razon_social)
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

    qs = TmMCliente.objects.select_related('id_ciudad').order_by('nombre_razon_social')
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


def citas(request):
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            mascota = form.cleaned_data['id_mascota']
            servicio = form.cleaned_data['id_servicio']
            fecha = form.cleaned_data['fecha_hora_reserva']

            reserva = TmTReserva.objects.create(
                id_cliente=mascota.id_cliente,
                fecha_hora_reserva=fecha,
                estado='Pendiente',
            )

            TmTDetallereserva.objects.create(
                id_reserva=reserva,
                id_mascota=mascota,
                id_servicio=servicio,
                cantidad=1,
                precio_aplicado=_precio_servicio(servicio),
                duracion_estimada_min=servicio.duracion_estimada_min,
                estado='Pendiente',
            )
            messages.success(request, 'Cita agendada correctamente.')
            return redirect('tienda:citas')
    else:
        form = CitaForm()

    detalles = _con_badges(TmTDetallereserva.objects
                            .select_related('id_reserva', 'id_mascota', 'id_servicio')
                            .order_by('-id_reserva__fecha_hora_reserva'))

    return render(request, 'tienda/citas.html', {
        'form': form,
        'detalles': detalles,
        'tipos_pago': TmPTipopago.objects.order_by('nombre'),
        'active_view': 'citas',
    })


def cita_editar(request, pk):
    detalle = get_object_or_404(
        TmTDetallereserva.objects.select_related('id_reserva', 'id_mascota', 'id_servicio'), pk=pk
    )
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            mascota = form.cleaned_data['id_mascota']
            servicio = form.cleaned_data['id_servicio']
            fecha = form.cleaned_data['fecha_hora_reserva']

            detalle.id_mascota = mascota
            detalle.id_servicio = servicio
            detalle.precio_aplicado = _precio_servicio(servicio)
            detalle.duracion_estimada_min = servicio.duracion_estimada_min
            detalle.save()

            if detalle.id_reserva:
                detalle.id_reserva.fecha_hora_reserva = fecha
                detalle.id_reserva.id_cliente = mascota.id_cliente
                detalle.id_reserva.save()

            messages.success(request, 'Cita actualizada correctamente.')
            return redirect('tienda:citas')
    else:
        form = CitaForm(initial={
            'id_mascota': detalle.id_mascota_id,
            'id_servicio': detalle.id_servicio_id,
            'fecha_hora_reserva': detalle.id_reserva.fecha_hora_reserva if detalle.id_reserva else None,
        })

    detalles = _con_badges(TmTDetallereserva.objects
                            .select_related('id_reserva', 'id_mascota', 'id_servicio')
                            .order_by('-id_reserva__fecha_hora_reserva'))

    return render(request, 'tienda/citas.html', {
        'form': form,
        'detalles': detalles,
        'editing': detalle,
        'tipos_pago': TmPTipopago.objects.order_by('nombre'),
        'active_view': 'citas',
    })


def cita_estado(request, pk):
    detalle = get_object_or_404(TmTDetallereserva.objects.select_related('id_reserva'), pk=pk)
    estado = request.POST.get('estado')
    if request.method == 'POST' and estado in BADGE_MAP:
        reserva = detalle.id_reserva

        if estado == 'Completado' and reserva and reserva.id_factura_id is None:
            tipo_pago = TmPTipopago.objects.filter(pk=request.POST.get('id_tipo_pago')).first()
            if tipo_pago is None:
                messages.error(request, 'Selecciona una forma de pago para completar y facturar la cita.')
                return redirect('tienda:citas')
            _facturar_reserva(reserva, tipo_pago)

        detalle.estado = estado
        detalle.save()
        if reserva:
            reserva.estado = estado
            reserva.save()

        if estado == 'Completado':
            messages.success(request, f'Cita completada. Factura {reserva.id_factura.numero_factura} generada.')
        else:
            messages.success(request, f'Cita marcada como {estado}.')
    return redirect('tienda:citas')


def cita_eliminar(request, pk):
    detalle = get_object_or_404(TmTDetallereserva.objects.select_related('id_reserva'), pk=pk)
    if request.method == 'POST':
        reserva = detalle.id_reserva
        try:
            detalle.delete()
            if reserva and not TmTDetallereserva.objects.filter(id_reserva=reserva).exists():
                reserva.delete()
            messages.success(request, 'Cita eliminada.')
        except DatabaseError:
            messages.error(request, 'No se puede eliminar esta cita.')
    return redirect('tienda:citas')


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
        'mascotas': mascotas_qs,
        'mascota_sel': mascota_sel,
        'historial': historial,
        'ingresos': ingresos,
        'total_general': total_general,
        'frecuentes': frecuentes,
        'inactivas': inactivas,
        'hoy': timezone.localdate(),
    })
