 ![logo rosalia](https://github.com/user-attachments/assets/46703e17-fca7-43a5-913a-7780b1a0cf09)

# 🌿 ROSAL.IA

**Repository Of Scientific Articles on Listed Species (ROSAL.IA)**

ROSAL.IA (Repository Of Scientific Articles on Listed Species) es una herramienta que automatiza la construcción del corpus de conocimiento científico. Nace como una iniciativa orientada a facilitar el acceso y aprovechamiento del conocimiento científico relacionado con especies catalogadas en listas oficiales de conservación. Su objetivo principal es coordinar la integración de fuentes de datos públicas —como las APIs del IEPNB— con información científica (obtenida a través de las APIs de Crossreference y Semantic Scholar) además de herramientas avanzadas de deep learning (DL) para construir un corpus actualizado de literatura científica, fiable y accesible al usuario.

 Este módulo coordina la recolección, limpieza y validación de literatura científica para alimentar los sistemas NLP y de generación automática de informes del proyecto.

---

![Diagrama Mermaid Rosal ia](https://github.com/user-attachments/assets/1861ea35-70c9-4ebb-8365-b3dab973c33c)

---

## 📘 ¿Qué es ROSAL.IA?

**ROSAL.IA** *(Repository Of Scientific Articles on Listed Species)* es una iniciativa orientada a:

- 📥 Integrar APIs públicas para acceder a listados oficiales de especies catalogadas con filtros dinámicos.
- 📚 Recuperar bibliografía científica relacionada con dichas especies (CrossRef, Semantic Scholar).
- 🧠 Aplicar NLP junto a peticiones estructuradas para generar informes sintéticos, rigurosos y actualizables.
- 🏛️ Ayudar a la creación, mantenimiento y acceso al conocimiento científico.

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
