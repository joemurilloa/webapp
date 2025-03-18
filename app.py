# app.py
from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for
import os
import json
from datetime import datetime
from generador_pdf import generar_pdf
from flask_sqlalchemy import SQLAlchemy
from generador_pdf import generar_pdf, generar_pdf_factura
from datetime import datetime, timedelta
from sqlalchemy import func, extract, or_
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuración
app.config['UPLOAD_FOLDER'] = 'static/img'
app.config['COTIZACIONES_FOLDER'] = 'cotizaciones'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/remodelacionesdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True  # Mostrar consultas SQL en la consola
app.config['SECRET_KEY'] = 'clave_secreta_remodelaciones_wm'

# Asegurar que exista la carpeta de cotizaciones
if not os.path.exists(app.config['COTIZACIONES_FOLDER']):
    os.makedirs(app.config['COTIZACIONES_FOLDER'])

# Inicializar la base de datos
db = SQLAlchemy(app)

# Código de diagnóstico para conexión a la base de datos
try:
    with app.app_context():
        # Intenta ejecutar una consulta simple
        result = db.session.execute('SELECT 1').fetchone()
        print("✅ Conexión a MySQL establecida correctamente")
except Exception as e:
    print(f"❌ Error de conexión a la base de datos: {str(e)}")
    print(f"URI: {app.config['SQLALCHEMY_DATABASE_URI'].replace(':root@', ':***@')}")

# Modelos de datos
class Cliente(db.Model):
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.Text, nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)
    notas = db.Column(db.Text, nullable=True)  # Nuevo campo
    
    # Relación con cotizaciones
    cotizaciones = db.relationship('Cotizacion', backref='cliente', lazy=True)




