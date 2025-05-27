# AURA: Análisis de Uso de Recursos de Acontecimientos

AURA nace como una solución práctica para facilitar la toma de decisiones estratégicas por parte de los organizadores de eventos, con el objetivo de reducir y compensar su impacto ambiental. Desde sus primeras fases, el proyecto adoptó un enfoque centrado en el usuario, priorizando el desarrollo de herramientas escalables, accesibles y alineadas con las necesidades reales del sector.

La herramienta integra modelos de aprendizaje automático para estimar la huella de carbono generada tanto por los asistentes como por el transporte de equipos multimedia. AURA no solo cuantifica emisiones: proporciona métricas accionables que promueven decisiones responsables, y actúa como un aliado estratégico para fomentar una cultura de sostenibilidad en la organización de eventos.


![Diagrama Mermaid Aura 1](https://github.com/user-attachments/assets/b274db7a-17e0-4d29-9ddb-bbe79657a8fa)



---

## 🌍 Visión General Técnica

- 🔁 Modelos de ML para emisiones de asistentes (`MLPRegressor`)
- 🔊 Modelos de ML para emisiones de equipos multimedia (`RandomForestRegressor`)
- 🧱 Arquitectura modular y escalable
- 🌱 Integración de mecanismos de compensación (reforestación)
- 📊 Resultado claros para usuarios técnicos y no técnicos

---

## 📁 Estructura del Proyecto

### `caso1.py` — Eventos Nacionales (España)
Analiza eventos dentro de España (península e islas).

- 🗺️ Cálculo de distancias entre ciudades usando grafos viales (`osmnx`)
- 🛫 Considera aeropuertos y estaciones ferroviarias
- 🌳 Estimación de CO₂ con clase `CarbonCalculator`
- 🧾 Analisis de impacto y propuestas de compensación

### `caso2.py` — Eventos Internacionales (Europa)
Expande el análisis a Europa, considerando múltiples modos de transporte.

- 🌍 Geocodificación de ciudades y países
- 🚆 Soporte para ciudades sin conexión ferroviaria
- 📐 Cálculo de distancias vía Haversine y redes viales
- 🔁 Reutiliza y extiende la lógica de `caso1.py`

### `caso3.py` — Eventos Globales
Genera datasets sintéticos para modelado predictivo.

- ✈️ Simulación realista de asistentes internacionales
- 🌎 Base con más de 40,000 ciudades
- ⚠️ ~15% de valores faltantes para simular casos reales
- 🧪 Útil para entrenamiento de modelos ML

---

## 🧠 Componentes de Aprendizaje Automático

- `MLPRegressor`: Estima emisiones individuales en función de procedencia, distancia y clase de viaje.
- `RandomForestRegressor`: Predice huella de carbono de equipos audiovisuales considerando consumo energético, número de dispositivos y duración.

Ambos modelos están integrados en pipelines con datos numéricos y categóricos para:
- Capturar relaciones no lineales
- Soportar datos heterogéneos
- Ofrecer un buen balance entre precisión y eficiencia

---

## 🌳 Clase Destacada: `CarbonCalculator`

Funcionalidad central para compensación:
- Cálculo de absorción de CO₂ con distintas especies arbóreas
- Proyección de absorción a lo largo del tiempo
- Comparación de estrategias de reforestación
- Estimaciones de plazos de compensación

---

## 🧰 Sistemas de Soporte

- ⚙️ Geocodificación optimizada (con caché LRU)
- 🧾 Logging detallado con timestamps
- 🔄 Múltiples reintentos para APIs externas
- 🚀 Caché local para grafos de transporte

---

## 🧪 Requisitos Técnicos

```bash
Python >= 3.8

# Dependencias principales
geopy>=2.3.0
networkx>=3.0
osmnx>=1.6
pandas>=2.0
scikit-learn>=1.3
