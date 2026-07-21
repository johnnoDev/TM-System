# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class TmMCliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    identificacion = models.CharField(max_length=20, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    id_ciudad = models.ForeignKey('TmPCiudad', models.DO_NOTHING, db_column='id_ciudad', blank=True, null=True)
    nombre = models.CharField(max_length=200, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    apellido = models.CharField(max_length=200, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    telefono = models.CharField(max_length=10, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    email = models.CharField(max_length=150, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    id_tipo_cliente = models.ForeignKey('TmPTipocliente', models.DO_NOTHING, db_column='id_tipo_cliente', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_M_Cliente'

    @property
    def nombre_completo(self):
        return ' '.join(parte for parte in (self.nombre, self.apellido) if parte) or None

    def __str__(self):
        return self.nombre_completo or f'Cliente #{self.id_cliente}'


class TmMHorario(models.Model):
    id_horario = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey('TmMUsuario', models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)
    fecha = models.DateField(blank=True, null=True)
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_M_Horario'

    def __str__(self):
        return f'Horario #{self.id_horario}'


class TmMMascota(models.Model):
    id_mascota = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(TmMCliente, models.DO_NOTHING, db_column='id_cliente', blank=True, null=True)
    id_raza = models.ForeignKey('TmPRaza', models.DO_NOTHING, db_column='id_raza', blank=True, null=True)
    nombre = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    sexo = models.CharField(max_length=10, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    talla = models.CharField(max_length=50, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_M_Mascota'

    def __str__(self):
        return self.nombre or f'Mascota #{self.id_mascota}'


class TmMProducto(models.Model):
    id_producto = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey('TmPCategoria', models.DO_NOTHING, db_column='id_categoria', blank=True, null=True)
    nombre_producto = models.CharField(max_length=150, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    precio_venta_actual = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    precio_costo_referencial = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock_actual = models.IntegerField(blank=True, null=True)
    stock_minimo = models.IntegerField(blank=True, null=True)
    ultima_actualizacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_M_Producto'

    def __str__(self):
        return self.nombre_producto or f'Producto #{self.id_producto}'


class TmMProveedor(models.Model):
    id_proveedor = models.AutoField(primary_key=True)
    ruc = models.CharField(max_length=13, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    razon_social = models.CharField(max_length=150, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    telefono = models.CharField(max_length=10, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    email = models.CharField(max_length=150, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    id_ciudad = models.ForeignKey('TmPCiudad', models.DO_NOTHING, db_column='id_ciudad', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_M_Proveedor'

    def __str__(self):
        return self.razon_social or f'Proveedor #{self.id_proveedor}'


class TmMServicio(models.Model):
    id_servicio = models.AutoField(primary_key=True)
    id_tarifa_servicio = models.ForeignKey('TmPTarifaservicio', models.DO_NOTHING, db_column='id_tarifa_servicio', blank=True, null=True)
    nombre_servicio = models.CharField(max_length=150, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    duracion_estimada_min = models.IntegerField(blank=True, null=True)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_M_Servicio'

    def __str__(self):
        if self.precio_base is not None:
            return f'{self.nombre_servicio} (${self.precio_base})'
        return self.nombre_servicio or f'Servicio #{self.id_servicio}'


class TmMUsuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombre_usuario = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    contrasena_hash = models.CharField(max_length=255, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    id_cargo = models.ForeignKey('TmPCargo', models.DO_NOTHING, db_column='id_cargo', blank=True, null=True)
    activo = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_M_Usuario'

    def __str__(self):
        return self.nombre_usuario or f'Usuario #{self.id_usuario}'


class TmPCargo(models.Model):
    id_cargo = models.AutoField(primary_key=True)
    nombre_cargo = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    descripcion = models.CharField(max_length=255, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_P_Cargo'

    def __str__(self):
        return self.nombre_cargo or f'Cargo #{self.id_cargo}'


class TmPCategoria(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre_categoria = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    descripcion = models.CharField(max_length=255, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_P_Categoria'

    def __str__(self):
        return self.nombre_categoria or f'Categoría #{self.id_categoria}'


class TmPCiudad(models.Model):
    id_ciudad = models.AutoField(primary_key=True)
    nombre_ciudad = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    id_provincia = models.ForeignKey('TmPProvincia', models.DO_NOTHING, db_column='id_provincia', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_P_Ciudad'

    def __str__(self):
        return self.nombre_ciudad or f'Ciudad #{self.id_ciudad}'


class TmPEspecie(models.Model):
    id_especie = models.AutoField(primary_key=True)
    nombre_especie = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_P_Especie'

    def __str__(self):
        return self.nombre_especie or f'Especie #{self.id_especie}'


class TmPProvincia(models.Model):
    id_provincia = models.AutoField(primary_key=True)
    nombre_provincia = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_P_Provincia'

    def __str__(self):
        return self.nombre_provincia or f'Provincia #{self.id_provincia}'


class TmPRaza(models.Model):
    id_raza = models.AutoField(primary_key=True)
    id_especie = models.ForeignKey(TmPEspecie, models.DO_NOTHING, db_column='id_especie', blank=True, null=True)
    nombre_raza = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_P_Raza'

    def __str__(self):
        if self.id_especie_id:
            return f'{self.nombre_raza} ({self.id_especie.nombre_especie})'
        return self.nombre_raza or f'Raza #{self.id_raza}'


class TmPTarifaservicio(models.Model):
    id_tarifa_servicio = models.AutoField(primary_key=True)
    talla = models.CharField(max_length=50, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_P_TarifaServicio'

    def __str__(self):
        return f'{self.talla} (${self.precio})' if self.talla else f'Tarifa #{self.id_tarifa_servicio}'


class TmPTipocliente(models.Model):
    id_tipo_cliente = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, db_collation='Modern_Spanish_CI_AS')

    class Meta:
        managed = False
        db_table = 'TM_P_TipoCliente'

    def __str__(self):
        return self.nombre or f'Tipo de cliente #{self.id_tipo_cliente}'


class TmPTipopago(models.Model):
    id_tipo_pago = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    codigo_sri = models.CharField(max_length=10, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    descripcion = models.CharField(max_length=255, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_P_TipoPago'

    def __str__(self):
        return self.nombre or f'Tipo de pago #{self.id_tipo_pago}'


class TmTCompra(models.Model):
    id_compra = models.AutoField(primary_key=True)
    id_proveedor = models.ForeignKey(TmMProveedor, models.DO_NOTHING, db_column='id_proveedor', blank=True, null=True)
    id_usuario = models.ForeignKey(TmMUsuario, models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)
    fecha_hora_compra = models.DateTimeField(blank=True, null=True)
    total_compra = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_T_Compra'

    def __str__(self):
        return f'Compra #{self.id_compra}'


class TmTDetallecompra(models.Model):
    id_detalle_compra = models.AutoField(primary_key=True)
    id_compra = models.ForeignKey(TmTCompra, models.DO_NOTHING, db_column='id_compra', blank=True, null=True)
    id_producto = models.ForeignKey(TmMProducto, models.DO_NOTHING, db_column='id_producto', blank=True, null=True)
    cantidad = models.IntegerField(blank=True, null=True)
    precio_costo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_T_DetalleCompra'

    def __str__(self):
        return f'Detalle compra #{self.id_detalle_compra}'


class TmTDetallereserva(models.Model):
    id_detalle_reserva = models.AutoField(primary_key=True)
    id_reserva = models.ForeignKey('TmTReserva', models.DO_NOTHING, db_column='id_reserva', blank=True, null=True)
    id_mascota = models.ForeignKey(TmMMascota, models.DO_NOTHING, db_column='id_mascota', blank=True, null=True)
    id_servicio = models.ForeignKey(TmMServicio, models.DO_NOTHING, db_column='id_servicio', blank=True, null=True)
    cantidad = models.IntegerField(blank=True, null=True)
    precio_aplicado = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    duracion_estimada_min = models.IntegerField(blank=True, null=True)
    estado = models.CharField(max_length=30, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_T_DetalleReserva'

    def __str__(self):
        return f'Detalle reserva #{self.id_detalle_reserva}'


class TmTDetalleventa(models.Model):
    id_detalle_venta = models.AutoField(primary_key=True)
    id_venta = models.ForeignKey('TmTVenta', models.DO_NOTHING, db_column='id_venta', blank=True, null=True)
    id_producto = models.ForeignKey(TmMProducto, models.DO_NOTHING, db_column='id_producto', blank=True, null=True)
    cantidad = models.IntegerField(blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_T_DetalleVenta'

    def __str__(self):
        return f'Detalle venta #{self.id_detalle_venta}'


class TmTFactura(models.Model):
    id_factura = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(TmMCliente, models.DO_NOTHING, db_column='id_cliente', blank=True, null=True)
    id_usuario = models.ForeignKey(TmMUsuario, models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)
    numero_factura = models.CharField(max_length=30, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    fecha_emision = models.DateTimeField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    iva = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    id_tipo_pago = models.ForeignKey(TmPTipopago, models.DO_NOTHING, db_column='id_tipo_pago', blank=True, null=True)
    estado = models.CharField(max_length=30, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_T_Factura'

    def __str__(self):
        return self.numero_factura or f'Factura #{self.id_factura}'


class TmTReserva(models.Model):
    id_reserva = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(TmMCliente, models.DO_NOTHING, db_column='id_cliente', blank=True, null=True)
    id_usuario = models.ForeignKey(TmMUsuario, models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)
    id_factura = models.ForeignKey(TmTFactura, models.DO_NOTHING, db_column='id_factura', blank=True, null=True)
    fecha_hora_reserva = models.DateTimeField(blank=True, null=True)
    estado = models.CharField(max_length=30, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_T_Reserva'

    def __str__(self):
        return f'Reserva #{self.id_reserva}'


class TmTVenta(models.Model):
    id_venta = models.AutoField(primary_key=True)
    id_factura = models.ForeignKey(TmTFactura, models.DO_NOTHING, db_column='id_factura', blank=True, null=True)
    fecha_hora_venta = models.DateTimeField(blank=True, null=True)
    total_venta = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TM_T_Venta'

    def __str__(self):
        return f'Venta #{self.id_venta}'
