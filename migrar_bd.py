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
            
            # Confirmar los cambios
            db.session.commit()
            print("Migración completada con éxito.")
            
            # Crear directorio para facturas si no existe
            import os
            if not os.path.exists('facturas'):
                os.makedirs('facturas')
                print("Directorio 'facturas' creado.")
            
            return True
        
        except Exception as e:
            db.session.rollback()
            print(f"Error durante la migración: {str(e)}")
            return False

if __name__ == "__main__":
    migrar_base_datos()