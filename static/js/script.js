/**
 * Script principal para la aplicación de cotizaciones
 * Remodelaciones William Murillo
 * Desarrollado por Joe Murillo
 */

// Inicializar funciones cuando el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', function() {
    console.log('Aplicación de Cotizaciones iniciada');
    
    // Obtener fecha actual y formatearla
    const hoy = new Date();
    const fechaFormateada = hoy.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
    
    // Mostrar fecha en elementos con clase 'fecha-actual' si existen
    document.querySelectorAll('.fecha-actual').forEach(function(el) {
        el.textContent = fechaFormateada;
    });
    
    // Inicializar tooltips de Bootstrap si existen
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Añadir comportamiento para confirmar antes de resetear el formulario
    document.querySelectorAll('form button[type="reset"]').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            if (!confirm('¿Está seguro de que desea limpiar todos los campos del formulario?')) {
                e.preventDefault();
            }
        });
    });
});

/**
 * Formatea un número como moneda (Lempiras)
 * @param {number} numero - El número a formatear
 * @returns {string} - Número formateado con formato de moneda
 */
function formatearMoneda(numero) {
    return new Intl.NumberFormat('es-HN', {
        style: 'currency',
        currency: 'HNL',
        minimumFractionDigits: 2
    }).format(numero);
}

/**
 * Muestra una notificación temporal
 * @param {string} mensaje - Mensaje a mostrar
 * @param {string} tipo - Tipo de notificación (success, danger, warning, info)
 * @param {number} duracion - Duración en milisegundos
 */
