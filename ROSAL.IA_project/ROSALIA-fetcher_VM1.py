# region Librerías necesarias
import pandas as pd
import time
import requests
import logging
import threading
from datetime import datetime
from openpyxl import load_workbook
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import product
from bs4 import BeautifulSoup
from langdetect import detect, DetectorFactory
import math
import json
import re
import io
from tqdm import tqdm
from codecarbon import OfflineEmissionsTracker
# endregion
# region Configuracion General
# region Configuración general de URLs y parámetros de ejecución
CROSSREF_API = "https://api.crossref.org/works"
IEPNB_API = "https://iepnb.gob.es/api/catalogo/v_listapatronespecie_normas"
EXCEL_URL = "https://www.miteco.gob.es/content/dam/miteco/es/biodiversidad/servicios/banco-datos-naturaleza/recursos/listas/lista-patron-especies-silvestres-con-normativa.xlsx"
OUTPUT_FILE = "ROSAL_IA_VM1.xlsx"
DELAY_BETWEEN_REQUESTS = 4  # Segundos entre peticiones a la API
RETRY_BACKOFF = 30           # Tiempo de espera tras recibir código 429
MAX_RETRIES = 10             # Reintentos máximos por fallo
DetectorFactory.seed = 0  # Para resultados reproducibles con langdetect
# endregion
# region Configuración de tracker de emisiones
pue = 1.12
country_iso_code = 'ESP'
region='ESP'
cloud_provider='gcp'
cloud_region='europe-southwest1'
country_2letter_iso_code = 'ES'
measure_power_secs = 30
save_to_file=False

tracker = OfflineEmissionsTracker(
        country_iso_code=country_iso_code,
        region=region,
        cloud_provider=cloud_provider,
        cloud_region=cloud_region,
        country_2letter_iso_code=country_2letter_iso_code,
        measure_power_secs=measure_power_secs,
        pue=pue,
        save_to_file= save_to_file
        )
# endregion
# region Configuración de registro (log) a consola y archivo
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
log_filename = f"ROSALIA_FETCHER_LOG_{timestamp}.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename, mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
log = logging.info  # Alias para usar el log como si fuera print()

# Variables de control globales
completed_species = 0             # Contador de especies procesadas
lock = threading.Lock()          # Bloqueo para manejo seguro entre hilos
total_requests = 0               # Total de peticiones realizadas a Semantic Scholar

# Carga de filtros dinámicos desde Excel oficial
response = requests.get(EXCEL_URL)
response.raise_for_status()
filter_df = pd.read_excel(io.BytesIO(response.content), sheet_name=1)
# endregion
# endregion
# region configuración de filtrado 
# Extracción de columnas filtrables desde el archivo
FILTER_OPTIONS = {
    col: sorted(filter_df[col].dropna().unique().tolist())
    for col in [
        "WithoutAutorship", "kingdom", "phylum", "class", "order", "family", "genus", "subgenus",
        "specificepithet", "infraspecificepithet", "taxonRank", "ScientificNameAuthorship",
        "taxonRemarks", "Vernacular Name", "Origen", "Environment", "Grupo taxonómico",
        "ScientificName", "Nombre en normativa", "Normativa", "Categoría",
        "Observaciones población", "Ámbito normativa", "Año normativa"
    ] if col in filter_df.columns
}

# Mapeo directo de nombres de filtro y DOIs
FILTER_KEY_MAP = {key: key for key in FILTER_OPTIONS.keys()}
# endregion

# region --- FUNCIONES AUXILIARES --- #