class Cotizacion(db.Model):
    __tablename__ = 'cotizaciones'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_cotizacion = db.Column(db.String(50), unique=True, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    tipo_proyecto = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    area = db.Column(db.Float, nullable=False)
    presupuesto = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    impuesto = db.Column(db.Float, nullable=False)
    descuento = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    tiempo_entrega = db.Column(db.String(100), nullable=False)
    forma_pago = db.Column(db.String(100), nullable=False)
    validez = db.Column(db.String(50), nullable=False)
    notas = db.Column(db.Text)
    estado = db.Column(db.String(20), default='Pendiente')
    facturada = db.Column(db.Boolean, default=False)
    
    # Relación con items
    items = db.relationship('ItemCotizacion', backref='cotizacion', lazy=True, cascade="all, delete-orphan")

class ItemCotizacion(db.Model):
    __tablename__ = 'items_cotizacion'
    
    id = db.Column(db.Integer, primary_key=True)
    cotizacion_id = db.Column(db.Integer, db.ForeignKey('cotizaciones.id'), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    unidad = db.Column(db.String(20), nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

class Factura(db.Model):
    __tablename__ = 'facturas'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_factura = db.Column(db.String(50), unique=True, nullable=False)
    cotizacion_id = db.Column(db.Integer, db.ForeignKey('cotizaciones.id'), nullable=False)
    fecha_emision = db.Column(db.DateTime, default=datetime.now, nullable=False)
    fecha_vencimiento = db.Column(db.DateTime, nullable=True)
    estado_pago = db.Column(db.String(20), default='Pendiente')
    metodo_pago = db.Column(db.String(50), nullable=False)
    rtn_cliente = db.Column(db.String(20), nullable=True)  # RTN: Registro Tributario Nacional (Honduras)
    subtotal = db.Column(db.Float, nullable=False)
    impuesto = db.Column(db.Float, nullable=False)
    descuento = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    notas = db.Column(db.Text, nullable=True)
# Modelos para el módulo de Planillas
class Empleado(db.Model):
    __tablename__ = 'empleados'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    identidad = db.Column(db.String(20), unique=True, nullable=False)  # Número de identidad hondureño
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    fecha_contratacion = db.Column(db.Date, nullable=False)
    puesto = db.Column(db.String(100), nullable=False)
    departamento = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    direccion = db.Column(db.Text, nullable=False)
    sueldo_base = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default='Activo')  # Activo, Inactivo, Suspendido
    cuenta_bancaria = db.Column(db.String(50), nullable=True)
    banco = db.Column(db.String(100), nullable=True)
    notas = db.Column(db.Text, nullable=True)
    foto = db.Column(db.String(255), nullable=True)  # Ruta a la foto del empleado
    
    # Relaciones
    planillas_detalles = db.relationship('PlanillaDetalle', backref='empleado', lazy=True)
    proyectos_empleados = db.relationship('ProyectoEmpleado', backref='empleado', lazy=True)

class Planilla(db.Model):
    __tablename__ = 'planillas'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_planilla = db.Column(db.String(50), unique=True, nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    fecha_pago = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # Quincenal, Mensual, Semanal
    estado = db.Column(db.String(20), default='Borrador')  # Borrador, Aprobada, Pagada, Anulada
    total_sueldos = db.Column(db.Float, default=0.0)
    total_deducciones = db.Column(db.Float, default=0.0)
    total_bonificaciones = db.Column(db.Float, default=0.0)
    total_neto = db.Column(db.Float, default=0.0)
    usuario_creacion = db.Column(db.String(100), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)
    notas = db.Column(db.Text, nullable=True)
    
    # Relaciones
    detalles = db.relationship('PlanillaDetalle', backref='planilla', lazy=True, cascade="all, delete-orphan")

class PlanillaDetalle(db.Model):
    __tablename__ = 'planillas_detalles'
    
    id = db.Column(db.Integer, primary_key=True)
    planilla_id = db.Column(db.Integer, db.ForeignKey('planillas.id'), nullable=False)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleados.id'), nullable=False)
    dias_trabajados = db.Column(db.Float, nullable=False, default=15.0)
    horas_extra = db.Column(db.Float, default=0.0)
    sueldo_base = db.Column(db.Float, nullable=False)
    
    # Ingresos
    bonificacion = db.Column(db.Float, default=0.0)
    comisiones = db.Column(db.Float, default=0.0)
    horas_extra_monto = db.Column(db.Float, default=0.0)
    otros_ingresos = db.Column(db.Float, default=0.0)
    
    # Deducciones
    ihss = db.Column(db.Float, default=0.0)  # Instituto Hondureño de Seguridad Social
    rap = db.Column(db.Float, default=0.0)   # Régimen de Aportaciones Privadas
    isr = db.Column(db.Float, default=0.0)   # Impuesto Sobre la Renta
    anticipo = db.Column(db.Float, default=0.0)
    prestamos = db.Column(db.Float, default=0.0)
    otras_deducciones = db.Column(db.Float, default=0.0)
    
    # Totales
    total_ingresos = db.Column(db.Float, default=0.0)
    total_deducciones = db.Column(db.Float, default=0.0)
    sueldo_neto = db.Column(db.Float, default=0.0)
    
    notas = db.Column(db.Text, nullable=True)

class ProyectoEmpleado(db.Model):
    __tablename__ = 'proyectos_empleados'
    
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleados.id'), nullable=False)
    cotizacion_id = db.Column(db.Integer, db.ForeignKey('cotizaciones.id'), nullable=False)
    fecha_asignacion = db.Column(db.Date, nullable=False)
    fecha_finalizacion = db.Column(db.Date, nullable=True)
    rol = db.Column(db.String(100), nullable=False)  # Supervisor, Albañil, Ayudante, etc.
    horas_asignadas = db.Column(db.Float, default=0.0)
    costo_hora = db.Column(db.Float, default=0.0)
    costo_total = db.Column(db.Float, default=0.0)
    estado = db.Column(db.String(20), default='Asignado')  # Asignado, En progreso, Completado
    notas = db.Column(db.Text, nullable=True)
    
    # Relación con cotización (proyecto)
    cotizacion = db.relationship('Cotizacion', backref=db.backref('asignaciones_empleados', lazy=True))
    
    # Relación con la cotización
    cotizacion = db.relationship('Cotizacion', backref=db.backref('factura', uselist=False))

# Rutas
@app.route('/')
def index():
    # Redirigir a dashboard en lugar de mostrar index.html
    return redirect(url_for('dashboard'))

# Agrega una nueva ruta para crear cotizaciones
@app.route('/nueva-cotizacion')
def nueva_cotizacion():
    return render_template('index.html')
@app.route('/generar-cotizacion', methods=['POST'])
def generar_cotizacion():
    try:
        # Datos del cliente
        datos_cliente = {
            'nombre': request.form.get('nombre', ''),
            'apellido': request.form.get('apellido', ''),
            'telefono': request.form.get('telefono', ''),
            'email': request.form.get('email', ''),
            'direccion': request.form.get('direccion', ''),
            'fecha': datetime.now().strftime('%d/%m/%Y')
        }
        
        # Verificar si se especificó un ID de cliente existente
        cliente_id = request.form.get('cliente_id')
        
        if cliente_id and cliente_id.strip():
            # Si se proporciona un ID de cliente, buscar el cliente existente
            cliente = Cliente.query.get(int(cliente_id))
            if not cliente:
                return jsonify({
                    'success': False,
                    'mensaje': 'El cliente seleccionado no existe'
                }), 400
            print(f"✅ Cliente existente encontrado por ID: {cliente.id} - {cliente.nombre} {cliente.apellido}")
        else:
            # Verificar si el cliente ya existe por email y teléfono
            cliente_existente = Cliente.query.filter_by(
                email=datos_cliente['email'],
                telefono=datos_cliente['telefono']
            ).first()
            
            if cliente_existente:
                cliente = cliente_existente
                print(f"✅ Cliente existente encontrado: {cliente.id} - {cliente.nombre} {cliente.apellido}")
            else:
                # Crear nuevo cliente en la base de datos
                cliente = Cliente(
                    nombre=datos_cliente['nombre'],
                    apellido=datos_cliente['apellido'],
                    telefono=datos_cliente['telefono'],
                    email=datos_cliente['email'],
                    direccion=datos_cliente['direccion']
                )
                db.session.add(cliente)
                db.session.flush()  # Para obtener el ID generado
                print(f"✅ Nuevo cliente creado con ID temporal: {cliente.id}")
        
        
        # Datos del proyecto
        datos_proyecto = {
            'tipo': request.form.get('tipo_proyecto', ''),
            'descripcion': request.form.get('descripcion', ''),
            'area': float(request.form.get('area', 0)),
            'presupuesto': float(request.form.get('presupuesto', 0))
        }
        
        # Datos de totales
        totales = {
            'subtotal': float(request.form.get('subtotal', 0)),
            'impuesto': float(request.form.get('impuesto', 0)),
            'descuento': float(request.form.get('descuento', 0)),
            'total': float(request.form.get('total', 0))
        }
        
        # Condiciones y términos
        condiciones = {
            'tiempo_entrega': request.form.get('tiempo_entrega', ''),
            'forma_pago': request.form.get('forma_pago', ''),
            'validez': request.form.get('validez', ''),
            'notas': request.form.get('notas', '')
        }
        
        # Generar número único para la cotización
        numero_cotizacion = f"COT-{datetime.now().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}"
        
        # Crear cotización en la base de datos
        nueva_cotizacion = Cotizacion(
            numero_cotizacion=numero_cotizacion,
            cliente_id=cliente.id,
            tipo_proyecto=datos_proyecto['tipo'],
            descripcion=datos_proyecto['descripcion'],
            area=datos_proyecto['area'],
            presupuesto=datos_proyecto['presupuesto'],
            subtotal=totales['subtotal'],
            impuesto=totales['impuesto'],
            descuento=totales['descuento'],
            total=totales['total'],
            tiempo_entrega=condiciones['tiempo_entrega'],
            forma_pago=condiciones['forma_pago'],
            validez=condiciones['validez'],
            notas=condiciones['notas']
        )
        
        # Guardar primero la cotización para obtener su ID
        db.session.add(nueva_cotizacion)
        db.session.commit()  # Commit intermedio para obtener ID de cotización
        print(f"✅ Cotización guardada con ID: {nueva_cotizacion.id}")
        
        # Datos de ítems (materiales y servicios)
        items = []
        item_count = int(request.form.get('item_count', 0))
        
        for i in range(item_count):
            item_data = {
                'descripcion': request.form.get(f'item_descripcion_{i}', ''),
                'cantidad': float(request.form.get(f'item_cantidad_{i}', 0)),
                'unidad': request.form.get(f'item_unidad_{i}', ''),
                'precio_unitario': float(request.form.get(f'item_precio_{i}', 0)),
                'subtotal': float(request.form.get(f'item_subtotal_{i}', 0))
            }
            
            # Crear item en la base de datos
            nuevo_item = ItemCotizacion(
                cotizacion_id=nueva_cotizacion.id,
                descripcion=item_data['descripcion'],
                cantidad=item_data['cantidad'],
                unidad=item_data['unidad'],
                precio_unitario=item_data['precio_unitario'],
                subtotal=item_data['subtotal']
            )
            db.session.add(nuevo_item)
            
            # Agregar a la lista para generar PDF
            items.append(item_data)
        
        # Confirmar todos los cambios en la base de datos
        db.session.commit()
        print(f"✅ {item_count} items guardados para la cotización {numero_cotizacion}")
        
        # Datos de la empresa
        datos_empresa = {
            'nombre': 'Remodelaciones William Murillo',
            'direccion': 'San Pedro Sula, Honduras',
            'telefono': '+504 XXXX-XXXX',  # Reemplazar con teléfono real
            'email': 'contacto@remodelacioneswm.com',  # Reemplazar con email real
            'sitio_web': 'www.remodelacioneswm.com',  # Reemplazar con sitio web real
            'logo_path': 'static/img/logo.png'
        }
        
        # Generar PDF
        pdf_path = generar_pdf(
            numero_cotizacion, 
            datos_cliente, 
            datos_proyecto, 
            items, 
            totales, 
            condiciones, 
            datos_empresa
        )
        
        # Verificar que todo se guardó correctamente
        cotizacion_guardada = Cotizacion.query.filter_by(numero_cotizacion=numero_cotizacion).first()
        if cotizacion_guardada:
            print(f"✅ Verificación: Cotización {numero_cotizacion} guardada correctamente")
            items_guardados = ItemCotizacion.query.filter_by(cotizacion_id=cotizacion_guardada.id).count()
            print(f"✅ Verificación: {items_guardados} items guardados")
        else:
            print(f"❌ ALERTA: No se encontró la cotización {numero_cotizacion} en la verificación")
        
        # Devolver la URL del PDF generado
        return jsonify({
            'success': True,
            'mensaje': 'Cotización generada exitosamente',
            'numero_cotizacion': numero_cotizacion,
            'pdf_url': f'/descargar-cotizacion/{numero_cotizacion}'
        })
    except Exception as e:
        # En caso de error, hacer rollback de transacciones pendientes
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al generar la cotización: {str(e)}'
        }), 500
# Agregar esta ruta API para buscar clientes
@app.route('/api/buscar-clientes')
def buscar_clientes():
    try:
        # Obtener término de búsqueda
        busqueda = request.args.get('q', '')
        
        if len(busqueda) < 3:
            return jsonify({
                'success': False,
                'mensaje': 'Ingrese al menos 3 caracteres para buscar'
            })
        
        # Consultar clientes que coincidan con el término de búsqueda
        clientes = Cliente.query.filter(
            or_(
                Cliente.nombre.like(f'%{busqueda}%'),
                Cliente.apellido.like(f'%{busqueda}%'),
                Cliente.telefono.like(f'%{busqueda}%'),
                Cliente.email.like(f'%{busqueda}%')
            )
        ).limit(10).all()
        
        # Convertir a formato JSON
        clientes_data = []
        for cliente in clientes:
            clientes_data.append({
                'id': cliente.id,
                'nombre': cliente.nombre,
                'apellido': cliente.apellido,
                'telefono': cliente.telefono,
                'email': cliente.email,
                'direccion': cliente.direccion
            })
        
        return jsonify({
            'success': True,
            'clientes': clientes_data
        })
        
    except Exception as e:
        print(f"Error al buscar clientes: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al buscar clientes: {str(e)}'
        }), 500
    
@app.route('/descargar-cotizacion/<numero_cotizacion>')
def descargar_cotizacion(numero_cotizacion):
    pdf_path = f"{app.config['COTIZACIONES_FOLDER']}/{numero_cotizacion}.pdf"
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, download_name=f"{numero_cotizacion}.pdf")
    else:
        return "Cotización no encontrada", 404

