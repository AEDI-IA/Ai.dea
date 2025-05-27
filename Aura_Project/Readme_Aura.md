# AURA – Scripts explicativos por caso de uso

AURA es una herramienta modular que calcula el impacto ambiental de eventos, centrada inicialmente en la movilidad de asistentes y transporte de equipos. Integra modelos de machine learning y permite estimar huella de carbono, analizar compensaciones por reforestación y adaptar cálculos a distintos contextos. Cada uno de los scripts aborda una parte específica del sistema.

---

# Guía del Código `caso1.py`

**Propósito:**  
Calcula distancias entre ciudades españolas (incluyendo islas) y gestiona datos de transporte (aeropuertos y estaciones). También permite estimar compensaciones mediante árboles.

**Características clave:**

- Manejo de grafos viales con `osmnx`
- Geocodificación optimizada con caché
- Base de datos extensible por región
- Clase `CarbonCalculator` para estimar CO₂ y compensación

---

# Guía del Código `caso2.py`

**Propósito:**  
Expande el análisis de `caso1.py` al contexto europeo. Calcula distancias entre ciudades del continente e islas, y soporta modos de transporte como avión, tren y coche.

**Características clave:**

- Geocodificación por nombre y país
- Gestión de casos especiales (Irlanda, Sicilia, Cerdeña)
- Soporte para ciudades sin tren
- Cálculo de distancias usando fórmula de Haversine y redes viales
- Reutiliza `CarbonCalculator` para estimaciones de compensación

---

# Guía del Código `caso3.py`

**Propósito:**  
Genera un dataset sintético de asistentes internacionales a un evento. Simula su procedencia, vuelos, clases y calcula la huella de carbono para entrenamiento de modelos.

**Características clave:**

- Geocodificación eficiente con catálogo de 40.000 ciudades
- Simulación realista de asistencia (nacional/internacional)
- Cálculo de CO₂ por tipo de vuelo y clase
- Introducción de valores faltantes para simular ruido de datos reales
- Soporte para cálculo de reforestación con `CarbonCalculator`

---

## 🧮 Clase Común: `CarbonCalculator`

Presente en los tres casos, esta clase agrupa métodos clave para el análisis y la compensación de carbono.

**Funciones principales:**

- Estimación de CO₂ en biomasa  
- Tasas de absorción por tipo, edad y tamaño del árbol  
- Cálculo de tiempos de compensación para mezclas forestales  

---

## ✅ Requisitos

- Python 3.8 o superior  
- Instalación de dependencias:

```bash
pip install -r requirements.txt

