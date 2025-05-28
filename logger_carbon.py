import os
import re
from datetime import datetime 
import logging
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
log_filename = f"logger_carbon{timestamp}.txt"

logging.basicConfig(
    
level=logging.INFO
,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename, mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
log = logging.info
  # Alias para usar el log como si fuera print() 

# Ruta de la carpeta donde están los logs
carpeta_logs = r"C:\Users\Miguel\Desktop\Codecarbon\LOG"

# Expresión regular para capturar valores tipo: 0.000123 o 1.23e-05 seguidos de 'kg CO₂eq'
patron = re.compile(r"([\d\.eE+-]+)\s*kg CO₂eq")

# Lista para guardar los resultados
resultados = []

# Recorrer todos los archivos .txt en la carpeta
for nombre_archivo in os.listdir(carpeta_logs):
    if nombre_archivo.endswith(".txt"):
        ruta_archivo = os.path.join(carpeta_logs, nombre_archivo)
        try:
            with open(ruta_archivo, "r", encoding="utf-8") as archivo:
                contenido = archivo.read()
                coincidencias = patron.findall(contenido)
                for valor_str in coincidencias:
                    try:
                        valor = float(valor_str)
                        resultados.append((nombre_archivo, valor))
                    except ValueError:
                        log(f"⚠️ No se pudo convertir '{valor_str}' en {nombre_archivo}")
        except Exception as e:
            log(f"❌ Error con {nombre_archivo}: {e}")

# Mostrar resultados individuales
log("----- Emisiones encontradas por archivo -----")
for archivo, valor in resultados:
    log(f"{archivo}: {valor:.15f} kg CO₂eq")

# Calcular y mostrar suma total
total_emisiones = sum(valor for _, valor in resultados)
log("\n===== TOTAL EMISIONES =====")
log(f"Total: {total_emisiones:.15f} kg CO₂eq")