@app.route('/historial')
def historial():
    # Obtener parámetros de filtrado
    cliente_filtro = request.args.get('cliente', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    
    # Consulta base para obtener cotizaciones con información de clientes
    query = db.session.query(
        Cotizacion, Cliente
    ).join(
        Cliente, Cotizacion.cliente_id == Cliente.id
    )
    
    # Aplicar filtros
    if cliente_filtro:
        query = query.filter(
            db.or_(
                Cliente.nombre.like(f'%{cliente_filtro}%'),
                Cliente.apellido.like(f'%{cliente_filtro}%')
            )
        )
    
    if fecha_desde:
        fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d')
        query = query.filter(Cotizacion.fecha_creacion >= fecha_desde_obj)
    
    if fecha_hasta:
        fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d')
        fecha_hasta_obj = fecha_hasta_obj.replace(hour=23, minute=59, second=59)
        query = query.filter(Cotizacion.fecha_creacion <= fecha_hasta_obj)
    
    # Ordenar por fecha de creación (más recientes primero)
    cotizaciones = query.order_by(Cotizacion.fecha_creacion.desc()).all()
    
    return render_template('historial.html', cotizaciones=cotizaciones)

@app.route('/ver-cotizacion/<numero_cotizacion>')
def ver_cotizacion(numero_cotizacion):
    # Buscar la cotización en la base de datos
    cotizacion = Cotizacion.query.filter_by(numero_cotizacion=numero_cotizacion).first_or_404()
    
    # Obtener información del cliente
    cliente = Cliente.query.get(cotizacion.cliente_id)
    
    # Obtener ítems de la cotización
    items = ItemCotizacion.query.filter_by(cotizacion_id=cotizacion.id).all()
    
    # Verificar si la cotización tiene una factura asociada
    factura = Factura.query.filter_by(cotizacion_id=cotizacion.id).first()
    
    return render_template('ver_cotizacion.html', cotizacion=cotizacion, cliente=cliente, items=items, factura=factura)

@app.route('/eliminar-cotizacion/<int:cotizacion_id>', methods=['POST'])
def eliminar_cotizacion(cotizacion_id):
    try:
        cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
        
        # Eliminar el archivo PDF si existe
        pdf_path = f"{app.config['COTIZACIONES_FOLDER']}/{cotizacion.numero_cotizacion}.pdf"
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        
        # Eliminar la cotización de la base de datos (los items se eliminarán automáticamente por el cascade)
        db.session.delete(cotizacion)
        db.session.commit()
        
        return jsonify({'success': True, 'mensaje': 'Cotización eliminada correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'mensaje': f'Error al eliminar la cotización: {str(e)}'}), 500

# Crear las tablas en la base de datos si no existen
with app.app_context():
    try:
        db.create_all()
        print("✅ Tablas creadas o verificadas correctamente")
    except Exception as e:
        print(f"❌ Error al crear tablas: {str(e)}")


    # Ruta para mostrar la página de facturación
@app.route('/facturacion')
def facturacion():
    # Obtener parámetros de filtrado
    cliente_filtro = request.args.get('cliente', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    
    # Consulta base para obtener cotizaciones con clientes
    query = db.session.query(Cotizacion, Cliente).join(
        Cliente, Cotizacion.cliente_id == Cliente.id
    )
    
    # Aplicar filtros
    if cliente_filtro:
        query = query.filter(
            db.or_(
                Cliente.nombre.like(f'%{cliente_filtro}%'),
                Cliente.apellido.like(f'%{cliente_filtro}%')
            )
        )
    
    if fecha_desde:
        fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d')
        query = query.filter(Cotizacion.fecha_creacion >= fecha_desde_obj)
    
    if fecha_hasta:
        fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d')
        fecha_hasta_obj = fecha_hasta_obj.replace(hour=23, minute=59, second=59)
        query = query.filter(Cotizacion.fecha_creacion <= fecha_hasta_obj)
    
    # Mostrar solo cotizaciones no facturadas y aprobadas
    query = query.filter(
        Cotizacion.facturada == False,
        Cotizacion.estado == 'Aprobada'
    )
    
    # Ordenar por fecha de creación (más recientes primero)
    cotizaciones = query.order_by(Cotizacion.fecha_creacion.desc()).all()
    
    return render_template('facturacion.html', cotizaciones=cotizaciones)
@app.route('/actualizar-estado-cotizacion/<int:cotizacion_id>', methods=['POST'])
def actualizar_estado_cotizacion(cotizacion_id):
    try:
        # Obtener los datos de la solicitud
        datos = request.json
        nuevo_estado = datos.get('estado')
        
        # Validar que el estado sea válido
        if nuevo_estado not in ['Pendiente', 'Aprobada', 'Rechazada']:
            return jsonify({
                'success': False,
                'mensaje': 'Estado no válido'
            }), 400
        
        # Buscar la cotización
        cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
        
        # Actualizar el estado
        cotizacion.estado = nuevo_estado
        
        # Guardar cambios
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': f'Estado de cotización actualizado a {nuevo_estado}'
        })
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al actualizar el estado: {str(e)}'
        }), 500
# Ruta para generar una factura desde una cotización
@app.route('/generar-factura/<int:cotizacion_id>', methods=['POST'])
def generar_factura(cotizacion_id):
    try:
        # Buscar la cotización en la base de datos
        cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
        
        # Verificar que la cotización no esté ya facturada
        if cotizacion.facturada:
            return jsonify({
                'success': False,
                'mensaje': 'Esta cotización ya ha sido facturada'
            }), 400
        
        # Verificar que la cotización esté aprobada
        if cotizacion.estado != 'Aprobada':
            return jsonify({
                'success': False,
                'mensaje': 'Solo se pueden facturar cotizaciones aprobadas'
            }), 400
        
        # Obtener información del cliente
        cliente = Cliente.query.get(cotizacion.cliente_id)
        
        # Obtener los ítems de la cotización
        items = ItemCotizacion.query.filter_by(cotizacion_id=cotizacion.id).all()
        
        # Generar número único para la factura
        numero_factura = f"FAC-{datetime.now().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}"
        
        # Obtener datos del formulario
        rtn_cliente = request.form.get('rtn_cliente', '')
        metodo_pago = request.form.get('metodo_pago', '')
        fecha_vencimiento_str = request.form.get('fecha_vencimiento', '')
        estado_pago = request.form.get('estado_pago', 'Pendiente')
        notas = request.form.get('notas', '')
        
        # Convertir fecha de vencimiento
        fecha_vencimiento = None
        if fecha_vencimiento_str:
            fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d')
        
        # Crear factura en la base de datos
        nueva_factura = Factura(
            numero_factura=numero_factura,
            cotizacion_id=cotizacion.id,
            rtn_cliente=rtn_cliente,
            metodo_pago=metodo_pago,
            fecha_vencimiento=fecha_vencimiento,
            estado_pago=estado_pago,
            notas=notas,
            subtotal=cotizacion.subtotal,
            impuesto=cotizacion.impuesto,
            descuento=cotizacion.descuento,
            total=cotizacion.total
        )
        
        # Marcar la cotización como facturada
        cotizacion.facturada = True
        
        # Guardar cambios en la base de datos
        db.session.add(nueva_factura)
        db.session.commit()
        
        # Generar PDF de la factura
        # Datos del cliente para el PDF
        datos_cliente = {
            'nombre': cliente.nombre,
            'apellido': cliente.apellido,
            'telefono': cliente.telefono,
            'email': cliente.email,
            'direccion': cliente.direccion,
            'rtn': rtn_cliente
        }
        
        # Datos del proyecto para el PDF
        datos_proyecto = {
            'tipo': cotizacion.tipo_proyecto,
            'descripcion': cotizacion.descripcion,
            'area': cotizacion.area
        }
        
        # Datos de la factura para el PDF
        datos_factura = {
            'numero_factura': numero_factura,
            'numero_cotizacion': cotizacion.numero_cotizacion,
            'fecha_emision': datetime.now().strftime('%d/%m/%Y'),
            'fecha_vencimiento': fecha_vencimiento.strftime('%d/%m/%Y') if fecha_vencimiento else '',
            'estado_pago': estado_pago,
            'metodo_pago': metodo_pago,
            'notas': notas
        }
        
        # Datos de totales para el PDF
        totales = {
            'subtotal': cotizacion.subtotal,
            'impuesto': cotizacion.impuesto,
            'descuento': cotizacion.descuento,
            'total': cotizacion.total
        }
        
        # Condiciones para el PDF
        condiciones = {
            'tiempo_entrega': cotizacion.tiempo_entrega,
            'forma_pago': cotizacion.forma_pago,
            'validez': cotizacion.validez
        }
        
        # Datos de la empresa
        datos_empresa = {
            'nombre': 'Remodelaciones William Murillo',
            'direccion': 'San Pedro Sula, Honduras',
            'telefono': '+504 XXXX-XXXX',  # Reemplazar con teléfono real
            'email': 'contacto@remodelacioneswm.com',  # Reemplazar con email real
            'sitio_web': 'www.remodelacioneswm.com',  # Reemplazar con sitio web real
            'logo_path': 'static/img/logo.png'
        }
        
        # Preparar ítems para el PDF
        items_pdf = []
        for item in items:
            items_pdf.append({
                'descripcion': item.descripcion,
                'cantidad': item.cantidad,
                'unidad': item.unidad,
                'precio_unitario': item.precio_unitario,
                'subtotal': item.subtotal
            })
        
        # Crear directorio para facturas si no existe
        if not os.path.exists('facturas'):
            os.makedirs('facturas')
        
        # Generar PDF
        pdf_path = generar_pdf_factura(
            numero_factura,
            datos_factura,
            datos_cliente,
            datos_proyecto,
            items_pdf,
            totales,
            condiciones,
            datos_empresa
        )
        
        return jsonify({
            'success': True,
            'mensaje': 'Factura generada exitosamente',
            'numero_factura': numero_factura,
            'factura_url': f'/ver-factura/{numero_factura}'
        })
    except Exception as e:
        # En caso de error, hacer rollback de transacciones pendientes
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al generar la factura: {str(e)}'
        }), 500

