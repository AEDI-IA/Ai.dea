# README - Cálculo de Distancias y Huella de Carbono (Caso1, Caso2, Caso3)

## 🧍️‍🦱 Descripción General

Este proyecto proporciona herramientas para calcular distancias entre ciudades (España, Europa y global), estimar la huella de carbono de los desplazamientos y proponer estrategias de compensación mediante reforestación. Está estructurado en tres casos de uso escalables.

---

## 📁 Scripts Incluidos

### `caso1.py` — Ciudades Españolas

Calcula distancias entre ciudades de España, tanto peninsulares como insulares, utilizando datos de OpenStreetMap y geolocalización. Permite:

* Generar bases de datos de distancias por transporte terrestre o aéreo.
* Integrar información sobre aeropuertos y estaciones de tren.
* Realizar cálculos de absorción y compensación de CO₂ mediante árboles.

**Características destacadas:**

* Uso de `geopy`, `osmnx` y `networkx`.
* Soporte para caché y logging avanzado.
* Clase `CarbonCalculator` para estimaciones detalladas de carbono.

---

### `caso2.py` — Ciudades Europeas

Extiende la funcionalidad del primer script al ámbito europeo. Soporta:

* Cálculo de distancias entre ciudades continentales e insulares.
* Diferentes modos de transporte (coche, tren, avión).
* Geocodificación con sistema de caché para mayor eficiencia.

**Características destacadas:**

* Diccionarios estructurados para distintas regiones (Irlanda, Sicilia, Cerdeña, etc.).
* Fórmula de Haversine para distancias aéreas.
* Mismos métodos de compensación de CO₂ que en `caso1.py`.

---

### `caso3.py` — Simulación de Asistencia y Huella de Carbono

Este módulo combina distancias con datos simulados de asistentes para eventos internacionales. Se compone de tres scripts:

* **Distancias:** Calcula distancias globales usando un catálogo de 40,000 ciudades.
* **Dataset de Asistencia:** Simula 32,000 asistentes con datos de procedencia, vuelos y clases.
* **Modelo de Asistencia:** Calcula la huella de carbono y propone estrategias de compensación.

**Características destacadas:**

* Generación de datos realistas y faltantes intencionales para robustez del modelo.
* Cálculo de emisiones según clase de vuelo y distancia.
* Herramientas de análisis y visualización de opciones de reforestación.

---

## 🧽 Clase Común: `CarbonCalculator`

Disponible en los tres scripts, esta clase centraliza los métodos para estimar y comparar estrategias de reforestación, incluyendo:

* Cálculo de CO₂ en biomasa.
* Tasas de absorción por especie, edad y tamaño del árbol.
* Tiempos de compensación para mezclas de árboles.

---

## ✅ Requisitos

* Python 3.8+
* Instalar dependencias:

```bash
pip install -r requirements.txt
```

---

## 🚀 Ejecución

```bash
python caso1.py     # Para ciudades de España  
python caso2.py     # Para ciudades de Europa  
python caso3_distancias.py  
python caso3_dataset_asistencia.py  
python caso3_modelo_asistencia.py
```
