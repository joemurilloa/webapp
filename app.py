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
    
    # Relación con la cotización
    cotizacion = db.relationship('Cotizacion', backref=db.backref('factura', uselist=False))

# Rutas
@app.route('/')
def index():
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
        
        # Verificar si el cliente ya existe
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
if __name__ == '__main__':
    app.run(debug=True)