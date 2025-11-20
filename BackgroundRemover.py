# BackgroundRemover.py - VERSIÓN FINAL ROBUSTA
# Este código está diseñado para funcionar con el Dockerfile que
# precarga 'u2netp.onnx' usando wget.

import os
import shutil
from datetime import datetime
from rembg import remove, new_session 
import io

# --- INTEGRACIÓN C++ (CYTHON) ---
# Se asume que el archivo compilado c_resizer.pyd o c_resizer.so existe.
try:
    # Importación relativa para Gunicorn/Flask
    from .c_resizer import resize_image_c 
except ImportError:
    try:
        # Importación normal para pruebas locales
        from c_resizer import resize_image_c 
    except ImportError:
        # Fallback si el módulo C++ no se compiló
        def resize_image_c(data_bytes, max_size):
            print("   -> ADVERTENCIA: Módulo C++ (c_resizer) no encontrado. La imagen no será redimensionada.")
            return data_bytes


class BackgroundRemover:
    # Definición del único modelo que usaremos (el que precarga el Dockerfile)
    MODEL_NAME = 'u2netp' # Modelo ligero (4.3 MB), optimizado para 4GB RAM
    
    def __init__(self, input_folder, output_folder):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self._setup_folders()
        
        # Lazy Loading: El modelo se carga en la primera petición
        self._session = None 

    @property
    def session(self):
        """
        Propiedad que carga el modelo 'u2netp' (que ya fue empaquetado por Docker).
        Si esta carga falla, es un error de memoria (RAM) o de archivo corrupto.
        """
        if self._session is None:
            print(f"⚙️ Iniciando carga del modelo IA (Modelo: {self.MODEL_NAME})...")
            
            try:
                # new_session cargará el modelo desde el caché de Docker
                # (precargado por wget en el Dockerfile)
                # NO intentará descargar nada.
                self._session = new_session(self.MODEL_NAME, providers=['CPUExecutionProvider'])
                print(f"✅ Modelo {self.MODEL_NAME} cargado exitosamente en RAM.")
            
            except Exception as e:
                # Si falla aquí, es grave (probablemente OutOfMemory o archivo corrupto)
                print(f"🛑 ERROR CRÍTICO: Falló la carga del modelo IA {self.MODEL_NAME}.")
                print(f"   Error: {e}")
                print(f"   Esto puede ser un error de OutOfMemory (RAM insuficiente).")
                self._session = None # Se mantiene como None para que las peticiones fallen
            
        return self._session

    def _setup_folders(self):
        """Verifica y crea las carpetas de entrada y salida."""
        os.makedirs(self.input_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        print(f"✔️ Carpetas verificadas: '{self.input_folder}' y '{self.output_folder}'.")

    def _get_resized_data(self, input_data: bytes, max_size: int = 1024) -> bytes:
        """
        Llama a la función optimizada en C++ (c_resizer) para redimensionar.
        """
        try:
            # Llama a la función C++ compilada
            resized_data = resize_image_c(input_data, max_size) 
            return resized_data
        except Exception as e:
            # Fallback si la función C++ falla en tiempo de ejecución
            print(f"   -> ERROR de ejecución C++: {e}. Usando datos originales.")
            return input_data

    # ... (Si tienes más funciones como _remove_background, mantenlas aquí)