function mostrarNotificacion(mensaje, tipo = 'info', duracion = 3000) {
    // Crear elemento de notificación
    const notificacion = document.createElement('div');
    notificacion.className = `toast align-items-center text-white bg-${tipo} border-0`;
    notificacion.setAttribute('role', 'alert');
    notificacion.setAttribute('aria-live', 'assertive');
    notificacion.setAttribute('aria-atomic', 'true');
    
    // Contenido de la notificación
    notificacion.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${mensaje}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Cerrar"></button>
        </div>
    `;
    
    // Contenedor para las notificaciones
    let contenedor = document.querySelector('.toast-container');
    if (!contenedor) {
        contenedor = document.createElement('div');
        contenedor.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(contenedor);
    }
    
    // Añadir notificación al contenedor
    contenedor.appendChild(notificacion);
    
    // Inicializar y mostrar la notificación
    const toast = new bootstrap.Toast(notificacion, {
        autohide: true,
        delay: duracion
    });
    toast.show();
    
    // Eliminar del DOM después de ocultarse
    notificacion.addEventListener('hidden.bs.toast', function() {
        notificacion.remove();
    });
}

/**
 * Valida un correo electrónico
 * @param {string} email - Correo electrónico a validar
 * @returns {boolean} - true si es válido, false si no
 */
function validarEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

/**
 * Valida un número de teléfono hondureño
 * @param {string} telefono - Número a validar
 * @returns {boolean} - true si es válido, false si no
 */
function validarTelefono(telefono) {
    // Remover espacios, guiones y paréntesis
    const numeroLimpio = telefono.replace(/[\s\-()]/g, '');
    
    // Validar formato de Honduras (inicia con +504 o 504, seguido de 8 dígitos)
    const regex = /^(\+?504)?\d{8}$/;
    return regex.test(numeroLimpio);
}

/**
 * Descarga un archivo desde una URL
 * @param {string} url - URL del archivo a descargar
 * @param {string} nombreArchivo - Nombre del archivo de descarga
 */
function descargarArchivo(url, nombreArchivo) {
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.download = nombreArchivo;
    document.body.appendChild(enlace);
    enlace.click();
    document.body.removeChild(enlace);
}

// Funcionalidad para búsqueda y selección de clientes en el formulario de cotización
document.addEventListener('DOMContentLoaded', function() {
    // Verificar si estamos en la página de cotizaciones
    const usarClienteExistente = document.getElementById('usarClienteExistente');
    if (!usarClienteExistente) return;
    
    // Referencias a elementos del DOM
    const clienteExistenteContainer = document.getElementById('clienteExistenteContainer');
    const buscarCliente = document.getElementById('buscarCliente');
    const btnBuscarCliente = document.getElementById('btnBuscarCliente');
    const resultadosBusqueda = document.getElementById('resultadosBusqueda');
    
    // Campos del formulario
    const clienteIdInput = document.getElementById('cliente_id');
    const nombreInput = document.getElementById('nombre');
    const apellidoInput = document.getElementById('apellido');
    const telefonoInput = document.getElementById('telefono');
    const emailInput = document.getElementById('email');
    const direccionInput = document.getElementById('direccion');
    
    // Mostrar/ocultar el buscador de clientes existentes
    usarClienteExistente.addEventListener('change', function() {
        clienteExistenteContainer.style.display = this.checked ? 'block' : 'none';
        
        // Si se desmarca, limpiar el cliente seleccionado
        if (!this.checked) {
            limpiarFormularioCliente();
            clienteIdInput.value = '';
        }
    });
    
    // Función para limpiar el formulario
    function limpiarFormularioCliente() {
        nombreInput.value = '';
        apellidoInput.value = '';
        telefonoInput.value = '';
        emailInput.value = '';
        direccionInput.value = '';
        clienteIdInput.value = '';
    }
    
    // Búsqueda de clientes al escribir
    let timeoutId;
    buscarCliente.addEventListener('input', function() {
        const busqueda = this.value.trim();
        
        // Limpiar timeout anterior
        clearTimeout(timeoutId);
        
        // Ocultar resultados si la búsqueda está vacía
        if (busqueda.length < 3) {
            resultadosBusqueda.style.display = 'none';
            return;
        }
        
        // Esperar 300ms después de que el usuario deje de escribir para hacer la búsqueda
        timeoutId = setTimeout(() => {
            buscarClientes(busqueda);
        }, 300);
    });
    
    // También permitir búsqueda al hacer clic en el botón
    btnBuscarCliente.addEventListener('click', function() {
        const busqueda = buscarCliente.value.trim();
        if (busqueda.length >= 3) {
            buscarClientes(busqueda);
        }
    });
    
    // Función para buscar clientes
    function buscarClientes(busqueda) {
        // Mostrar indicador de carga
        resultadosBusqueda.innerHTML = '<div class="p-3 text-center"><div class="spinner-border spinner-border-sm text-primary" role="status"></div> Buscando...</div>';
        resultadosBusqueda.style.display = 'block';
        
        // Realizar solicitud AJAX
        fetch(`/api/buscar-clientes?q=${encodeURIComponent(busqueda)}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    mostrarResultadosBusqueda(data.clientes);
                } else {
                    resultadosBusqueda.innerHTML = `<div class="p-3 text-center text-danger">${data.mensaje}</div>`;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                resultadosBusqueda.innerHTML = '<div class="p-3 text-center text-danger">Error al buscar clientes</div>';
            });
    }
    
    // Función para mostrar resultados de búsqueda
    function mostrarResultadosBusqueda(clientes) {
        // Limpiar resultados anteriores
        resultadosBusqueda.innerHTML = '';
        
        if (clientes.length === 0) {
            resultadosBusqueda.innerHTML = '<div class="p-3 text-center">No se encontraron clientes</div>';
            return;
        }
        
        // Crear elemento para cada cliente
        clientes.forEach(cliente => {
            const itemCliente = document.createElement('a');
            itemCliente.href = '#';
            itemCliente.className = 'list-group-item list-group-item-action';
            itemCliente.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${cliente.nombre} ${cliente.apellido}</strong>
                        <small class="d-block text-muted">${cliente.email}</small>
                    </div>
                    <span class="text-primary">${cliente.telefono}</span>
                </div>
            `;
            
            // Evento para seleccionar cliente
            itemCliente.addEventListener('click', function(e) {
                e.preventDefault();
                seleccionarCliente(cliente);
            });
            
            resultadosBusqueda.appendChild(itemCliente);
        });
    }
    
    // Función para seleccionar un cliente
    function seleccionarCliente(cliente) {
        // Llenar formulario con datos del cliente
        nombreInput.value = cliente.nombre;
        apellidoInput.value = cliente.apellido;
        telefonoInput.value = cliente.telefono;
        emailInput.value = cliente.email;
        direccionInput.value = cliente.direccion;
        clienteIdInput.value = cliente.id;
        
        // Ocultar resultados
        resultadosBusqueda.style.display = 'none';
        
        // Mostrar nombre del cliente seleccionado en el campo de búsqueda
        buscarCliente.value = `${cliente.nombre} ${cliente.apellido}`;
        
        // Mostrar notificación
        mostrarNotificacion(`Cliente seleccionado: ${cliente.nombre} ${cliente.apellido}`, 'success');
    }
});