# Ruta para ver el historial de facturas
@app.route('/historial-facturas')
def historial_facturas():
    # Obtener parámetros de filtrado
    cliente_filtro = request.args.get('cliente', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    estado_filtro = request.args.get('estado', '')
    
    # Consulta base para obtener facturas con clientes y cotizaciones
    query = db.session.query(Factura, Cliente, Cotizacion).join(
        Cotizacion, Factura.cotizacion_id == Cotizacion.id
    ).join(
        Cliente, Cotizacion.cliente_id == Cliente.id
    )
    
    # Aplicar filtros
    if cliente_filtro:
        query = query.filter(
            db.or_(
                Cliente.nombre.like(f'%{cliente_filtro}%'),
                Cliente.apellido.like(f'%{cliente_filtro}%')
            )
        )
    
    if fecha_desde:
        fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d')
        query = query.filter(Factura.fecha_emision >= fecha_desde_obj)
    
    if fecha_hasta:
        fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d')
        fecha_hasta_obj = fecha_hasta_obj.replace(hour=23, minute=59, second=59)
        query = query.filter(Factura.fecha_emision <= fecha_hasta_obj)
    
    if estado_filtro:
        query = query.filter(Factura.estado_pago == estado_filtro)
    
    # Ordenar por fecha de emisión (más recientes primero)
    facturas = query.order_by(Factura.fecha_emision.desc()).all()
    
    return render_template('historial_facturas.html', facturas=facturas)

# Ruta para ver una factura específica
@app.route('/ver-factura/<numero_factura>')
def ver_factura(numero_factura):
    # Buscar la factura en la base de datos
    factura = Factura.query.filter_by(numero_factura=numero_factura).first_or_404()
    
    # Obtener la cotización relacionada
    cotizacion = Cotizacion.query.get(factura.cotizacion_id)
    
    # Obtener información del cliente
    cliente = Cliente.query.get(cotizacion.cliente_id)
    
    # Obtener ítems de la cotización
    items = ItemCotizacion.query.filter_by(cotizacion_id=cotizacion.id).all()
    
    return render_template('ver_factura.html', factura=factura, cotizacion=cotizacion, cliente=cliente, items=items)

# Ruta para descargar una factura
@app.route('/descargar-factura/<numero_factura>')
def descargar_factura(numero_factura):
    pdf_path = f"facturas/{numero_factura}.pdf"
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, download_name=f"{numero_factura}.pdf")
    else:
        return "Factura no encontrada", 404

# Ruta para actualizar el estado de una factura
@app.route('/actualizar-estado-factura/<int:factura_id>', methods=['POST'])
def actualizar_estado_factura(factura_id):
    try:
        # Buscar la factura en la base de datos
        factura = Factura.query.get_or_404(factura_id)
        
        # Obtener datos del formulario
        estado_pago = request.form.get('estado_pago', 'Pendiente')
        notas = request.form.get('notas', '')
        
        # Actualizar datos de la factura
        factura.estado_pago = estado_pago
        factura.notas = notas
        
        # Guardar cambios en la base de datos
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Estado de factura actualizado correctamente'
        })
    except Exception as e:
        # En caso de error, hacer rollback de transacciones pendientes
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al actualizar el estado de la factura: {str(e)}'
        }), 500

# Ruta para eliminar una factura
@app.route('/eliminar-factura/<int:factura_id>', methods=['POST'])
def eliminar_factura(factura_id):
    try:
        # Buscar la factura en la base de datos
        factura = Factura.query.get_or_404(factura_id)
        
        # Obtener la cotización relacionada
        cotizacion = Cotizacion.query.get(factura.cotizacion_id)
        
        # Marcar la cotización como no facturada
        cotizacion.facturada = False
        
        # Eliminar el archivo PDF si existe
        pdf_path = f"facturas/{factura.numero_factura}.pdf"
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        
        # Eliminar la factura de la base de datos
        db.session.delete(factura)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Factura eliminada correctamente'
        })
    except Exception as e:
        # En caso de error, hacer rollback de transacciones pendientes
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al eliminar la factura: {str(e)}'
        }), 500
    
@app.route('/clientes')
def clientes():
    # Obtener parámetros de filtrado
    nombre_filtro = request.args.get('nombre', '')
    telefono_filtro = request.args.get('telefono', '')
    fecha_registro_filtro = request.args.get('fecha_registro', '')
    
    # Consulta base
    query = Cliente.query
    
    # Aplicar filtros
    if nombre_filtro:
        query = query.filter(
            or_(
                Cliente.nombre.like(f'%{nombre_filtro}%'),
                Cliente.apellido.like(f'%{nombre_filtro}%')
            )
        )
    
    if telefono_filtro:
        query = query.filter(Cliente.telefono.like(f'%{telefono_filtro}%'))
    
    if fecha_registro_filtro:
        fecha_registro_obj = datetime.strptime(fecha_registro_filtro, '%Y-%m-%d')
        query = query.filter(Cliente.fecha_registro >= fecha_registro_obj)
    
    # Obtener clientes
    clientes = query.order_by(Cliente.nombre).all()
    
    # Estadísticas
    total_clientes = Cliente.query.count()
    
    # Clientes nuevos del mes actual
    primer_dia_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    clientes_nuevos = Cliente.query.filter(Cliente.fecha_registro >= primer_dia_mes).count()
    
    # Cotizaciones activas (pendientes o aprobadas)
    cotizaciones_activas = Cotizacion.query.filter(
        Cotizacion.estado.in_(['Pendiente', 'Aprobada']),
        Cotizacion.facturada == False
    ).count()
    
    # Facturas pendientes
    facturas_pendientes = Factura.query.filter_by(estado_pago='Pendiente').count()
    
    return render_template(
        'clientes.html',
        clientes=clientes,
        total_clientes=total_clientes,
        clientes_nuevos=clientes_nuevos,
        cotizaciones_activas=cotizaciones_activas,
        facturas_pendientes=facturas_pendientes
    )

