document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const submitButton = document.getElementById('submit-button');
    const fileNameDisplay = document.getElementById('file-name-display');
    const statusMessage = document.getElementById('status-message'); 

    // --- LÓGICA DE SELECCIÓN Y HABILITACIÓN DEL BOTÓN ---
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            submitButton.disabled = false; 
            fileNameDisplay.textContent = `Archivo seleccionado: ${fileInput.files[0].name}`;
        } else {
            submitButton.disabled = true;
            fileNameDisplay.textContent = '';
        }
    });

    // --- LÓGICA DE ENVÍO DEL FORMULARIO ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (fileInput.files.length === 0 || submitButton.disabled) {
            alert("Por favor, selecciona una imagen antes de continuar.");
            return;
        }

        // 1. Mostrar estado inicial (Procesando...)
        statusMessage.style.display = 'block';
        statusMessage.style.backgroundColor = '#ffeaa7'; // Amarillo/Advertencia
        statusMessage.style.color = '#333';
        statusMessage.textContent = 'Procesando, por favor espere...';
        
        submitButton.disabled = true;
        submitButton.textContent = 'Procesando...';

        const formData = new FormData(form);

        try {
            // 2. Enviar la petición al servidor Flask
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                // 3. Manejar la descarga
                const blob = await response.blob();
                
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                
                // Obtener el nombre del archivo
                const disposition = response.headers.get('Content-Disposition');
                let filename = 'removed_bg.png';
                if (disposition && disposition.indexOf('attachment') !== -1) {
                    const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                    const matches = filenameRegex.exec(disposition);
                    if (matches != null && matches[1]) {
                        filename = matches[1].replace(/['"]/g, '');
                    }
                }
                
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url); 

                // 4. CAMBIO CLAVE: Mostrar el éxito en el div #status-message (VERDE)
                statusMessage.style.backgroundColor = '#d4edda'; // Color verde claro
                statusMessage.style.color = '#155724';           // Color verde oscuro
                statusMessage.textContent = `✅ ¡Fondo retirado con éxito! Descargando ${filename}.`;

            } else {
                // 4. Manejo de errores
                const errorText = await response.text();
                statusMessage.style.backgroundColor = '#f8d7da'; // Color rojo claro
                statusMessage.style.color = '#721c24';            // Color rojo oscuro
                statusMessage.textContent = '❌ Error al procesar la imagen: ' + errorText;
            }
        } catch (error) {
            console.error('Error de red o de proceso:', error);
            statusMessage.style.backgroundColor = '#f8d7da';
            statusMessage.style.color = '#721c24';
            statusMessage.textContent = '❌ Error de conexión. Revisa la consola de Flask.';
        } finally {
            // 5. Restablecer la interfaz, manteniendo el mensaje visible
            
            submitButton.disabled = true; 
            submitButton.textContent = 'Quitar Fondo...';
            form.reset(); 
            fileNameDisplay.textContent = ''; 
            
            // Opcional: Ocultar el mensaje después de 5 segundos para limpiar la interfaz
            setTimeout(() => {
                statusMessage.style.display = 'none';
            }, 5000);
        }
    });
});