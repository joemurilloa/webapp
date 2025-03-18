/**
 * Script para el módulo de Planillas
 * Remodelaciones William Murillo
 * Desarrollado por Joe Murillo
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Módulo de Planillas iniciado');
    
    // Inicializar tooltips si existen
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Funciones para gestión de empleados
    setupEmpleadosForm();
    
    // Funciones para la creación de planillas
    setupPlanillasForm();
    
    // Funciones para reportes
    setupReportesInteractivos();
    
    /**
     * Configura el formulario de empleados
     */
    function setupEmpleadosForm() {
        const formEmpleado = document.getElementById('empleadoForm');
        if (!formEmpleado) return;
        
        // Vista previa de foto
        const inputFoto = document.getElementById('foto');
        if (inputFoto) {
            inputFoto.addEventListener('change', function() {
                const preview = document.getElementById('previewFoto');
                const file = this.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        preview.querySelector('img').src = e.target.result;
                        preview.classList.remove('d-none');
                    };
                    reader.readAsDataURL(file);
                } else {
                    preview.classList.add('d-none');
                }
            });
        }
        
        // Formato de fecha de nacimiento (evitar menores de edad o mayores de 70 años)
        const fechaNacimiento = document.getElementById('fecha_nacimiento');
        if (fechaNacimiento) {
            const hoy = new Date();
            const min = new Date();
            min.setFullYear(hoy.getFullYear() - 70); // Máximo 70 años
            
            const max = new Date();
            max.setFullYear(hoy.getFullYear() - 18); // Mínimo 18 años
            
            fechaNacimiento.min = min.toISOString().split('T')[0];
            fechaNacimiento.max = max.toISOString().split('T')[0];
        }
        
        // Calculadora de salario mensual a partir de salario por hora
        const sueldoHora = document.getElementById('sueldo_hora');
        const sueldoBase = document.getElementById('sueldo_base');
        
        if (sueldoHora && sueldoBase) {
            sueldoHora.addEventListener('input', function() {
                const valorHora = parseFloat(this.value) || 0;
                // Salario mensual = valor por hora * 8 horas * 30 días
                const salarioMensual = valorHora * 8 * 30;
                sueldoBase.value = salarioMensual.toFixed(2);
            });
            
            sueldoBase.addEventListener('input', function() {
                const salarioMensual = parseFloat(this.value) || 0;
                // Valor por hora = salario mensual / (8 horas * 30 días)
                const valorHora = salarioMensual / (8 * 30);
                sueldoHora.value = valorHora.toFixed(2);
            });
        }
        
        // Formatear automáticamente el número de identidad de Honduras
        const inputIdentidad = document.getElementById('identidad');
        if (inputIdentidad) {
            inputIdentidad.addEventListener('input', function() {
                let identidad = this.value.replace(/\D/g, '');
                if (identidad.length > 0) {
                    // Formato para identidad de Honduras: XXXX-XXXX-XXXXX
                    if (identidad.length <= 4) {
                        this.value = identidad;
                    } else if (identidad.length <= 8) {
                        this.value = identidad.substring(0, 4) + '-' + identidad.substring(4);
                    } else {
                        this.value = identidad.substring(0, 4) + '-' + identidad.substring(4, 8) + '-' + identidad.substring(8, 13);
                    }
                }
            });
        }
    }
    
    /**
     * Configura el formulario de planillas
     */
    function setupPlanillasForm() {
        const formPlanilla = document.getElementById('planillaForm');
        if (!formPlanilla) return;
        
        // Seleccionar/deseleccionar todos los empleados
        const seleccionarTodos = document.getElementById('seleccionarTodos');
        if (seleccionarTodos) {
            seleccionarTodos.addEventListener('change', function() {
                const checkboxes = document.querySelectorAll('.checkbox-empleado');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = this.checked;
                });
            });
        }
        
        // Filtrar empleados por búsqueda
        const buscarEmpleado = document.getElementById('buscarEmpleado');
        if (buscarEmpleado) {
            buscarEmpleado.addEventListener('input', function() {
                const busqueda = this.value.toLowerCase();
                const filas = document.querySelectorAll('.empleado-row');
                
                filas.forEach(fila => {
                    const nombre = fila.dataset.nombre.toLowerCase();
                    if (nombre.includes(busqueda)) {
                        fila.style.display = '';
                    } else {
                        fila.style.display = 'none';
                    }
                });
            });
        }
        
        // Calcular deducciones automáticamente
        formPlanilla.querySelectorAll('.dias-trabajados, .horas-extra').forEach(input => {
            input.addEventListener('input', function() {
                const empleadoId = this.id.split('_').pop();
                calcularDeduccionesEmpleado(empleadoId);
            });
        });
        
        // Calcular deducciones para un empleado
        function calcularDeduccionesEmpleado(empleadoId) {
            // Implementar cálculos de deducciones según la legislación de Honduras
            // Esta es una versión simplificada
            console.log(`Calculando deducciones para empleado ${empleadoId}`);
        }
    }
    
    /**
     * Configura los reportes interactivos
     */
    function setupReportesInteractivos() {
        // Implementar funciones para gestionar reportes interactivos
        const contenedorReportes = document.getElementById('reporte-container');
        if (!contenedorReportes) return;
        
        // Funcionalidad para cambiar entre tipos de reportes
        document.querySelectorAll('.report-card').forEach(card => {
            card.addEventListener('click', function() {
                const reporteId = this.id;
                mostrarReporte(reporteId);
            });
        });
        
        function mostrarReporte(reporteId) {
            console.log(`Mostrando reporte: ${reporteId}`);
            // Implementar lógica para mostrar el reporte seleccionado
        }
    }
});

/**
 * Formatea un valor como moneda (Lempiras)
 * @param {number} valor - El valor a formatear
 * @returns {string} - Valor formateado con formato de moneda
 */
function formatearMoneda(valor) {
    return new Intl.NumberFormat('es-HN', {
        style: 'currency',
        currency: 'HNL',
        minimumFractionDigits: 2
    }).format(valor);
}

/**
 * Calcula la edad a partir de una fecha de nacimiento
 * @param {string} fechaNacimiento - Fecha de nacimiento en formato YYYY-MM-DD
 * @returns {number} - Edad en años
 */
function calcularEdad(fechaNacimiento) {
    const hoy = new Date();
    const fechaNac = new Date(fechaNacimiento);
    let edad = hoy.getFullYear() - fechaNac.getFullYear();
    const mes = hoy.getMonth() - fechaNac.getMonth();
    
    if (mes < 0 || (mes === 0 && hoy.getDate() < fechaNac.getDate())) {
        edad--;
    }
    
    return edad;
}

/**
 * Exporta una tabla a Excel
 * @param {string} tableId - ID de la tabla a exportar
 * @param {string} filename - Nombre del archivo Excel
 */
function exportarTablaExcel(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    // Crear un libro de trabajo
    const wb = XLSX.utils.table_to_book(table);
    
    // Exportar a Excel
    XLSX.writeFile(wb, `${filename}.xlsx`);
}