@app.route('/crear-cliente', methods=['POST'])
def crear_cliente():
    try:
        # Obtener datos del formulario
        nombre = request.form.get('nombre', '')
        apellido = request.form.get('apellido', '')
        telefono = request.form.get('telefono', '')
        email = request.form.get('email', '')
        direccion = request.form.get('direccion', '')
        notas = request.form.get('notas', '')
        
        # Verificar si el cliente ya existe
        cliente_existente = Cliente.query.filter_by(
            email=email,
            telefono=telefono
        ).first()
        
        if cliente_existente:
            return jsonify({
                'success': False,
                'mensaje': 'Ya existe un cliente con este email y teléfono'
            })
        
        # Crear nuevo cliente
        nuevo_cliente = Cliente(
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            email=email,
            direccion=direccion,
            notas=notas
        )
        
        # Guardar en la base de datos
        db.session.add(nuevo_cliente)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Cliente creado exitosamente',
            'cliente_id': nuevo_cliente.id
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al crear el cliente: {str(e)}'
        }), 500

@app.route('/obtener-cliente/<int:cliente_id>')
def obtener_cliente(cliente_id):
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        
        # Convertir a formato JSON compatible
        cliente_data = {
            'id': cliente.id,
            'nombre': cliente.nombre,
            'apellido': cliente.apellido,
            'telefono': cliente.telefono,
            'email': cliente.email,
            'direccion': cliente.direccion,
            'notas': cliente.notas
        }
        
        return jsonify({
            'success': True,
            'cliente': cliente_data
        })
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al obtener el cliente: {str(e)}'
        }), 500

@app.route('/actualizar-cliente/<int:cliente_id>', methods=['POST'])
def actualizar_cliente(cliente_id):
    try:
        # Buscar cliente
        cliente = Cliente.query.get_or_404(cliente_id)
        
        # Actualizar datos
        cliente.nombre = request.form.get('nombre', cliente.nombre)
        cliente.apellido = request.form.get('apellido', cliente.apellido)
        cliente.telefono = request.form.get('telefono', cliente.telefono)
        cliente.email = request.form.get('email', cliente.email)
        cliente.direccion = request.form.get('direccion', cliente.direccion)
        cliente.notas = request.form.get('notas', cliente.notas)
        
        # Guardar cambios
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Cliente actualizado exitosamente'
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al actualizar el cliente: {str(e)}'
        }), 500

@app.route('/eliminar-cliente/<int:cliente_id>', methods=['POST'])
def eliminar_cliente(cliente_id):
    try:
        # Buscar cliente
        cliente = Cliente.query.get_or_404(cliente_id)
        
        # Eliminar el cliente (las cotizaciones y facturas relacionadas se eliminarán por cascade)
        db.session.delete(cliente)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Cliente eliminado exitosamente'
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al eliminar el cliente: {str(e)}'
        }), 500

@app.route('/cliente/<int:cliente_id>')
def cliente_detalles(cliente_id):
    # Obtener cliente
    cliente = Cliente.query.get_or_404(cliente_id)
    
    # Obtener estadísticas
    cotizaciones_aprobadas = sum(1 for c in cliente.cotizaciones if c.estado == 'Aprobada')
    cotizaciones_rechazadas = sum(1 for c in cliente.cotizaciones if c.estado == 'Rechazada')
    
    # Obtener facturas asociadas al cliente
    facturas = Factura.query.join(Cotizacion).filter(Cotizacion.cliente_id == cliente_id).all()
    
    # Calcular valor total y porcentajes
    valor_total = sum(c.total for c in cliente.cotizaciones)
    porcentaje_aprobado = 0
    porcentaje_pendiente = 0
    porcentaje_rechazado = 0
    
    if cliente.cotizaciones and valor_total > 0:
        valor_aprobado = sum(c.total for c in cliente.cotizaciones if c.estado == 'Aprobada')
        valor_pendiente = sum(c.total for c in cliente.cotizaciones if c.estado == 'Pendiente')
        valor_rechazado = sum(c.total for c in cliente.cotizaciones if c.estado == 'Rechazada')
        
        porcentaje_aprobado = round((valor_aprobado / valor_total) * 100)
        porcentaje_pendiente = round((valor_pendiente / valor_total) * 100)
        porcentaje_rechazado = round((valor_rechazado / valor_total) * 100)
    
    return render_template(
        'cliente_detalles.html',
        cliente=cliente,
        cotizaciones_aprobadas=cotizaciones_aprobadas,
        cotizaciones_rechazadas=cotizaciones_rechazadas,
        facturas=facturas,
        valor_total=valor_total,
        porcentaje_aprobado=porcentaje_aprobado,
        porcentaje_pendiente=porcentaje_pendiente,
        porcentaje_rechazado=porcentaje_rechazado
    )   
# Rutas para el módulo de Planillas

# Página principal de planillas
@app.route('/planillas')
def planillas():
    return render_template('planillas/index.html')

# Empleados
@app.route('/empleados')
def empleados():
    # Obtener parámetros de filtrado
    nombre_filtro = request.args.get('nombre', '')
    departamento_filtro = request.args.get('departamento', '')
    estado_filtro = request.args.get('estado', '')
    
    # Consulta base
    query = Empleado.query
    
    # Aplicar filtros
    if nombre_filtro:
        query = query.filter(
            or_(
                Empleado.nombre.like(f'%{nombre_filtro}%'),
                Empleado.apellido.like(f'%{nombre_filtro}%')
            )
        )
    
    if departamento_filtro:
        query = query.filter(Empleado.departamento == departamento_filtro)
    
    if estado_filtro:
        query = query.filter(Empleado.estado == estado_filtro)
    
    # Obtener empleados
    empleados = query.order_by(Empleado.nombre).all()
    
    # Obtener lista de departamentos para el filtro
    departamentos = db.session.query(Empleado.departamento).distinct().all()
    departamentos = [d[0] for d in departamentos]
    
    return render_template(
        'planillas/empleados.html',
        empleados=empleados,
        departamentos=departamentos
    )

@app.route('/crear-empleado', methods=['POST'])
def crear_empleado():
    try:
        # Obtener datos del formulario
        codigo = request.form.get('codigo', '')
        nombre = request.form.get('nombre', '')
        apellido = request.form.get('apellido', '')
        identidad = request.form.get('identidad', '')
        fecha_nacimiento = request.form.get('fecha_nacimiento', '')
        fecha_contratacion = request.form.get('fecha_contratacion', '')
        puesto = request.form.get('puesto', '')
        departamento = request.form.get('departamento', '')
        telefono = request.form.get('telefono', '')
        email = request.form.get('email', '')
        direccion = request.form.get('direccion', '')
        sueldo_base = float(request.form.get('sueldo_base', 0))
        cuenta_bancaria = request.form.get('cuenta_bancaria', '')
        banco = request.form.get('banco', '')
        notas = request.form.get('notas', '')
        
        # Procesar fecha de nacimiento
        fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date() if fecha_nacimiento else None
        
        # Procesar fecha de contratación
        fecha_contratacion = datetime.strptime(fecha_contratacion, '%Y-%m-%d').date() if fecha_contratacion else None
        
        # Verificar si ya existe un empleado con la misma identidad
        empleado_existente = Empleado.query.filter_by(identidad=identidad).first()
        if empleado_existente:
            return jsonify({
                'success': False,
                'mensaje': 'Ya existe un empleado con este número de identidad'
            })
        
        # Crear nuevo empleado
        nuevo_empleado = Empleado(
            codigo=codigo,
            nombre=nombre,
            apellido=apellido,
            identidad=identidad,
            fecha_nacimiento=fecha_nacimiento,
            fecha_contratacion=fecha_contratacion,
            puesto=puesto,
            departamento=departamento,
            telefono=telefono,
            email=email,
            direccion=direccion,
            sueldo_base=sueldo_base,
            cuenta_bancaria=cuenta_bancaria,
            banco=banco,
            notas=notas
        )
        
        # Subir foto si se proporciona
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto and foto.filename:
                filename = secure_filename(f"{codigo}_{foto.filename}")
                foto_path = os.path.join(app.config['UPLOAD_FOLDER'], 'empleados', filename)
                
                # Crear directorio si no existe
                os.makedirs(os.path.dirname(foto_path), exist_ok=True)
                
                # Guardar foto
                foto.save(foto_path)
                nuevo_empleado.foto = os.path.join('empleados', filename)
        
        # Guardar en la base de datos
        db.session.add(nuevo_empleado)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Empleado creado exitosamente',
            'empleado_id': nuevo_empleado.id
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al crear el empleado: {str(e)}'
        }), 500

