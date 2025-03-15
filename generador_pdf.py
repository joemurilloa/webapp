# generador_pdf.py
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
import os

def generar_pdf(numero_cotizacion, datos_cliente, datos_proyecto, items, totales, condiciones, datos_empresa):
    """
    Genera un PDF de cotización con los datos proporcionados
    
    Args:
        numero_cotizacion (str): Número único de la cotización
        datos_cliente (dict): Información del cliente
        datos_proyecto (dict): Detalles del proyecto
        items (list): Lista de materiales y servicios
        totales (dict): Subtotal, impuestos, descuentos y total
        condiciones (dict): Términos y condiciones
        datos_empresa (dict): Información de la empresa
        
    Returns:
        str: Ruta al archivo PDF generado
    """
    # Crear directorio para cotizaciones si no existe
    if not os.path.exists('cotizaciones'):
        os.makedirs('cotizaciones')
    
    # Ruta del archivo PDF
    pdf_path = f"cotizaciones/{numero_cotizacion}.pdf"
    
    # Crear documento
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Contenedor para elementos del PDF
    elementos = []
    
    # Estilos
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        'TituloCotizacion',
        parent=estilos['Heading1'],
        fontSize=16,
        alignment=1,  # Centrado
        spaceAfter=12
    )
    estilo_subtitulo = ParagraphStyle(
        'Subtitulo',
        parent=estilos['Heading2'],
        fontSize=14,
        spaceAfter=6
    )
    estilo_normal = estilos['Normal']
    estilo_item = ParagraphStyle(
        'Item',
        parent=estilos['Normal'],
        fontSize=9,
        leading=12
    )
    
    # Encabezado con logo e información de la empresa
    datos_encabezado = []
    
    # Logo de la empresa (si existe)
    if os.path.exists(datos_empresa['logo_path']):
        logo = Image(datos_empresa['logo_path'], width=1.5*inch, height=1*inch)
        info_empresa = [
            [logo, Paragraph(f"<b>{datos_empresa['nombre']}</b><br/>"
                            f"{datos_empresa['direccion']}<br/>"
                            f"Tel: {datos_empresa['telefono']}<br/>"
                            f"Email: {datos_empresa['email']}<br/>"
                            f"Web: {datos_empresa['sitio_web']}", estilo_normal)]
        ]
    else:
        # Si no hay logo, solo mostrar información de la empresa
        info_empresa = [
            [Paragraph(f"<b>{datos_empresa['nombre']}</b><br/>"
                      f"{datos_empresa['direccion']}<br/>"
                      f"Tel: {datos_empresa['telefono']}<br/>"
                      f"Email: {datos_empresa['email']}<br/>"
                      f"Web: {datos_empresa['sitio_web']}", estilo_normal)]
        ]
    
    tabla_empresa = Table(info_empresa, colWidths=[2*inch, 3.5*inch])
    tabla_empresa.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elementos.append(tabla_empresa)
    elementos.append(Spacer(1, 0.5*inch))
    
    # Título de la cotización
    elementos.append(Paragraph(f"COTIZACIÓN #{numero_cotizacion}", estilo_titulo))
    elementos.append(Paragraph(f"Fecha: {datos_cliente['fecha']}", estilo_normal))
    elementos.append(Spacer(1, 0.25*inch))
    
    # Información del cliente
    elementos.append(Paragraph("INFORMACIÓN DEL CLIENTE", estilo_subtitulo))
    datos_cliente_tabla = [
        ["Nombre:", f"{datos_cliente['nombre']} {datos_cliente['apellido']}", "Teléfono:", datos_cliente['telefono']],
        ["Email:", datos_cliente['email'], "Dirección:", datos_cliente['direccion']]
    ]
    tabla_cliente = Table(datos_cliente_tabla, colWidths=[1*inch, 2*inch, 1*inch, 2*inch])
    tabla_cliente.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
    ]))
    elementos.append(tabla_cliente)
    elementos.append(Spacer(1, 0.25*inch))
    
    # Información del proyecto
    elementos.append(Paragraph("DETALLES DEL PROYECTO", estilo_subtitulo))
    datos_proyecto_tabla = [
        ["Tipo de Proyecto:", datos_proyecto['tipo']],
        ["Descripción:", datos_proyecto['descripcion']],
        ["Área (m²):", datos_proyecto['area']],
        ["Presupuesto Estimado:", datos_proyecto['presupuesto']]
    ]
    tabla_proyecto = Table(datos_proyecto_tabla, colWidths=[2*inch, 4*inch])
    tabla_proyecto.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
    ]))
    elementos.append(tabla_proyecto)
    elementos.append(Spacer(1, 0.25*inch))
    
    # Lista de materiales y servicios
    elementos.append(Paragraph("MATERIALES Y SERVICIOS", estilo_subtitulo))
    
    # Cabecera de la tabla de items
    encabezados = ["Descripción", "Cantidad", "Unidad", "Precio Unitario", "Subtotal"]
    datos_items = [encabezados]
    
    # Agregar items
    for item in items:
        datos_items.append([
            Paragraph(item['descripcion'], estilo_item),
            item['cantidad'],
            item['unidad'],
            f"L. {item['precio_unitario']}",
            f"L. {item['subtotal']}"
        ])
    
    # Crear tabla de items
    tabla_items = Table(datos_items, colWidths=[2.5*inch, 0.8*inch, 0.8*inch, 1.2*inch, 1*inch])
    tabla_items.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(tabla_items)
    elementos.append(Spacer(1, 0.1*inch))
    
    # Tabla de totales
    datos_totales = [
        ["", "", "Subtotal:", f"L. {totales['subtotal']}"],
        ["", "", "Impuesto (15%):", f"L. {totales['impuesto']}"],
        ["", "", "Descuento:", f"L. {totales['descuento']}"],
        ["", "", "TOTAL:", f"L. {totales['total']}"]
    ]
    tabla_totales = Table(datos_totales, colWidths=[2.5*inch, 0.8*inch, 1.8*inch, 1.2*inch])
    tabla_totales.setStyle(TableStyle([
        ('GRID', (2, 0), (3, -1), 0.5, colors.grey),
        ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
        ('BACKGROUND', (2, -1), (3, -1), colors.lightgrey),
        ('ALIGN', (2, 0), (3, -1), 'RIGHT'),
        ('FONTNAME', (2, -1), (3, -1), 'Helvetica-Bold'),
    ]))
    elementos.append(tabla_totales)
    elementos.append(Spacer(1, 0.25*inch))
    
    # Términos y condiciones
    elementos.append(Paragraph("TÉRMINOS Y CONDICIONES", estilo_subtitulo))
    datos_condiciones = [
        ["Tiempo de Entrega:", condiciones['tiempo_entrega']],
        ["Forma de Pago:", condiciones['forma_pago']],
        ["Validez de la Oferta:", condiciones['validez']],
        ["Notas Adicionales:", condiciones['notas']]
    ]
    tabla_condiciones = Table(datos_condiciones, colWidths=[2*inch, 4*inch])
    tabla_condiciones.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
    ]))
    elementos.append(tabla_condiciones)
    elementos.append(Spacer(1, 0.5*inch))
    
    # Pie de página
    elementos.append(Paragraph("¡Gracias por considerar nuestros servicios!", estilo_normal))
    elementos.append(Paragraph(
        "Para aprobar esta cotización, por favor firme a continuación o contáctenos.",
        estilo_normal
    ))
    elementos.append(Spacer(1, 0.5*inch))
    
    # Área de firma
    datos_firma = [
        ["_________________________", "_________________________"],
        ["Firma del Cliente", "Por Remodelaciones William Murillo"],
        ["Fecha: ___________________", ""]
    ]
    tabla_firma = Table(datos_firma, colWidths=[3*inch, 3*inch])
    tabla_firma.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(tabla_firma)
    
    # Construir PDF
    doc.build(elementos)
    
    return pdf_path

