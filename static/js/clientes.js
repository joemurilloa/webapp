/**
 * Script para la gestión de clientes
 * Remodelaciones William Murillo
 * Desarrollado por Joe Murillo
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Módulo de Gestión de Clientes iniciado');
    
    // Inicializar tooltips si existen
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Función para validar el formulario de cliente
    function validarFormularioCliente(form) {
        // Validar email
        const email = form.querySelector('#email').value;
        if (!validarEmail(email)) {
            mostrarNotificacion('Por favor ingrese un correo electrónico válido', 'warning');
            return false;
        }
        
        // Validar teléfono
        const telefono = form.querySelector('#telefono').value;
        if (!validarTelefono(telefono)) {
            mostrarNotificacion('Por favor ingrese un número de teléfono válido', 'warning');
            return false;
        }
        
        // Todo validado
        return true;
    }
    
    // Añadir validación al formulario de cliente
    const formCliente = document.getElementById('clienteForm');
    if (formCliente) {
        formCliente.addEventListener('submit', function(e) {
            if (!validarFormularioCliente(this)) {
                e.preventDefault();
                return false;
            }
        });
    }
    
    // Función para formatear teléfonos automáticamente
    const inputTelefono = document.getElementById('telefono');
    if (inputTelefono) {
        inputTelefono.addEventListener('input', function() {
            let numero = this.value.replace(/\D/g, '');
            if (numero.length > 0) {
                // Formato para teléfonos de Honduras: +504 XXXX-XXXX
                if (numero.length <= 4) {
                    this.value = numero;
                } else if (numero.length <= 8) {
                    this.value = numero.substring(0, 4) + '-' + numero.substring(4);
                } else {
                    this.value = '+504 ' + numero.substring(0, 4) + '-' + numero.substring(4, 12);
                }
            }
        });
    }
    
    // Función para buscar clientes en tiempo real
    const inputBusqueda = document.getElementById('filtroNombre');
    if (inputBusqueda) {
        let timeoutId;
        inputBusqueda.addEventListener('input', function() {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                document.getElementById('filtroForm').submit();
            }, 500);
        });
    }
    
    // Inicializar gráficos si hay elementos canvas
    const chartElements = document.querySelectorAll('.cliente-chart');
    if (chartElements.length > 0 && typeof Chart !== 'undefined') {
        chartElements.forEach(function(canvas) {
            const ctx = canvas.getContext('2d');
            const chartType = canvas.dataset.type || 'bar';
            const chartData = JSON.parse(canvas.dataset.values || '[]');
            const chartLabels = JSON.parse(canvas.dataset.labels || '[]');
            
            new Chart(ctx, {
                type: chartType,
                data: {
                    labels: chartLabels,
                    datasets: [{
                        label: canvas.dataset.title || '',
                        data: chartData,
                        backgroundColor: [
                            'rgba(54, 162, 235, 0.5)',
                            'rgba(75, 192, 192, 0.5)',
                            'rgba(255, 206, 86, 0.5)',
                            'rgba(255, 99, 132, 0.5)',
                            'rgba(153, 102, 255, 0.5)'
                        ],
                        borderColor: [
                            'rgba(54, 162, 235, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(255, 206, 86, 1)',
                            'rgba(255, 99, 132, 1)',
                            'rgba(153, 102, 255, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        });
    }
});