@app.route('/obtener-empleado/<int:empleado_id>')
def obtener_empleado(empleado_id):
    try:
        empleado = Empleado.query.get_or_404(empleado_id)
        
        # Convertir a formato JSON compatible
        empleado_data = {
            'id': empleado.id,
            'codigo': empleado.codigo,
            'nombre': empleado.nombre,
            'apellido': empleado.apellido,
            'identidad': empleado.identidad,
            'fecha_nacimiento': empleado.fecha_nacimiento.strftime('%Y-%m-%d') if empleado.fecha_nacimiento else '',
            'fecha_contratacion': empleado.fecha_contratacion.strftime('%Y-%m-%d') if empleado.fecha_contratacion else '',
            'puesto': empleado.puesto,
            'departamento': empleado.departamento,
            'telefono': empleado.telefono,
            'email': empleado.email,
            'direccion': empleado.direccion,
            'sueldo_base': empleado.sueldo_base,
            'estado': empleado.estado,
            'cuenta_bancaria': empleado.cuenta_bancaria,
            'banco': empleado.banco,
            'notas': empleado.notas,
            'foto': empleado.foto
        }
        
        return jsonify({
            'success': True,
            'empleado': empleado_data
        })
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al obtener el empleado: {str(e)}'
        }), 500

@app.route('/actualizar-empleado/<int:empleado_id>', methods=['POST'])
def actualizar_empleado(empleado_id):
    try:
        # Buscar empleado
        empleado = Empleado.query.get_or_404(empleado_id)
        
        # Actualizar datos
        empleado.codigo = request.form.get('codigo', empleado.codigo)
        empleado.nombre = request.form.get('nombre', empleado.nombre)
        empleado.apellido = request.form.get('apellido', empleado.apellido)
        empleado.identidad = request.form.get('identidad', empleado.identidad)
        
        fecha_nacimiento = request.form.get('fecha_nacimiento', '')
        if fecha_nacimiento:
            empleado.fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
        
        fecha_contratacion = request.form.get('fecha_contratacion', '')
        if fecha_contratacion:
            empleado.fecha_contratacion = datetime.strptime(fecha_contratacion, '%Y-%m-%d').date()
        
        empleado.puesto = request.form.get('puesto', empleado.puesto)
        empleado.departamento = request.form.get('departamento', empleado.departamento)
        empleado.telefono = request.form.get('telefono', empleado.telefono)
        empleado.email = request.form.get('email', empleado.email)
        empleado.direccion = request.form.get('direccion', empleado.direccion)
        empleado.sueldo_base = float(request.form.get('sueldo_base', empleado.sueldo_base))
        empleado.estado = request.form.get('estado', empleado.estado)
        empleado.cuenta_bancaria = request.form.get('cuenta_bancaria', empleado.cuenta_bancaria)
        empleado.banco = request.form.get('banco', empleado.banco)
        empleado.notas = request.form.get('notas', empleado.notas)
        
        # Subir foto si se proporciona
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto and foto.filename:
                filename = secure_filename(f"{empleado.codigo}_{foto.filename}")
                foto_path = os.path.join(app.config['UPLOAD_FOLDER'], 'empleados', filename)
                
                # Crear directorio si no existe
                os.makedirs(os.path.dirname(foto_path), exist_ok=True)
                
                # Eliminar foto anterior si existe
                if empleado.foto and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], empleado.foto)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], empleado.foto))
                
                # Guardar nueva foto
                foto.save(foto_path)
                empleado.foto = os.path.join('empleados', filename)
        
        # Guardar cambios
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Empleado actualizado exitosamente'
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al actualizar el empleado: {str(e)}'
        }), 500

@app.route('/eliminar-empleado/<int:empleado_id>', methods=['POST'])
def eliminar_empleado(empleado_id):
    try:
        # Buscar empleado
        empleado = Empleado.query.get_or_404(empleado_id)
        
        # Eliminar la foto si existe
        if empleado.foto and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], empleado.foto)):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], empleado.foto))
        
        # Eliminar el empleado
        db.session.delete(empleado)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Empleado eliminado exitosamente'
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al eliminar el empleado: {str(e)}'
        }), 500

@app.route('/empleado/<int:empleado_id>')
def empleado_detalles(empleado_id):
    # Obtener empleado
    empleado = Empleado.query.get_or_404(empleado_id)
    
    # Obtener proyectos asignados
    proyectos = ProyectoEmpleado.query.filter_by(empleado_id=empleado_id).join(
        Cotizacion, ProyectoEmpleado.cotizacion_id == Cotizacion.id
    ).all()
    
    # Obtener historial de planillas
    planillas = PlanillaDetalle.query.filter_by(empleado_id=empleado_id).join(
        Planilla, PlanillaDetalle.planilla_id == Planilla.id
    ).all()
    
    return render_template(
        'planillas/empleado_detalles.html',
        empleado=empleado,
        proyectos=proyectos,
        planillas=planillas
    )

# Planillas
@app.route('/lista-planillas')
def lista_planillas():
    # Obtener parámetros de filtrado
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    tipo_filtro = request.args.get('tipo', '')
    estado_filtro = request.args.get('estado', '')
    
    # Consulta base
    query = Planilla.query
    
    # Aplicar filtros
    if fecha_desde:
        fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d')
        query = query.filter(Planilla.fecha_pago >= fecha_desde_obj)
    
    if fecha_hasta:
        fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d')
        query = query.filter(Planilla.fecha_pago <= fecha_hasta_obj)
    
    if tipo_filtro:
        query = query.filter(Planilla.tipo == tipo_filtro)
    
    if estado_filtro:
        query = query.filter(Planilla.estado == estado_filtro)
    
    # Obtener planillas ordenadas por fecha (más recientes primero)
    planillas = query.order_by(Planilla.fecha_pago.desc()).all()
    
    return render_template(
        'planillas/lista_planillas.html',
        planillas=planillas
    )

@app.route('/crear-planilla')
def crear_planilla():
    # Obtener todos los empleados activos
    empleados = Empleado.query.filter_by(estado='Activo').all()
    
    return render_template(
        'planillas/crear_planilla.html',
        empleados=empleados
    )

