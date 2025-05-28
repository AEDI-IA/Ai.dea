# 🌿 ROSAL.IA Fetcher VM1

**Repository Of Scientific Articles on Listed Species (ROSAL.IA)**

ROSAL.IA (Repository Of Scientific Articles on Listed Species) es una herramienta que automatiza la construcción del corpus de conocimiento científico. Nace como una iniciativa orientada a facilitar el acceso y aprovechamiento del conocimiento científico relacionado con especies catalogadas en listas oficiales de conservación. Su objetivo principal es coordinar la integración de fuentes de datos públicas —como las APIs del IEPNB— con herramientas avanzadas de inteligencia artificial (IA) y deep learning (DL), para construir un corpus actualizado y fiable de literatura científica.

 Este módulo coordina la recolección, limpieza y validación de literatura científica para alimentar los sistemas NLP y de generación automática de informes del proyecto.

---

![Diagrama Mermaid Rosal ia](https://github.com/user-attachments/assets/b5879372-19b7-41bf-bd6f-727d36be7e78)

---

## 📘 ¿Qué es ROSAL.IA?

**ROSAL.IA** *(Repository Of Scientific Articles on Listed Species)* es una iniciativa orientada a:

- 📥 Integrar APIs públicas para acceder a listados oficiales de especies catalogadas (como IEPNB).
- 📚 Recuperar bibliografía científica relacionada con dichas especies (CrossRef, Semantic Scholar).
- 🧠 Aplicar IA y NLP para generar informes sintéticos, rigurosos y actualizables.
- 🏛️ Servir como infraestructura científica para entidades públicas y conservacionistas.

---

## 🧪 ¿Qué hace `ROSALIA-Fetcher_VM1.py`?

Este módulo realiza:

1. **Filtrado dinámico de especies** desde el Excel oficial del MITECO.
2. **Búsqueda automatizada de artículos científicos** relacionados (CrossRef, Semantic Scholar).
3. **Extracción y validación de abstracts**.
4. **Limpieza avanzada y filtrado lingüístico** (idioma, contenido, duplicados).
5. **Generación de corpus en `.xlsx`** listo para uso en modelos o informes.

---

## ⚙️ Tecnologías clave

- **spaCy `en_core_web_lg`** — Extracción de entidades, deduplicación y filtrado.
- **CrossRef / Semantic Scholar APIs** — Recuperación de artículos científicos.
- **IEPNB API** — Listado oficial de especies normativas.
- **CodeCarbon** — Medición de impacto ambiental del proceso.
- **Pandas + BeautifulSoup + tqdm** — Limpieza, scraping y monitoreo.

---

## ▶️ Cómo ejecutar

### 1. Instalación

```bash
pip install -r requirements.txt
