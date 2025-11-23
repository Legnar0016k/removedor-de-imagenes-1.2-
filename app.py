import io
import os
import tempfile
from flask import Flask, request, send_file, render_template_string
from rembg import remove, new_session
from PIL import Image

# Configuración de la aplicación Flask
app = Flask(__name__)

# --- INICIALIZACIÓN DE LA IA (El cambio clave) ---
# Usamos 'u2net' que es el modelo estándar y mucho más pesado.
# Esto asegura que la RAM consumida al iniciar el contenedor esté en el rango de 1.5GB - 1.7GB.
print("Inicializando la sesión de rembg con el modelo u2net (versión grande)...")
try:
    # Se inicializa la sesión una sola vez para que el modelo se cargue en memoria.
    REMBG_SESSION = new_session('u2net') 
    print("Modelo 'u2net' cargado exitosamente en memoria.")
except Exception as e:
    print(f"Error al cargar el modelo U2NET: {e}")
    REMBG_SESSION = None
# --------------------------------------------------

# HTML de la página de inicio (solo para verificar que el servidor está activo)
HTML_INDEX = """
<!DOCTYPE html>
<html>
<head>
    <title>Removedor de Fondo de IA (Modelo Pesado)</title>
    <style>
        body { font-family: sans-serif; margin: 50px; text-align: center; }
        h1 { color: #333; }
        p { color: #555; }
    </style>
</head>
<body>
    <h1>Servicio de Remoción de Fondo de IA</h1>
    <p>¡El servicio de IA con el modelo pesado (u2net) está funcionando correctamente!</p>
    <p>Endpoint de la API: <strong>/remover</strong> (Método POST)</p>
    <p>Ahora puedes enviar imágenes aquí para procesamiento.</p>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    """Ruta de inicio para verificar que el servicio está activo."""
    return render_template_string(HTML_INDEX)

@app.route("/remover", methods=["POST"])
def remover_fondo():
    """
    Ruta para procesar una imagen enviada por POST y remover el fondo usando rembg.
    """
    if not REMBG_SESSION:
        # Si la sesión no se cargó (por ejemplo, el modelo no se descargó o cargó), 
        # devolvemos un error 503.
        return "Error interno del servidor: El modelo de IA no se pudo cargar.", 503

    if 'file' not in request.files:
        return "Error: No se encontró la parte 'file' en la solicitud.", 400

    file = request.files['file']
    
    if file.filename == '':
        return "Error: Nombre de archivo no especificado.", 400

    if file:
        try:
            # Leer la imagen de entrada en memoria
            input_image_data = file.read()
            
            # Usar el modelo pesado cargado en la sesión
            # El parámetro session=REMBG_SESSION es clave para usar la versión pesada
            output_image_data = remove(input_image_data, session=REMBG_SESSION)

            # Preparar la imagen de salida (PNG con fondo transparente)
            return send_file(
                io.BytesIO(output_image_data),
                mimetype='image/png',
                as_attachment=True,
                download_name=f"sin_fondo_{file.filename.split('.')[0]}.png"
            )

        except Exception as e:
            # Captura cualquier error durante el procesamiento (por ejemplo, formato de imagen no válido)
            return f"Error al procesar la imagen: {str(e)}", 500

    return "Error desconocido al procesar la solicitud.", 500

if __name__ == "__main__":
    # Si se ejecuta localmente, Flask utilizará el puerto 8080.
    # Cloud Run usa Gunicorn, por lo que esto solo aplica para pruebas locales.
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))