@app.route('/guardar-planilla', methods=['POST'])
def guardar_planilla():
    try:
        # Obtener datos básicos de la planilla
        numero_planilla = f"PLAN-{datetime.now().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}"
        fecha_inicio = request.form.get('fecha_inicio', '')
        fecha_fin = request.form.get('fecha_fin', '')
        fecha_pago = request.form.get('fecha_pago', '')
        tipo = request.form.get('tipo', '')
        notas = request.form.get('notas', '')
        
        # Convertir fechas
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date() if fecha_inicio else None
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date() if fecha_fin else None
        fecha_pago = datetime.strptime(fecha_pago, '%Y-%m-%d').date() if fecha_pago else None
        
        # Crear nueva planilla
        nueva_planilla = Planilla(
            numero_planilla=numero_planilla,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            fecha_pago=fecha_pago,
            tipo=tipo,
            estado='Borrador',
            notas=notas,
            usuario_creacion='Admin'  # Aquí podrías poner el usuario actual si tienes sistema de autenticación
        )
        
        # Guardar la planilla para obtener su ID
        db.session.add(nueva_planilla)
        db.session.commit()
        
        # Obtener los empleados seleccionados
        empleados_ids = request.form.getlist('empleados[]')
        
        # Totales acumulados
        total_sueldos = 0
        total_deducciones = 0
        total_bonificaciones = 0
        total_neto = 0
        
        # Crear un detalle para cada empleado seleccionado
        for emp_id in empleados_ids:
            empleado = Empleado.query.get(int(emp_id))
            if empleado and empleado.estado == 'Activo':
                # Calcular sueldos y deducciones
                sueldo_base = empleado.sueldo_base
                dias_trabajados = float(request.form.get(f'dias_trabajados_{emp_id}', 15))
                
                # Ajustar sueldo por días trabajados
                dias_periodo = 15 if tipo == 'Quincenal' else 30  # Ajustar según tipo de planilla
                sueldo_proporcion = sueldo_base * (dias_trabajados / dias_periodo)
                
                # Calcular deducciones
                # IHSS: 2.5% del sueldo hasta un techo (ajustar según leyes actuales)
                techo_ihss = 9849.70  # Techo mensual para 2023 en Honduras
                if tipo == 'Quincenal':
                    techo_ihss = techo_ihss / 2
                sueldo_para_ihss = min(sueldo_proporcion, techo_ihss)
                ihss = sueldo_para_ihss * 0.025
                
                # RAP: 1.5% del sueldo
                rap = sueldo_proporcion * 0.015
                
                # ISR: cálculo simplificado (ajustar según tabla progresiva vigente)
                # Este es un cálculo muy simplificado, deberías implementar la tabla completa
                sueldo_anual_proyectado = sueldo_base * 12
                isr = 0
                if sueldo_anual_proyectado > 180000:
                    isr = (sueldo_proporcion - 15000) * 0.15 / 12
                    if tipo == 'Quincenal':
                        isr = isr / 2
                
                # Crear detalle de planilla
                detalle = PlanillaDetalle(
                    planilla_id=nueva_planilla.id,
                    empleado_id=empleado.id,
                    dias_trabajados=dias_trabajados,
                    sueldo_base=sueldo_base,
                    horas_extra=float(request.form.get(f'horas_extra_{emp_id}', 0)),
                    horas_extra_monto=float(request.form.get(f'horas_extra_monto_{emp_id}', 0)),
                    bonificacion=float(request.form.get(f'bonificacion_{emp_id}', 0)),
                    comisiones=float(request.form.get(f'comisiones_{emp_id}', 0)),
                    otros_ingresos=float(request.form.get(f'otros_ingresos_{emp_id}', 0)),
                    ihss=ihss,
                    rap=rap,
                    isr=isr,
                    anticipo=float(request.form.get(f'anticipo_{emp_id}', 0)),
                    prestamos=float(request.form.get(f'prestamos_{emp_id}', 0)),
                    otras_deducciones=float(request.form.get(f'otras_deducciones_{emp_id}', 0))
                )
                
                # Calcular totales
                total_ingresos = (sueldo_proporcion + 
                                detalle.horas_extra_monto + 
                                detalle.bonificacion + 
                                detalle.comisiones + 
                                detalle.otros_ingresos)
                
                total_deducciones_detalle = (detalle.ihss + 
                                           detalle.rap + 
                                           detalle.isr + 
                                           detalle.anticipo + 
                                           detalle.prestamos + 
                                           detalle.otras_deducciones)
                
                sueldo_neto = total_ingresos - total_deducciones_detalle
                
                # Actualizar valores en el detalle
                detalle.total_ingresos = total_ingresos
                detalle.total_deducciones = total_deducciones_detalle
                detalle.sueldo_neto = sueldo_neto
                
                # Agregar el detalle a la base de datos
                db.session.add(detalle)
                
                # Acumular totales para la planilla
                total_sueldos += sueldo_proporcion
                total_deducciones += total_deducciones_detalle
                total_bonificaciones += (detalle.horas_extra_monto + 
                                        detalle.bonificacion + 
                                        detalle.comisiones + 
                                        detalle.otros_ingresos)
                total_neto += sueldo_neto
        
        # Actualizar totales en la planilla
        nueva_planilla.total_sueldos = total_sueldos
        nueva_planilla.total_deducciones = total_deducciones
        nueva_planilla.total_bonificaciones = total_bonificaciones
        nueva_planilla.total_neto = total_neto
        
        # Guardar todos los cambios
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Planilla creada exitosamente',
            'planilla_id': nueva_planilla.id,
            'numero_planilla': nueva_planilla.numero_planilla
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al crear la planilla: {str(e)}'
        }), 500

@app.route('/ver-planilla/<int:planilla_id>')
def ver_planilla(planilla_id):
    # Obtener planilla
    planilla = Planilla.query.get_or_404(planilla_id)
    
    # Obtener detalles de la planilla con información de empleados
    detalles = db.session.query(
        PlanillaDetalle, Empleado
    ).join(
        Empleado, PlanillaDetalle.empleado_id == Empleado.id
    ).filter(
        PlanillaDetalle.planilla_id == planilla_id
    ).all()
    
    return render_template(
        'planillas/ver_planilla.html',
        planilla=planilla,
        detalles=detalles
    )

@app.route('/actualizar-estado-planilla/<int:planilla_id>', methods=['POST'])
def actualizar_estado_planilla(planilla_id):
    try:
        # Obtener los datos de la solicitud
        datos = request.json
        nuevo_estado = datos.get('estado')
        
        # Validar que el estado sea válido
        if nuevo_estado not in ['Borrador', 'Aprobada', 'Pagada', 'Anulada']:
            return jsonify({
                'success': False,
                'mensaje': 'Estado no válido'
            }), 400
        
        # Buscar la planilla
        planilla = Planilla.query.get_or_404(planilla_id)
        
        # Actualizar el estado
        planilla.estado = nuevo_estado
        
        # Guardar cambios
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': f'Estado de planilla actualizado a {nuevo_estado}'
        })
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al actualizar el estado: {str(e)}'
        }), 500

@app.route('/eliminar-planilla/<int:planilla_id>', methods=['POST'])
def eliminar_planilla(planilla_id):
    try:
        # Buscar planilla
        planilla = Planilla.query.get_or_404(planilla_id)
        
        # Solo permitir eliminar planillas en estado "Borrador"
        if planilla.estado != 'Borrador':
            return jsonify({
                'success': False,
                'mensaje': 'Solo se pueden eliminar planillas en estado Borrador'
            }), 400
        
        # Eliminar la planilla (los detalles se eliminarán por cascade)
        db.session.delete(planilla)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Planilla eliminada exitosamente'
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al eliminar la planilla: {str(e)}'
        }), 500

# Asignación de empleados a proyectos
@app.route('/asignar-empleados/<int:cotizacion_id>')
def asignar_empleados(cotizacion_id):
    # Obtener cotización (proyecto)
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
    
    # Obtener cliente
    cliente = Cliente.query.get(cotizacion.cliente_id)
    
    # Obtener empleados activos
    empleados = Empleado.query.filter_by(estado='Activo').all()
    
    # Obtener asignaciones actuales
    asignaciones = ProyectoEmpleado.query.filter_by(cotizacion_id=cotizacion_id).all()
    
    return render_template(
        'planillas/asignar_empleados.html',
        cotizacion=cotizacion,
        cliente=cliente,
        empleados=empleados,
        asignaciones=asignaciones
    )

@app.route('/guardar-asignacion', methods=['POST'])
def guardar_asignacion():
    try:
        # Obtener datos del formulario
        cotizacion_id = int(request.form.get('cotizacion_id'))
        empleado_id = int(request.form.get('empleado_id'))
        rol = request.form.get('rol', '')
        horas_asignadas = float(request.form.get('horas_asignadas', 0))
        costo_hora = float(request.form.get('costo_hora', 0))
        fecha_asignacion = request.form.get('fecha_asignacion', '')
        notas = request.form.get('notas', '')
        
        # Convertir fecha
        fecha_asignacion = datetime.strptime(fecha_asignacion, '%Y-%m-%d').date() if fecha_asignacion else datetime.now().date()
        
        # Calcular costo total
        costo_total = horas_asignadas * costo_hora
        
        # Verificar si ya existe asignación para este empleado en este proyecto
        asignacion_existente = ProyectoEmpleado.query.filter_by(
            cotizacion_id=cotizacion_id,
            empleado_id=empleado_id
        ).first()
        
        if asignacion_existente:
            # Actualizar asignación existente
            asignacion_existente.rol = rol
            asignacion_existente.horas_asignadas = horas_asignadas
            asignacion_existente.costo_hora = costo_hora
            asignacion_existente.costo_total = costo_total
            asignacion_existente.fecha_asignacion = fecha_asignacion
            asignacion_existente.notas = notas
            asignacion_existente.estado = 'Asignado'  # Restablecer estado
        else:
            # Crear nueva asignación
            nueva_asignacion = ProyectoEmpleado(
                cotizacion_id=cotizacion_id,
                empleado_id=empleado_id,
                rol=rol,
                horas_asignadas=horas_asignadas,
                costo_hora=costo_hora,
                costo_total=costo_total,
                fecha_asignacion=fecha_asignacion,
                estado='Asignado',
                notas=notas
            )
            db.session.add(nueva_asignacion)
        
        # Guardar cambios
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Empleado asignado exitosamente'
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al asignar empleado: {str(e)}'
        }), 500

