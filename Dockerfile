# Usa una imagen base de Python
FROM python:3.11-slim

# Establece el directorio de trabajo (para que coincida con tu error)
WORKDIR /usr/src/app 

# Copia el script Flask y la carpeta 'data'
COPY app.py /usr/src/app/
# ESTO ES CRUCIAL: Copia la carpeta 'data' y todo su contenido
COPY data/ /usr/src/app/data/

# Copia el archivo de requisitos e instálalo primero
COPY requirements.txt /usr/src/app/
# Instala Flask (asumiendo que estás usando un requirements.txt, pero lo instalaremos directamente)
RUN pip install --no-cache-dir -r requirements.txt

# Puerto que expone el servidor Flask
EXPOSE 5000

# Comando para arrancar el servidor
CMD ["python", "app.py"]