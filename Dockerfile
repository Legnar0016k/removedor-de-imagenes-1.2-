# Usa una imagen base de Python Slim para reducir el tamaño
FROM python:3.11-slim

# 1. Configura el directorio de trabajo
WORKDIR /app

# 2. Instala herramientas C/C++, WGET Y LIBRERÍAS DE IMAGEN
#    Añadido: --no-install-recommends para instalar solo lo esencial.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Copia los archivos de requerimientos
COPY requirements.txt .

# 4. Instala todas las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# =========================================================================
# 5. GARANTÍA DE EMPAQUETADO DEL MODELO
# =========================================================================
ENV MODEL_CACHE_PATH /root/.u2net
ENV MODEL_NAME u2netp.onnx
ENV MODEL_URL https://github.com/danielgatis/rembg/releases/download/v0.0.0/$MODEL_NAME

RUN mkdir -p $MODEL_CACHE_PATH && \
    echo "Descargando el modelo ligero $MODEL_NAME..." && \
    wget -O $MODEL_CACHE_PATH/$MODEL_NAME $MODEL_URL && \
    echo "¡Descarga completa y empaquetada con éxito!"

# 6. Copia el resto del código fuente
#    (NOTA: El archivo .dockerignore debe estar presente y limpio)
COPY . .

# 7. Compila el módulo Cython/C++ DENTRO del contenedor
RUN python setup.py build_ext --inplace

# Expone el puerto 8080 (Cloud Run lo requiere)
EXPOSE 8080

# Comando para iniciar el servidor Gunicorn.
# Importante: Gunicorn DEBE escuchar en 0.0.0.0:8080, NO 5000.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