def chunk_list(lst, chunk_size):
    """Divide una lista en sublistas de tamaño `chunk_size`."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

# Función para obtener el número de especies por filtro
def n_species_by_filter(key):
    """
    Devuelve un listado con el número de especies para cada valor único de un filtro simple.

    Args:
        key (str): Clave del filtro.

    Returns:
        list of tuples: Lista de tuplas (valor, número de especies)
    """
    results = []
    if key in FILTER_OPTIONS:
        for value in FILTER_OPTIONS[key]:
            filters = {key: f"eq.{value}"}
            species = fetch_species_list(filters=filters)
            count = len(species)
            results.append((value, count))
    return results


# Función para analizar combinaciones de filtros
def n_species_in_n_filters(base_filter_key, base_filter_value, compare_filter_keys):
    log(f"\nAnalizando filtro compuesto '{base_filter_key}' = '{base_filter_value}'")
    filter_combos = [FILTER_OPTIONS[key] for key in compare_filter_keys if key in FILTER_OPTIONS]
    results = []

    for values in product(*filter_combos):
        filters = {base_filter_key: f"eq.{base_filter_value}"}
        filters.update({k: f"eq.{v}" for k, v in zip(compare_filter_keys, values)})
        species = fetch_species_list(filters=filters)
        count = len(species)
        if count > 0:
            combo_desc = ", ".join(f"{k}={v}" for k, v in zip(compare_filter_keys, values))
            results.append((combo_desc, count))

    if results:
        log("\nFiltro combinado:")
        for combo, count in sorted(results, key=lambda x: -x[1]):
            log(f"- {combo}: {count} especies")
    else:
        log("No hay especies encontradas con esta combinación de filtros.")

    return results

# Función para obtener el abstract de un artículo utilizando la API de Semantic Scholar
def fetch_abstract_from_semantic_scholar(doi, title):
    """
    Intenta obtener el abstract de un artículo utilizando la API de Semantic Scholar.

    Args:
        doi (str): DOI del artículo.
        title (str): Título del artículo.

    Returns:
        str or None: El abstract si se encuentra, de lo contrario None.
    """
    api_url = "https://api.semanticscholar.org/graph/v1/paper/search?query="

    if doi:
        query = f"DOI:{doi}"
    elif title:
        query = title
    else:
        return None

    response = requests.get(f"{api_url}{query}&fields=abstract")
    if response.status_code == 200:
        data = response.json().get("data", [])
        if data and "abstract" in data[0]:
            return data[0]["abstract"]

    return None

# Función para obtener los metadatos de un artículo utilizando su DOI
def fetch_article_by_doi(doi, species_name, use_web_abstract=True):
    """
    Obtiene los metadatos de un artículo utilizando su DOI desde la API de CrossRef.

    Args:
        doi (str): Identificador DOI del artículo.
        species_name (str): Nombre de la especie científica asociada al artículo.
        use_web_abstract (bool): Indica si debe intentar obtener el abstract desde la web del artículo si no está presente.

    Returns:
        dict or None: Un diccionario con los metadatos del artículo si se recupera correctamente, de lo contrario None.
    """
    url = f"{CROSSREF_API}/{doi}"
    retries = 0

    while retries < MAX_RETRIES:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                item = response.json().get("message", {})
                abstract = item.get("abstract", "")

                # Solo intentamos obtener abstract de la web si se permite
                if not abstract and item.get("URL") and use_web_abstract:
                    abstract = fetch_abstract_from_web(item.get("URL"))

                return {
                    "scientific name": species_name,
                    "title": item.get("title", [""])[0],
                    "year": extract_year(item),
                    "authors": format_authors(item.get("author", [])),
                    "abstract": abstract,
                    "url": item.get("URL", ""),
                    "DOI": doi
                }

            elif response.status_code == 429:
                time.sleep(RETRY_BACKOFF)
                retries += 1
            else:
                retries += 1
                time.sleep(DELAY_BETWEEN_REQUESTS)
        except Exception as e:
            log(f"⚠️ Error al obtener metadatos por DOI {doi}: {str(e)}")
            retries += 1

    return None

# Función para obtener el abstract desde la web del artículo
def fetch_abstract_from_web(url):
    """
    Intenta obtener el abstract de un artículo directamente desde su página web.

    Args:
        url (str): URL del artículo.

    Returns:
        str: El texto del abstract si se encuentra, de lo contrario una cadena vacía.
    """
    try:
        response = requests.get(url, timeout=120, allow_redirects=True)
        response.raise_for_status()
        final_url = response.url  # URL final después de redirecciones
        soup = BeautifulSoup(response.content, "html.parser")

        # Verificar si es un artículo de ScienceDirect
        if "sciencedirect.com" in final_url:
            abstract_section = soup.find("div", class_="abstract author")
            if abstract_section:
                abstract_text = abstract_section.get_text(strip=True, separator=" ")
                if abstract_text:
                    log(f"✅ Abstract obtenido desde ScienceDirect para: {final_url}")
                    return abstract_text

        # Verificar si es un artículo de TandFOnline
        if "tandfonline.com" in final_url:
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, list):
                        for entry in data:
                            if entry.get("@type") == "ScholarlyArticle" and "abstract" in entry:
                                abstract_text = entry["abstract"].strip()
                                log(f"✅ Abstract obtenido desde TandFOnline para: {final_url}")
                                return abstract_text
                except json.JSONDecodeError:
                    continue

        # Procedimiento general para otros sitios
        abstract_keywords = ["abstract", "resumen", "summary"]
        possible_titles = soup.find_all(['h2', 'h3', 'strong', 'span', 'div'], string=True)

        for title in possible_titles:
            text_title = title.get_text(strip=True).lower()
            if any(keyword in text_title for keyword in abstract_keywords):
                next_elem = title.find_next_sibling()
                if next_elem and 50 < len(next_elem.get_text(strip=True)) < 2000:
                    log(f"✅ Abstract obtenido desde la web para: {final_url}")
                    return next_elem.get_text(strip=True)

        possible_abstracts = soup.find_all(['p', 'div'], string=True)
        for elem in possible_abstracts:
            text = elem.get_text(strip=True)
            if any(keyword in text.lower() for keyword in abstract_keywords) or (50 < len(text) < 2000):
                log(f"✅ Abstract obtenido desde la web para: {final_url}")
                return text

    except Exception as e:
        log(f"⚠️ No se pudo obtener el abstract de {url}: {str(e)}")

    return ""

# Validar que el artículo pertenece a la especie correcta o al género (con opción de abreviatura en paso 3)
def validate_species(article, species_name, genus=None, allow_abbreviation=False):
    """
    Valida si un artículo está relacionado con una especie específica.

    Args:
        article (dict): Diccionario con los metadatos del artículo.
        species_name (str): Nombre completo de la especie científica a validar.
        genus (str, opcional): Género de la especie para validación adicional.
        allow_abbreviation (bool): Indica si se permiten abreviaturas para la validación.

    Returns:
        bool: True si el artículo está relacionado con la especie, False en caso contrario.
    """
    full_name = species_name.lower()
    text_fields = (article.get("title", "") + " " + article.get("abstract", "")).lower()

    if full_name in text_fields:
        return True

    if allow_abbreviation:
        abbrev_1 = f"{species_name.split()[0][0]}. {species_name.split()[1]}".lower()
        abbrev_2 = f"{species_name.split()[0][0]}.{species_name.split()[1]}".lower()
        if abbrev_1 in text_fields or abbrev_2 in text_fields:
            return True

    if genus and genus.lower() in text_fields:
        return True

    return False

# Extraer el año del artículo
def extract_year(item):
    """
    Extrae el año de publicación de un artículo desde su estructura de metadatos.

    Args:
        item (dict): Diccionario de metadatos del artículo (CrossRef).

    Returns:
        int or None: El año de publicación si se encuentra, de lo contrario None.
    """
    try:
        if "published-online" in item:
            return item["published-online"]["date-parts"][0][0]
        if "published-print" in item:
            return item["published-print"]["date-parts"][0][0]
        if "issued" in item:
            return item["issued"]["date-parts"][0][0]
    except:
        return None

# Formatear autores
def format_authors(authors_list):
    """
    Formatea la lista de autores de un artículo en una cadena de texto legible.

    Args:
        authors_list (list): Lista de diccionarios con los datos de los autores.

    Returns:
        str: Cadena de texto con los nombres de los autores, separados por comas.
    """
    if not authors_list:
        return "Desconocido"
    return ", ".join([f"{a.get('given', '')} {a.get('family', '')}".strip() for a in authors_list])

# Detectar idioma
def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

def extract_english_block(text, min_non_en_block=30):
    # Divide el texto en frases o párrafos
    blocks = re.split(r'(?<=[.!?])\s+|\n+', text)
    english_blocks = []
    for block in blocks:
        block = block.strip()
        if len(block) == 0:
            continue
        try:
            lang = detect(block)
        except:
            lang = "unknown"
        # Si el bloque es inglés, lo guardamos
        if lang == "en":
            english_blocks.append(block)
        # Si el bloque NO es inglés y es corto, también lo guardamos (por si es un nombre científico, etc.)
        elif len(block) < min_non_en_block:
            english_blocks.append(block)
    # Si hay bloques en inglés (o cortos no ingleses), los unimos y devolvemos solo eso
    if english_blocks:
        return " ".join(english_blocks)
    # Si no hay bloques válidos, devolvemos vacío
    return ""

# endregion

# region --- FUNCIONES PRINCIPALES --- #

# Función para imprimir ayuda de filtros
def help_filters(key=None, value=None, num_filters=1):
    """
    Proporciona ayuda sobre los filtros disponibles y sus valores posibles para la API.

    Args:
        key (str or list, opcional): Clave del filtro o lista de claves para combinaciones.
        value (str, opcional): Valor del filtro base para mostrar combinaciones o ejemplo de uso.
        num_filters (int): Número de filtros a combinar. Por defecto 1 (individual).

    Flujo:
        - Sin clave: lista todas las claves de filtro disponibles.
        - Con clave y num_filters=1: muestra valores posibles con número de especies.
        - Con clave y valor: muestra ejemplo de uso (y combinaciones si es lista con num_filters > 1).

    Ejemplos:
        help_filters()  # Lista todas las claves de filtro.
        help_filters("Categoría")  # Muestra valores y especies para "Categoría".
        help_filters("Categoría", "Anexo II. Lista de especies en peligro o amenazadas")
        help_filters(["Categoría", "Grupo taxonómico"], value="Anexo II. Lista de especies en peligro o amenazadas", num_filters=2)

    Returns:
        None
    """
    # Caso 1: sin argumentos → mostrar claves
    if key is None:
        log("🔑 Claves de filtro disponibles:")
        for k in FILTER_OPTIONS:
            log(f"- {k}")
        return

    # Caso 2: combinación de filtros, requiere value del primer filtro
    if isinstance(key, list) and num_filters > 1:
        if len(key) != num_filters:
            log(f"⚠️ Debes proporcionar exactamente {num_filters} claves para combinaciones.")
            return
        if not value:
            log("ℹ️ Para combinaciones, proporciona el valor base del primer filtro.")
            log(f"Ejemplo: help_filters({key}, value=\"valor_base\", num_filters={num_filters})")
            return
        base_key = key[0]
        log(f"\n🔍 Combinaciones para {base_key} = '{value}':")
        combos = n_species_in_n_filters(base_key, value, key[1:])
        for desc, count in combos:
            log(f"   ↪ {desc} → {count} especies")
        return

    # Caso 3: filtro simple, mostrar valores y número de especies
    if isinstance(key, str) and key in FILTER_OPTIONS:
        if value is None:
            log(f"\n🎯 Valores posibles para '{key}' con número de especies:")
            values_with_counts = n_species_by_filter(key)
            for v, count in values_with_counts:
                log(f"- {v} → {count} especies")
            return
        else:
            log("📘 Ejemplo de uso con ese filtro:")
            log(f"filters = {{\"{key}\": \"eq.{value}\"}}")
            return

    log("⚠️ Clave(s) de filtro no válida(s). Usa help_filters() para ver las disponibles.")

# Función para establecer la lista de especies filtradas
def fetch_species_list(limit=1000, offset=0, filters=None):
    """
    Obtiene una lista de especies desde la API de IEPNB, aplicando filtros opcionales.

    Args:
        limit (int, opcional): Número máximo de especies a recuperar por solicitud (paginación).
        offset (int, opcional): Desplazamiento inicial para la paginación.
        filters (dict, opcional): Diccionario de filtros para refinar la búsqueda. 
            Las claves deben coincidir con las definidas en FILTER_KEY_MAP o en la API directamente.
            Para mayor rapidez en la creación y uso de filtros usar help_filters().
            Se pueden combinar múltiples filtros en un solo diccionario.

    Flujo:
        - Realiza solicitudes paginadas a la API de IEPNB hasta que no haya más datos.
        - Aplica filtros opcionales a cada solicitud para refinar los resultados.
        - Registra las URLs de las solicitudes para diagnóstico y depuración.
        - Si se encuentra un error en la respuesta de la API, se detiene el proceso.
        - Acumula todas las especies recuperadas en una lista.

    Returns:
        list: Lista de especies obtenidas desde la API de IEPNB.
    """
    log("Descargando lista de especies desde la API IEPNB...")
    species_list = []
    while True:
        params = {"limit": limit, "offset": offset}
        if filters:
            for k, v in filters.items():
                actual_key = FILTER_KEY_MAP.get(k, k)
                params[actual_key] = v
        response = requests.get(IEPNB_API, params=params)
        log("URL de la petición: " + response.url)
        if response.status_code != 200:
            log(f"Error en la descarga: {response.status_code}")
            break
        data = response.json()
        if not data:
            break
        species_list.extend(data)
        offset += limit
    log(f"Total de especies recuperadas: {len(species_list)}")
    return species_list

# Función para buscar artículos científicos para una especie específica
def fetcher_cf(species_name, n_species):
    """
    Obtiene artículos científicos para una especie específica desde la API de CrossRef.

    Args:
        species_name (str): Nombre de la especie científica.
        n_species (int): Número total de especies a procesar, para ajustar el límite de búsqueda.

    Returns:
        list: Lista de artículos recuperados desde CrossRef.
    """
    total_available_rows = 9900
    rows_per_species = total_available_rows // n_species
    if rows_per_species > 350:
        rows_per_species = 350
    log(f"🔍 Buscando artículos para la especie: {species_name}... | Máx. artículos: {rows_per_species}")

    genus = species_name.split()[0]
    query_url = (
        f"{CROSSREF_API}?query.bibliographic=\"{genus}\""
        f"&filter=type:journal-article&rows={rows_per_species}&sort=issued&order=desc&select=DOI"
    )

    response = requests.get(query_url)
    response.raise_for_status()
    data = response.json().get("message", {}).get("items", [])

    log(f"🔍 Artículos recuperados de Crossref: {len(data)} para la especie {species_name}.")
    return data

# Función para procesar los artículos obtenidos
def fetcher_processor(data, species_name):
    """
    Procesa una lista de artículos obtenidos, verificando su abstract y clasificándolos.

    Args:
        data (list): Lista de artículos obtenidos desde la API.
        species_name (str): Nombre de la especie científica.

    Returns:
        list: Lista de artículos procesados con información sobre abstract y criterio.
    """
    articles = []
    processed_dois = set()

    for item in data:
        doi = item.get("DOI")
        if doi not in processed_dois:
            processed_dois.add(doi)
            article = fetch_article_by_doi(doi, species_name, use_web_abstract=True)

            if article:
                if not article.get("abstract") and article.get("url"):
                    abstract = fetch_abstract_from_web(article.get("url"))
                    if not abstract:
                        abstract = fetch_abstract_from_semantic_scholar(doi, article.get("title"))

                    if abstract:
                        article["abstract"] = abstract

                article["abs_pres"] = 1 if article.get("abstract") else 0

                if validate_species(article, species_name, allow_abbreviation=True):
                    article["criterio"] = "Exacto"
                else:
                    article["criterio"] = "Genus"

                articles.append(article)

    log(f"🔎 Completado: {species_name} | Artículos procesados: {len(articles)}")
    return articles

# Función para buscar y procesar artículos en paralelo
def fetcher_pipe(species_name, n_species):
    """
    Combina la obtención y procesamiento de artículos científicos para una especie.

    Args:
        species_name (str): Nombre de la especie científica.
        n_species (int): Número total de especies a procesar.

    Returns:
        list: Lista de artículos procesados con información sobre abstract y criterio.
    """
    data = fetcher_cf(species_name, n_species)
    articles = fetcher_processor(data, species_name)
    return articles

# Función para limpiar los abstracts
def abstract_cleaning(df):
    """
    Limpia y mejora los abstracts de un DataFrame de artículos.

    Args:
        df (pd.DataFrame): DataFrame que contiene los artículos y sus abstracts.

    Returns:
        pd.DataFrame: DataFrame con los abstracts mejorados y la columna abs_pres ajustada.
    """
    log(f"Mejorando output de abstracts...")

    # Limpiar etiquetas HTML, saltos de línea y símbolos matemáticos al inicio en abstracts (pueden tener contenido matemático luego)
    df['abstract'] = df['abstract'].fillna("").apply(lambda x: re.sub(r'^[-=+*/%<>^&|]+', '', re.sub(r'<.*?>|\n|\r', ' ', x)).strip())

    # Verificar si el abstract es similar al título y eliminarlo, el abstract no puede ser lo mismo que el título. Lo hacemos antes de otras limpiezas para facilitar la detección exacta
    df['abstract'] = df.apply(lambda row: "" if row['title'].strip().lower() in row['abstract'].lower() and len(row['abstract']) <= len(row['title']) + 20 else row['abstract'], axis=1)
    
    # Eliminar la palabra "abstract" en cualquier variación de mayúsculas/minúsculas
    df['abstract'] = df['abstract'].str.replace(r'abstract', '', case=False, regex=True)

    # Eliminar "summary" o "summary:" si es la primera palabra del abstract en cualquier variación de mayúsculas/minúsculas
    df['abstract'] = df['abstract'].str.replace(r'^(summary:?)(\s+)', '', case=False, regex=True)

    # Eliminar "article" o "article:" si es la primera palabra del abstract en cualquier variación de mayúsculas/minúsculas
    df['abstract'] = df['abstract'].str.replace(r'^(article:?)(\s+)', '', case=False, regex=True)

    # Eliminar espacios duplicados
    df['abstract'] = df['abstract'].str.replace(r'\s{2,}', ' ', regex=True).str.strip()
   
    # Vaciar abstract si no está en inglés. Puede que haya abstracts en otros idiomas, pero generamente están mezclados con otros idiomas y/o con otros abstracts, siendo esta parte con otros abstract dañina para la calidad del dato, ganamos robustez
    df['abstract'] = df['abstract'].apply(lambda x: x if x == "" or detect_language(x) == "en" else "")

    # Extraer solo el bloque en inglés si hay texto mixto. Si el inglés está mezclado con otros idiomas pero es dominante en inglés, pasa el filtro anterior (abstract en varios idiomas). Esto nos devolverá solo el bloque en inglés
    df['abstract'] = df['abstract'].apply(lambda x: extract_english_block(x) if x else x)

    # Vaciar abstract si la primera palabra de 'scientific name' no aparece en el abstract. Se perderán abstract pero se gana en calidad del dato, evitando abstracts emplazados erroneamente.
    df['abstract'] = df.apply(lambda row: row['abstract'] if row['abstract'] == "" or row['scientific name'].split()[0].lower() in row['abstract'].lower() else "",axis=1)

    # Eliminar abstracts que contienen el mensaje de compra completada o de artículos retirados
    df['abstract'] = df['abstract'].apply(lambda x: "" if "Your purchase has been completed" in x else x)

    df['abstract'] = df['abstract'].apply(lambda x: "" if "This retracts the article" in x else x)

    df['abstract'] = df.apply(lambda row: "" if re.match(r"^[\[\(\s]{0,2}retracted[\]\)\s]{0,2}", row['title'].strip(), re.IGNORECASE) else row['abstract'],axis=1)

    # Ajustar abs_pres a 0 si el abstract está vacío para facilitar procesamiento posterior
    df['abs_pres'] = df['abstract'].apply(lambda x: 0 if x == "" else 1)

    log(f"Abstracts mejorados.")
    return df

def get_fetcher_lists(filter_df):
    """
    Divide los valores únicos de 'WithoutAutorship' en 15 listas iguales para procesos paralelos.

    Args:
        filter_df (pd.DataFrame): El DataFrame filtrado leído desde el Excel.

    Returns:
        dict: Diccionario con claves Fetcher_list_VM1...VM15 y sus listas correspondientes.
    """
    unique_species = filter_df['WithoutAutorship'].dropna().unique().tolist()
    unique_species = list(map(str, unique_species))  # Asegura que todos sean strings

    num_lists = 15
    chunk_size = math.ceil(len(unique_species) / num_lists)
    species_chunks = [unique_species[i * chunk_size:(i + 1) * chunk_size] for i in range(num_lists)]

    return {f"Fetcher_list_VM{i+1}": chunk for i, chunk in enumerate(species_chunks)}

# Función para actualizar artículos de especies

def update_species_articles(filters=None):
    """
    Actualiza los artículos científicos para una lista de especies, procesándolos de manera paralela.
    5 es el límite para Crossref, ponemos max_workers=4 para ser conservadores.

    Args:
        filters (dict, opcional): Diccionario de filtros para determinar las especies a procesar.

    Flujo:
        - Recupera la lista de especies a procesar.
        - Utiliza un ThreadPoolExecutor para buscar y procesar artículos en paralelo para cada especie.
        - Clasifica los artículos en principales (con abstract válido) y auxiliares (sin abstract).
        - Almacena los artículos principales y auxiliares en archivos Excel separados.
        - Registra el tiempo total de ejecución.

    Returns:
        None
    """
    species_list = fetch_species_list(filters=filters)
    if not species_list:
        log("🚫 No se encontraron especies con los filtros dados.")
        return

    chunks = chunk_list(species_list, 28)
    total_species = len(species_list)
    all_results = []

    log(f"🧩 Total de especies: {total_species} en {len(chunks)} chunks de hasta 28.")

    overall_start_time = time.time()

    for i, chunk in enumerate(chunks, start=1):
        log(f"\n📦 Procesando chunk {i}/{len(chunks)} con {len(chunk)} especies...")

        start_time = time.time()
        chunk_results = []

        with tqdm(total=len(chunk), desc=f"Chunk {i}", unit="especies") as pbar:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(fetcher_pipe, species["WithoutAutorship"], len(chunk)): species
                    for species in chunk
                }
                for future in as_completed(futures):
                    species = futures[future]
                    articles = future.result()
                    chunk_results.extend(articles)

                    # Logging detallado
                    exact_count = sum(1 for a in articles if a['criterio'] == 'Exacto')
                    genus_count = sum(1 for a in articles if a['criterio'] == 'Genus')
                    exact_with_abstract = sum(1 for a in articles if a['criterio'] == 'Exacto' and a['abs_pres'] == 1)
                    exact_without_abstract = exact_count - exact_with_abstract
                    genus_with_abstract = sum(1 for a in articles if a['criterio'] == 'Genus' and a['abs_pres'] == 1)
                    genus_without_abstract = genus_count - genus_with_abstract

                    log(f"🔎 {species['WithoutAutorship']} | Total: {len(articles)} | "
                        f"Exacto: {exact_count} (Abs: {exact_with_abstract}/{exact_without_abstract}) | "
                        f"Genus: {genus_count} (Abs: {genus_with_abstract}/{genus_without_abstract})")

                    pbar.update(1)

        all_results.extend(chunk_results)
        elapsed = round((time.time() - start_time) / 60, 2)
        log(f"✅ Chunk {i} completado en {elapsed} min con {len(chunk_results)} artículos.")

        # Espera de 5 minutos entre chunks, excepto después del último
        if i < len(chunks):
            log("⏳ Esperando 5 minutos antes de continuar con el siguiente chunk...")
            time.sleep(300)

    if all_results:
        df = pd.DataFrame(all_results)
        df = df.sort_values(by=["scientific name", "year", "criterio"], ascending=[True, False, True])
        df = abstract_cleaning(df)
        df.to_excel(OUTPUT_FILE, index=False)

        # Guardar metadatos
        wb = load_workbook(OUTPUT_FILE)
        wb.properties.keywords = f"Filtros usados: {filters}"
        wb.save(OUTPUT_FILE)
        wb.close()

        log(f"\n📁 Archivo generado: {OUTPUT_FILE}")
    else:
        log("\n🚫 No se encontraron artículos nuevos.")

    total_time = round((time.time() - overall_start_time) / 60, 2)
    log(f"\n⏱️ Tiempo total de ejecución: {total_time} minutos")

# endregion

# Punto de entrada principal
if __name__ == "__main__":
    tracker.start()
    fetcher_lists = get_fetcher_lists(filter_df)
    update_species_articles(filters={"WithoutAutorship": fetcher_lists["Fetcher_list_VM1"]})
    emissions = tracker.stop()
    log(f"\n💨 Emisiones totales: {emissions} kg CO₂eq")
    log("✅ Proceso completado.")