# Al final de generador_pdf.py
def generar_pdf_factura(numero_factura, datos_factura, datos_cliente, datos_proyecto, 
                  items, totales, condiciones, datos_empresa):
    """
    Genera un PDF de factura con los datos proporcionados
    
    Args:
        numero_factura (str): Número único de la factura
        datos_factura (dict): Información de la factura (fecha emisión, vencimiento, etc.)
        datos_cliente (dict): Información del cliente
        datos_proyecto (dict): Detalles del proyecto
        items (list): Lista de materiales y servicios
        totales (dict): Subtotal, impuestos, descuentos y total
        condiciones (dict): Términos y condiciones
        datos_empresa (dict): Información de la empresa
        
    Returns:
        str: Ruta al archivo PDF generado
    """
    # Crear directorio para facturas si no existe
    if not os.path.exists('facturas'):
        os.makedirs('facturas')
    
    # Ruta del archivo PDF
    pdf_path = f"facturas/{numero_factura}.pdf"
    
    # Crear documento
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Contenedor para elementos del PDF
    elementos = []
    
    # Estilos
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        'TituloFactura',
        parent=estilos['Heading1'],
        fontSize=16,
        alignment=1,  # Centrado
        spaceAfter=12
    )
    estilo_subtitulo = ParagraphStyle(
        'Subtitulo',
        parent=estilos['Heading2'],
        fontSize=14,
        spaceAfter=6
    )
    estilo_normal = estilos['Normal']
    estilo_item = ParagraphStyle(
        'Item',
        parent=estilos['Normal'],
        fontSize=9,
        leading=12
    )
    
    # Encabezado con logo e información de la empresa
    datos_encabezado = []
    
    # Logo de la empresa (si existe)
    if os.path.exists(datos_empresa['logo_path']):
        logo = Image(datos_empresa['logo_path'], width=1.5*inch, height=1*inch)
        info_empresa = [
            [logo, Paragraph(f"<b>{datos_empresa['nombre']}</b><br/>"
                            f"{datos_empresa['direccion']}<br/>"
                            f"Tel: {datos_empresa['telefono']}<br/>"
                            f"Email: {datos_empresa['email']}<br/>"
                            f"Web: {datos_empresa['sitio_web']}", estilo_normal)]
        ]
    else:
        # Si no hay logo, solo mostrar información de la empresa
        info_empresa = [
            [Paragraph(f"<b>{datos_empresa['nombre']}</b><br/>"
                      f"{datos_empresa['direccion']}<br/>"
                      f"Tel: {datos_empresa['telefono']}<br/>"
                      f"Email: {datos_empresa['email']}<br/>"
                      f"Web: {datos_empresa['sitio_web']}", estilo_normal)]
        ]
    
    tabla_empresa = Table(info_empresa, colWidths=[2*inch, 3.5*inch])
    tabla_empresa.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elementos.append(tabla_empresa)
    elementos.append(Spacer(1, 0.5*inch))
    
    # Título de la factura
    elementos.append(Paragraph(f"FACTURA #{numero_factura}", estilo_titulo))
    elementos.append(Paragraph(f"Fecha de Emisión: {datos_factura['fecha_emision']}", estilo_normal))
    if datos_factura.get('fecha_vencimiento'):
        elementos.append(Paragraph(f"Fecha de Vencimiento: {datos_factura['fecha_vencimiento']}", estilo_normal))
    elementos.append(Paragraph(f"Cotización Relacionada: {datos_factura['numero_cotizacion']}", estilo_normal))
    elementos.append(Spacer(1, 0.25*inch))
    
    # Información del cliente
    elementos.append(Paragraph("INFORMACIÓN DEL CLIENTE", estilo_subtitulo))
    
    # Agregar RTN si está disponible
    rtn_info = f"RTN: {datos_cliente['rtn']}" if datos_cliente.get('rtn') else ""
    
    datos_cliente_tabla = [
        ["Nombre:", f"{datos_cliente['nombre']} {datos_cliente['apellido']}", "Teléfono:", datos_cliente['telefono']],
        ["Email:", datos_cliente['email'], "Dirección:", datos_cliente['direccion']],
    ]
    
    # Agregar fila de RTN si está disponible
    if rtn_info:
        datos_cliente_tabla.append(["RTN:", datos_cliente['rtn'], "", ""])
    
    tabla_cliente = Table(datos_cliente_tabla, colWidths=[1*inch, 2*inch, 1*inch, 2*inch])
    tabla_cliente.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
    ]))
    elementos.append(tabla_cliente)
    elementos.append(Spacer(1, 0.25*inch))
    
    # Información del proyecto
    elementos.append(Paragraph("DETALLES DEL PROYECTO", estilo_subtitulo))
    datos_proyecto_tabla = [
        ["Tipo de Proyecto:", datos_proyecto['tipo']],
        ["Descripción:", datos_proyecto['descripcion']],
        ["Área (m²):", datos_proyecto['area']]
    ]
    tabla_proyecto = Table(datos_proyecto_tabla, colWidths=[2*inch, 4*inch])
    tabla_proyecto.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
    ]))
    elementos.append(tabla_proyecto)
    elementos.append(Spacer(1, 0.25*inch))
    
    # Lista de materiales y servicios
    elementos.append(Paragraph("MATERIALES Y SERVICIOS", estilo_subtitulo))
    
    # Cabecera de la tabla de items
    encabezados = ["Descripción", "Cantidad", "Unidad", "Precio Unitario", "Subtotal"]
    datos_items = [encabezados]
    
    # Agregar items
    for item in items:
        datos_items.append([
            Paragraph(item['descripcion'], estilo_item),
            item['cantidad'],
            item['unidad'],
            f"L. {item['precio_unitario']:.2f}",
            f"L. {item['subtotal']:.2f}"
        ])
    
    # Crear tabla de items
    tabla_items = Table(datos_items, colWidths=[2.5*inch, 0.8*inch, 0.8*inch, 1.2*inch, 1*inch])
    tabla_items.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(tabla_items)
    elementos.append(Spacer(1, 0.1*inch))
    
    # Tabla de totales
    datos_totales = [
        ["", "", "Subtotal:", f"L. {totales['subtotal']:.2f}"],
        ["", "", "Impuesto (15%):", f"L. {totales['impuesto']:.2f}"],
        ["", "", "Descuento:", f"L. {totales['descuento']:.2f}"],
        ["", "", "TOTAL:", f"L. {totales['total']:.2f}"]
    ]
    tabla_totales = Table(datos_totales, colWidths=[2.5*inch, 0.8*inch, 1.8*inch, 1.2*inch])
    tabla_totales.setStyle(TableStyle([
        ('GRID', (2, 0), (3, -1), 0.5, colors.grey),
        ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
        ('BACKGROUND', (2, -1), (3, -1), colors.lightgrey),
        ('ALIGN', (2, 0), (3, -1), 'RIGHT'),
        ('FONTNAME', (2, -1), (3, -1), 'Helvetica-Bold'),
    ]))
    elementos.append(tabla_totales)
    elementos.append(Spacer(1, 0.25*inch))
    
    # Información de pago
    elementos.append(Paragraph("INFORMACIÓN DE PAGO", estilo_subtitulo))
    datos_pago = [
        ["Método de Pago:", datos_factura['metodo_pago']],
        ["Estado:", datos_factura['estado_pago']],
    ]
    tabla_pago = Table(datos_pago, colWidths=[2*inch, 4*inch])
    tabla_pago.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
    ]))
    elementos.append(tabla_pago)
    elementos.append(Spacer(1, 0.25*inch))
    
    # Notas
    if datos_factura.get('notas'):
        elementos.append(Paragraph("NOTAS", estilo_subtitulo))
        elementos.append(Paragraph(datos_factura['notas'], estilo_normal))
        elementos.append(Spacer(1, 0.25*inch))
    
    # Pie de página
    elementos.append(Paragraph("GRACIAS POR SU PREFERENCIA", estilo_titulo))
    elementos.append(Paragraph("Esta factura es un documento legal. Por favor conserve este documento para sus registros.", estilo_normal))
    elementos.append(Spacer(1, 0.5*inch))
    
    # Construir PDF
    doc.build(elementos)
    
    return pdf_path