@app.route('/eliminar-asignacion/<int:asignacion_id>', methods=['POST'])
def eliminar_asignacion(asignacion_id):
    try:
        # Buscar asignación
        asignacion = ProyectoEmpleado.query.get_or_404(asignacion_id)
        
        # Eliminar asignación
        db.session.delete(asignacion)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Asignación eliminada exitosamente'
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al eliminar asignación: {str(e)}'
        }), 500

# Reportes
@app.route('/reportes-planillas')
def reportes_planillas():
    return render_template('planillas/reportes.html')

@app.route('/reporte-planilla-mensual', methods=['POST'])
def reporte_planilla_mensual():
    try:
        # Obtener datos del formulario
        mes = int(request.form.get('mes', datetime.now().month))
        anio = int(request.form.get('anio', datetime.now().year))
        
        # Crear fechas de inicio y fin del mes
        fecha_inicio = datetime(anio, mes, 1).date()
        if mes == 12:
            fecha_fin = datetime(anio + 1, 1, 1).date() - timedelta(days=1)
        else:
            fecha_fin = datetime(anio, mes + 1, 1).date() - timedelta(days=1)
        
        # Obtener planillas del mes
        planillas = Planilla.query.filter(
            Planilla.fecha_pago >= fecha_inicio,
            Planilla.fecha_pago <= fecha_fin
        ).all()
        
        # Datos para el reporte
        datos_reporte = {
            'mes': mes,
            'anio': anio,
            'fecha_inicio': fecha_inicio.strftime('%d/%m/%Y'),
            'fecha_fin': fecha_fin.strftime('%d/%m/%Y'),
            'planillas': [],
            'totales': {
                'sueldos': 0,
                'bonificaciones': 0,
                'deducciones': 0,
                'neto': 0
            }
        }
        
        # Procesar cada planilla
        for planilla in planillas:
            datos_planilla = {
                'id': planilla.id,
                'numero': planilla.numero_planilla,
                'tipo': planilla.tipo,
                'fecha_pago': planilla.fecha_pago.strftime('%d/%m/%Y'),
                'total_sueldos': planilla.total_sueldos,
                'total_bonificaciones': planilla.total_bonificaciones,
                'total_deducciones': planilla.total_deducciones,
                'total_neto': planilla.total_neto,
                'estado': planilla.estado
            }
            
            datos_reporte['planillas'].append(datos_planilla)
            
            # Acumular totales
            if planilla.estado in ['Aprobada', 'Pagada']:
                datos_reporte['totales']['sueldos'] += planilla.total_sueldos
                datos_reporte['totales']['bonificaciones'] += planilla.total_bonificaciones
                datos_reporte['totales']['deducciones'] += planilla.total_deducciones
                datos_reporte['totales']['neto'] += planilla.total_neto
        
        return jsonify({
            'success': True,
            'datos': datos_reporte
        })
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al generar reporte: {str(e)}'
        }), 500

@app.route('/reporte-costos-proyecto/<int:cotizacion_id>')
def reporte_costos_proyecto(cotizacion_id):
    try:
        # Obtener cotización (proyecto)
        cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
        
        # Obtener cliente
        cliente = Cliente.query.get(cotizacion.cliente_id)
        
        # Obtener asignaciones de empleados
        asignaciones = ProyectoEmpleado.query.filter_by(cotizacion_id=cotizacion_id).all()
        
        # Calcular costos totales
        costo_mano_obra = sum(a.costo_total for a in asignaciones)
        
        # Calcular costos de materiales (suponiendo que son los items de cotización)
        items = ItemCotizacion.query.filter_by(cotizacion_id=cotizacion_id).all()
        costo_materiales = sum(item.subtotal for item in items)
        
        # Calcular rentabilidad
        ingreso_total = cotizacion.total
        costo_total = costo_mano_obra + costo_materiales
        ganancia = ingreso_total - costo_total
        margen = (ganancia / ingreso_total * 100) if ingreso_total > 0 else 0
        
        # Crear datos del reporte
        datos_reporte = {
            'cotizacion': {
                'id': cotizacion.id,
                'numero': cotizacion.numero_cotizacion,
                'tipo': cotizacion.tipo_proyecto,
                'descripcion': cotizacion.descripcion,
                'fecha': cotizacion.fecha_creacion.strftime('%d/%m/%Y'),
                'estado': cotizacion.estado,
                'total': cotizacion.total
            },
            'cliente': {
                'nombre': cliente.nombre,
                'apellido': cliente.apellido,
                'telefono': cliente.telefono,
                'email': cliente.email
            },
            'asignaciones': [],
            'costos': {
                'mano_obra': costo_mano_obra,
                'materiales': costo_materiales,
                'total': costo_total
            },
            'rentabilidad': {
                'ingreso': ingreso_total,
                'ganancia': ganancia,
                'margen': margen
            }
        }
        
        # Procesar cada asignación
        for asignacion in asignaciones:
            empleado = Empleado.query.get(asignacion.empleado_id)
            datos_asignacion = {
                'id': asignacion.id,
                'empleado': f"{empleado.nombre} {empleado.apellido}",
                'rol': asignacion.rol,
                'horas': asignacion.horas_asignadas,
                'costo_hora': asignacion.costo_hora,
                'costo_total': asignacion.costo_total,
                'estado': asignacion.estado
            }
            datos_reporte['asignaciones'].append(datos_asignacion)
        
        return jsonify({
            'success': True,
            'datos': datos_reporte
        })
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al generar reporte: {str(e)}'
        }), 500

# Ruta para la página del dashboard
@app.route('/dashboard')
def dashboard():
    """
    Página principal del dashboard
    """
    return render_template('dashboard.html')

# Ruta para la API del dashboard
@app.route('/api/dashboard-data')
def dashboard_data():
    """
    API que devuelve los datos para el dashboard en formato JSON
    """
    try:
        # Obtener fecha actual y primer día del mes
        fecha_actual = datetime.now()
        primer_dia_mes = fecha_actual.replace(day=1, hour=0, minute=0, second=0)
        
        # Crear respuesta JSON simplificada
        response_data = {
            'success': True,
            'stats': {
                'clientes': {
                    'total': Cliente.query.count(),
                    'nuevos_mes': Cliente.query.filter(Cliente.fecha_registro >= primer_dia_mes).count()
                },
                'cotizaciones': {
                    'total': Cotizacion.query.count(),
                    'mes': Cotizacion.query.filter(Cotizacion.fecha_creacion >= primer_dia_mes).count(),
                    'pendientes': Cotizacion.query.filter_by(estado='Pendiente').count(),
                    'aprobadas': Cotizacion.query.filter_by(estado='Aprobada').count(),
                    'rechazadas': Cotizacion.query.filter_by(estado='Rechazada').count()
                },
                'facturas': {
                    'total': Factura.query.count(),
                    'mes': Factura.query.filter(Factura.fecha_emision >= primer_dia_mes).count(),
                    'pendientes': Factura.query.filter_by(estado_pago='Pendiente').count(),
                    'pagadas': Factura.query.filter_by(estado_pago='Pagado').count()
                },
                'ingresos': {
                    'total': float(db.session.query(func.sum(Factura.total)).filter(Factura.estado_pago == 'Pagado').scalar() or 0),
                    'mes': float(db.session.query(func.sum(Factura.total))
                                 .filter(Factura.estado_pago == 'Pagado',
                                        Factura.fecha_emision >= primer_dia_mes).scalar() or 0)
                }
            },
            'charts': {
                'tendencia': {
                    'meses': ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio'],
                    'cotizaciones': [5, 8, 12, 10, 15, 20],
                    'aprobadas': [3, 5, 8, 7, 10, 15],
                    'facturadas': [2, 4, 7, 6, 8, 12]
                },
                'estados': {
                    'Pendiente': Cotizacion.query.filter_by(estado='Pendiente').count(),
                    'Aprobada': Cotizacion.query.filter_by(estado='Aprobada').count(),
                    'Rechazada': Cotizacion.query.filter_by(estado='Rechazada').count()
                }
            },
            'tables': {
                'cotizaciones_recientes': [],
                'facturas_recientes': [],
                'top_clientes': [],
                'top_proyectos': []
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ ERROR en API Dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)