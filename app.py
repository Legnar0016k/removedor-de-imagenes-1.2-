from flask import Flask, render_template, request, send_file
import os
import io
import shutil
from rembg import remove, new_session 
# Asegúrate de que el nombre del archivo de tu clase sea 'BackgroundRemover.py' 
from BackgroundRemover import BackgroundRemover 

app = Flask(__name__)

# --- CONFIGURACIÓN ---
UPLOAD_FOLDER = 'temp_uploads'
PROCESSED_FOLDER = 'temp_processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Crea una instancia de tu removedor.
# IMPORTANTE: El modelo de IA NO se carga aquí (gracias al Lazy Loading en la clase).
remover = BackgroundRemover(UPLOAD_FOLDER, PROCESSED_FOLDER)

# --- RUTAS DE LA APLICACIÓN ---

@app.route('/')
def index():
    """Renderiza la página principal de la interfaz web."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Maneja la subida, procesamiento y descarga del archivo."""
    
    # Manejo de errores de archivos
    if 'file' not in request.files or request.files['file'].filename == '':
        return 'No se seleccionó o se encontró un archivo.', 400
    
    file = request.files['file']
    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    
    # 🚨 NOTA: La propiedad 'remover.session' se accede aquí. Si es la primera vez,
    # el modelo de IA se carga en este momento (Lazy Loading).
    if not remover.session:
        return 'Error del servidor: El modelo de IA no se pudo cargar. Intente reiniciar.', 500

    try:
        # 1. Guardar el archivo subido
        file.save(input_path)
        
        # 2. Leer el archivo a bytes para el procesamiento
        with open(input_path, 'rb') as f:
            input_bytes = f.read()

        # 3. Redimensionar (Llamada al módulo C++ dentro de BackgroundRemover)
        print("Iniciando redimensionamiento (C++)...")
        # El método llama a la función C++ y devuelve los datos optimizados
        resized_data = remover._get_resized_data(input_bytes, max_size=1024)
        print("Redimensionamiento completado.")

        # 4. Procesar la imagen redimensionada (Usando la sesión cargada)
        print(f"Iniciando procesamiento de {file.filename}...")
        output_data = remove(resized_data, session=remover.session)
        print("Procesamiento completado.")

        # 5. Devolver la imagen procesada al navegador
        return send_file(
            io.BytesIO(output_data),
            mimetype='image/png',
            as_attachment=True,
            download_name='removed_bg_' + file.filename.rsplit('.', 1)[0] + '.png'
        )
        
    except Exception as e:
        print(f"Error durante el procesamiento: {e}")
        return f'Error al procesar la imagen: {e}', 500
        
    finally:
        # 6. Limpiar el archivo subido (sea exitoso o no)
        if os.path.exists(input_path):
            os.remove(input_path)
            
# --- INICIO DEL SERVIDOR ---

if __name__ == '__main__':
    # Limpieza al inicio
    if os.path.exists(UPLOAD_FOLDER):
        shutil.rmtree(UPLOAD_FOLDER) 
    os.makedirs(UPLOAD_FOLDER, exist_ok=True) 
    
    # El servidor inicia de forma INSTANTÁNEA gracias al Lazy Loading
    print("🚀 Servidor Flask iniciado. Visita http://127.0.0.1:5000")
    
    app.run(debug=True)