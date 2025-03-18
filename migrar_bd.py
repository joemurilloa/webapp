# migrar_bd.py - Script para migrar la base de datos
from app import app, db
from sqlalchemy import text

def migrar_base_datos():
    """
    Realiza la migración de la base de datos para agregar el nuevo modelo
    de facturas y los campos adicionales.
    """
    print("Iniciando migración de la base de datos...")
    
    with app.app_context():
        try:
            # 1. Verificar si la columna 'facturada' ya existe en la tabla 'cotizaciones'
            query_verificar = text("""
                SELECT COUNT(*) AS columna_existe
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = 'remodelacionesdb'
                AND TABLE_NAME = 'cotizaciones' 
                AND COLUMN_NAME = 'facturada'
            """)
            
            resultado = db.session.execute(query_verificar).fetchone()
            
            # Si la columna no existe, agregarla
            if resultado and resultado[0] == 0:
                print("Agregando columna 'facturada' a la tabla 'cotizaciones'...")
                query_agregar_columna = text("""
                    ALTER TABLE cotizaciones 
                    ADD COLUMN facturada BOOLEAN DEFAULT FALSE
                """)
                db.session.execute(query_agregar_columna)
            else:
                print("La columna 'facturada' ya existe en la tabla 'cotizaciones'.")
            
            # 2. Verificar si la tabla 'facturas' ya existe
            query_tabla_existe = text("""
                SELECT COUNT(*) AS tabla_existe
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = 'remodelacionesdb'
                AND TABLE_NAME = 'facturas'
            """)
            
            resultado = db.session.execute(query_tabla_existe).fetchone()
            
            # Si la tabla no existe, crearla
            if resultado and resultado[0] == 0:
                print("Creando tabla 'facturas'...")
                query_crear_tabla = text("""
                    CREATE TABLE facturas (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        numero_factura VARCHAR(50) NOT NULL UNIQUE,
                        cotizacion_id INT NOT NULL,
                        fecha_emision DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        fecha_vencimiento DATETIME,
                        estado_pago VARCHAR(20) NOT NULL DEFAULT 'Pendiente',
                        metodo_pago VARCHAR(50) NOT NULL,
                        rtn_cliente VARCHAR(20),
                        subtotal FLOAT NOT NULL,
                        impuesto FLOAT NOT NULL,
                        descuento FLOAT NOT NULL,
                        total FLOAT NOT NULL,
                        notas TEXT,
                        FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones(id) ON DELETE CASCADE
                    );
                """)
                db.session.execute(query_crear_tabla)
            else:
                print("La tabla 'facturas' ya existe.")
            
            # 3. Verificar si la columna 'notas' ya existe en la tabla 'clientes'
            query_verificar_notas = text("""
                SELECT COUNT(*) AS columna_existe
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = 'remodelacionesdb'
                AND TABLE_NAME = 'clientes' 
                AND COLUMN_NAME = 'notas'
            """)
            
            resultado_notas = db.session.execute(query_verificar_notas).fetchone()
            
            # Si la columna no existe, agregarla
            if resultado_notas and resultado_notas[0] == 0:
                print("Agregando columna 'notas' a la tabla 'clientes'...")
                query_agregar_notas = text("""
                    ALTER TABLE clientes 
                    ADD COLUMN notas TEXT
                """)
                db.session.execute(query_agregar_notas)
            else:
                print("La columna 'notas' ya existe en la tabla 'clientes'.")
            
            # 4. Verificar si las tablas del módulo de planillas ya existen
            print("Verificando tablas del módulo de planillas...")
            from datetime import datetime, timedelta
            
            # Importar los modelos del módulo de planillas
            from app import Empleado, Planilla, PlanillaDetalle, ProyectoEmpleado
            
            # Verificar cada tabla del módulo de planillas
            tablas_planillas = ['empleados', 'planillas', 'planillas_detalles', 'proyectos_empleados']
            tablas_faltantes = []
            
            for tabla in tablas_planillas:
                query_tabla_existe = text(f"""
                    SELECT COUNT(*) AS tabla_existe
                    FROM information_schema.TABLES 
                    WHERE TABLE_SCHEMA = 'remodelacionesdb'
                    AND TABLE_NAME = '{tabla}'
                """)
                
                resultado = db.session.execute(query_tabla_existe).fetchone()
                
                # Si la tabla no existe, la agregamos a la lista de tablas faltantes
                if resultado and resultado[0] == 0:
                    print(f"La tabla '{tabla}' no existe, se creará durante la migración.")
                    tablas_faltantes.append(tabla)
                else:
                    print(f"La tabla '{tabla}' ya existe.")
            
            # Si hay tablas faltantes, creamos todas las tablas del módulo de planillas
            if tablas_faltantes:
                print("Creando tablas del módulo de planillas...")
                
                # Crear tabla de empleados si no existe
                if 'empleados' in tablas_faltantes:
                    query_crear_empleados = text("""
                        CREATE TABLE empleados (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            codigo VARCHAR(20) NOT NULL UNIQUE,
                            nombre VARCHAR(100) NOT NULL,
                            apellido VARCHAR(100) NOT NULL,
                            identidad VARCHAR(20) NOT NULL UNIQUE,
                            fecha_nacimiento DATE NOT NULL,
                            fecha_contratacion DATE NOT NULL,
                            puesto VARCHAR(100) NOT NULL,
                            departamento VARCHAR(100) NOT NULL,
                            telefono VARCHAR(20) NOT NULL,
                            email VARCHAR(100),
                            direccion TEXT NOT NULL,
                            sueldo_base FLOAT NOT NULL,
                            estado VARCHAR(20) DEFAULT 'Activo',
                            cuenta_bancaria VARCHAR(50),
                            banco VARCHAR(100),
                            notas TEXT,
                            foto VARCHAR(255)
                        );
                    """)
                    db.session.execute(query_crear_empleados)
                    print("Tabla 'empleados' creada.")
                
                # Crear tabla de planillas si no existe
                if 'planillas' in tablas_faltantes:
                    query_crear_planillas = text("""
                        CREATE TABLE planillas (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            numero_planilla VARCHAR(50) NOT NULL UNIQUE,
                            fecha_inicio DATE NOT NULL,
                            fecha_fin DATE NOT NULL,
                            fecha_pago DATE NOT NULL,
                            tipo VARCHAR(50) NOT NULL,
                            estado VARCHAR(20) DEFAULT 'Borrador',
                            total_sueldos FLOAT DEFAULT 0.0,
                            total_deducciones FLOAT DEFAULT 0.0,
                            total_bonificaciones FLOAT DEFAULT 0.0,
                            total_neto FLOAT DEFAULT 0.0,
                            usuario_creacion VARCHAR(100),
                            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                            notas TEXT
                        );
                    """)
                    db.session.execute(query_crear_planillas)
                    print("Tabla 'planillas' creada.")
                
                # Crear tabla de detalles de planilla si no existe
                if 'planillas_detalles' in tablas_faltantes:
                    query_crear_detalles = text("""
                        CREATE TABLE planillas_detalles (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            planilla_id INT NOT NULL,
                            empleado_id INT NOT NULL,
                            dias_trabajados FLOAT NOT NULL DEFAULT 15.0,
                            horas_extra FLOAT DEFAULT 0.0,
                            sueldo_base FLOAT NOT NULL,
                            bonificacion FLOAT DEFAULT 0.0,
                            comisiones FLOAT DEFAULT 0.0,
                            horas_extra_monto FLOAT DEFAULT 0.0,
                            otros_ingresos FLOAT DEFAULT 0.0,
                            ihss FLOAT DEFAULT 0.0,
                            rap FLOAT DEFAULT 0.0,
                            isr FLOAT DEFAULT 0.0,
                            anticipo FLOAT DEFAULT 0.0,
                            prestamos FLOAT DEFAULT 0.0,
                            otras_deducciones FLOAT DEFAULT 0.0,
                            total_ingresos FLOAT DEFAULT 0.0,
                            total_deducciones FLOAT DEFAULT 0.0,
                            sueldo_neto FLOAT DEFAULT 0.0,
                            notas TEXT,
                            FOREIGN KEY (planilla_id) REFERENCES planillas(id) ON DELETE CASCADE,
                            FOREIGN KEY (empleado_id) REFERENCES empleados(id) ON DELETE CASCADE
                        );
                    """)
                    db.session.execute(query_crear_detalles)
                    print("Tabla 'planillas_detalles' creada.")
                
                # Crear tabla de asignación de empleados a proyectos si no existe
                if 'proyectos_empleados' in tablas_faltantes:
                    query_crear_proyectos = text("""
                        CREATE TABLE proyectos_empleados (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            empleado_id INT NOT NULL,
                            cotizacion_id INT NOT NULL,
                            fecha_asignacion DATE NOT NULL,
                            fecha_finalizacion DATE,
                            rol VARCHAR(100) NOT NULL,
                            horas_asignadas FLOAT DEFAULT 0.0,
                            costo_hora FLOAT DEFAULT 0.0,
                            costo_total FLOAT DEFAULT 0.0,
                            estado VARCHAR(20) DEFAULT 'Asignado',
                            notas TEXT,
                            FOREIGN KEY (empleado_id) REFERENCES empleados(id) ON DELETE CASCADE,
                            FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones(id) ON DELETE CASCADE
                        );
                    """)
                    db.session.execute(query_crear_proyectos)
                    print("Tabla 'proyectos_empleados' creada.")
            else:
                print("Todas las tablas del módulo de planillas ya existen.")
            
            # Confirmar los cambios
            db.session.commit()
            
            # Crear directorios necesarios si no existen
            import os
            if not os.path.exists('facturas'):
                os.makedirs('facturas')
                print("Directorio 'facturas' creado.")
            
            # Crear directorio para fotos de empleados si no existe
            if not os.path.exists(os.path.join('static', 'img', 'empleados')):
                os.makedirs(os.path.join('static', 'img', 'empleados'))
                print("Directorio 'static/img/empleados' creado.")
            
            print("Migración completada con éxito.")
            return True
        
        except Exception as e:
            db.session.rollback()
            print(f"Error durante la migración: {str(e)}")
            return False

if __name__ == "__main__":
    migrar_base_datos()