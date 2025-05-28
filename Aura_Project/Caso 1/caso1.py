# -*- coding: utf-8 -*-

"""
SCRIPT 1: DISTANCIAS
"""

from itertools import combinations
from functools import lru_cache
from geopy.distance import geodesic
import networkx as nx
import pandas as pd
import osmnx as ox
from datetime import datetime
import logging
from pathlib import Path
import pickle
import mlcroissant as mlc
import requests
from time import sleep
from tenacity import retry, stop_after_attempt, wait_exponential
# Configuración de logging
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
log_filename = f"AURA_CASO1_TEST_LOG_{timestamp}.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename, mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
log = logging.info  # Alias para usar el log como si fuera print()

# ── Ajustes globales OSMnx ───────────────────────────────────
ox.settings.overpass_settings = '[out:json][timeout:600]'     # 10 min
ox.settings.overpass_endpoint = 'https://overpass.kumi.systems/api/interpreter'
ox.settings.max_query_area_size = 2e7     # 20.000 km² – evita troceos excesivos
ox.settings.use_cache = True              # guarda la respuesta en disco ~/.cache
ox.settings.log_console = True            # ver logs en pantalla

OVERPASS_ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]

# Throttling interno de OSMnx
ox.settings.rate_limit    = True   # respeta 'retry-after'
ox.settings.retry_count   = 3
ox.settings.retry_sleep   = 60     # segundos



@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=10, min=10, max=120))
def _download_graph(place, network_type="drive", cf=None):
    return ox.graph_from_place(place, network_type=network_type, custom_filter=cf)

def _build_spain_drive_graph() -> nx.MultiDiGraph:
    for ep in OVERPASS_ENDPOINTS:
        ox.settings.overpass_endpoint = ep
        log(f"→ intentando {ep}")
        try:
            return _download_graph("Spain", network_type="drive")
        except Exception as e:
            log(f"   ✗  {ep} falló: {e}")
    raise RuntimeError("Todos los endpoints Overpass fallaron para el grafo 'drive'")



#---------------- 1) LISTAS DE CIUDADES Y PAISES----------------
 # Aeropuertos
# ── Peninsulares e insulares ─────────────────────────────────────────

PENINSULAR_SPANISH_CITIES = {'Madrid, Spain': ['LEMD', 'NaN'], 'Barcelona, Spain': ['LEBL', 'LERS'], 'Valencia, Spain': ['LEVC', 'NaN'], 'Sevilla, Spain': ['LEZL', 'NaN'], 'Zaragoza, Spain': ['LEZG', 'NaN'], 
'Malaga, Spain': ['LEMG', 'NaN'], 'Murcia, Spain': ['LEMI', 'NaN'], 'Alicante, Spain': ['LEAL', 'NaN'], 'Bilbao, Spain': ['LEBB', 'NaN'], 'Cordoba, Spain': ['NaN', 'NaN'], 
'Valladolid, Spain': ['LEVD', 'NaN'], 'Vigo, Spain': ['LEVX', 'NaN'], "L'Hospitalet de Llobregat, Spain": ['LEBL', 'LERS'], 'Gijon, Spain': ['LEAS', 'NaN'], 
'Vitoria-Gasteiz, Spain': ['LEVT', 'NaN'], 'A Coruna, Spain': ['LECO', 'NaN'], 'Elche, Spain': ['LEAL', 'NaN'], 'Granada, Spain': ['LEGR', 'NaN'], 'Terrassa, Spain': ['LEBL', 'LERS'], 
'Badalona, Spain': ['LEBL', 'LERS'], 'Sabadell, Spain': ['LEBL', 'LERS'], 'Oviedo, Spain': ['LEAS', 'NaN'], 'Cartagena, Spain': ['LEMI', 'NaN'], 'Mostoles, Spain': ['LEMD', 'NaN'], 
'Jerez de la Frontera, Spain': ['LEJR', 'NaN'], 'Pamplona, Spain': ['LEPP', 'NaN'], 'Almeria, Spain': ['LEAM', 'NaN'], 'Alcala de Henares, Spain': ['LEMD', 'NaN'], 
'Leganes, Spain': ['LEMD', 'NaN'], 'Fuenlabrada, Spain': ['LEMD', 'NaN'], 'Getafe, Spain': ['LEMD', 'NaN'], 'San Sebastian, Spain': ['LESO', 'NaN'], 
'Castellon de la Plana, Spain': ['LECH', 'NaN'], 'Burgos, Spain': ['LEBG', 'NaN'], 'Albacete, Spain': ['LEAB', 'NaN'], 'Santander, Spain': ['LEXJ', 'NaN'], 
'Alcorcon, Spain': ['LEMD', 'NaN'], 'Marbella, Spain': ['LEMG', 'NaN'], 'Logrono, Spain': ['LELO', 'NaN'], 'Badajoz, Spain': ['LEBZ', 'NaN'], 'Salamanca, Spain': ['LESA', 'NaN'], 
'Lleida, Spain': ['LEDA', 'NaN'], 'Huelva, Spain': ['NaN', 'NaN'], 'Tarragona, Spain': ['LERS', 'NaN'], 'Torrejon de Ardoz, Spain': ['LEMD', 'NaN'], 'Dos Hermanas, Spain': ['LEZL', 'NaN'], 
'Parla, Spain': ['LEMD', 'NaN'], 'Mataro, Spain': ['LEBL', 'LERS'], 'Algeciras, Spain': ['NaN', 'NaN'], 'Leon, Spain': ['LELN', 'NaN'], 'Alcobendas, Spain': ['LEMD', 'NaN'], 
'Santa Coloma de Gramenet, Spain': ['LEBL', 'LERS'], 'Jaen, Spain': ['LEGR', 'NaN'], 'Cadiz, Spain': ['LEJR', 'NaN'], 'Reus, Spain': ['LERS', 'NaN'], 'Roquetas de Mar, Spain': ['LEAM', 'NaN'], 
'Girona, Spain': ['LEGE', 'NaN'], 'Ourense, Spain': ['NaN', 'NaN'], 'Barakaldo, Spain': ['LEBB', 'NaN'], 'Rivas-Vaciamadrid, Spain': ['LEMD', 'NaN'], 
'Santiago de Compostela, Spain': ['LEST', 'NaN'], 'Lugo, Spain': ['NaN', 'NaN'], 'Sant Cugat del Valles, Spain': ['LEBL', 'LERS'], 'Las Rozas de Madrid, Spain': ['LEMD', 'NaN'], 
'Lorca, Spain': ['LEMI', 'NaN'], 'Caceres, Spain': ['NaN', 'NaN'], 'San Sebastian de los Reyes, Spain': ['LEMD', 'NaN'], 'Torrevieja, Spain': ['LEAL', 'NaN'], 
'San Fernando, Spain': ['LEJR', 'NaN'], 'Mijas, Spain': ['LEMG', 'NaN'], 'Cornella de Llobregat, Spain': ['LEBL', 'LERS'], 'Guadalajara, Spain': ['LEMD', 'NaN'], 
'El Ejido, Spain': ['LEAM', 'NaN'], 'El Puerto de Santa Maria, Spain': ['LEJR', 'NaN'], 'Chiclana de la Frontera, Spain': ['LEJR', 'NaN'], 'Torrent, Spain': ['LEVC', 'NaN'], 
'Pozuelo de Alarcon, Spain': ['LEMD', 'NaN'], 'Toledo, Spain': ['LEMD', 'NaN'], 'Velez-Malaga, Spain': ['LEMG', 'NaN'], 'Fuengirola, Spain': ['LEMG', 'NaN'], 
'Sant Boi de Llobregat, Spain': ['LEBL', 'LERS'], 'Talavera de la Reina, Spain': ['LEMD', 'NaN'], 'Orihuela, Spain': ['LEAL', 'NaN'], 'Valdemoro, Spain': ['LEMD', 'NaN'], 
'Pontevedra, Spain': ['LEVX', 'NaN'], 'Rubi, Spain': ['LEBL', 'LERS'], 'Coslada, Spain': ['LEMD', 'NaN'], 'Manresa, Spain': ['LEBL', 'LERS'], 'Gandia, Spain': ['LEVC', 'NaN'], 
'Estepona, Spain': ['LEMG', 'NaN'], 'Benalmadena, Spain': ['LEMG', 'NaN'], 'Molina de Segura, Spain': ['LEMI', 'NaN'], 'Alcala de Guadaira, Spain': ['LEZL', 'NaN'], 
'Palencia, Spain': ['LEVD', 'NaN'], 'Getxo, Spain': ['LEBB', 'NaN'], 'Ciudad Real, Spain': ['LERL', 'NaN'], 'Aviles, Spain': ['LEAS', 'NaN'], 'Paterna, Spain': ['LEVC', 'NaN'], 
'Benidorm, Spain': ['LEAL', 'NaN'], 'Majadahonda, Spain': ['LEMD', 'NaN'], 'Sagunto, Spain': ['LEVC', 'NaN'], 'Torremolinos, Spain': ['LEMG', 'NaN'], 'Vilanova i la Geltru, Spain': ['LEBL', 'LERS'], 
'Sanlucar de Barrameda, Spain': ['LEJR', 'NaN'], 'Castelldefels, Spain': ['LEBL', 'LERS'], 'Viladecans, Spain': ['LEBL', 'LERS'], 'Collado Villalba, Spain': ['LEMD', 'NaN'], 
'El Prat de Llobregat, Spain': ['LEBL', 'LERS'], 'Boadilla del Monte, Spain': ['LEMD', 'NaN'], 'Ferrol, Spain': ['LECO', 'NaN'], 'Granollers, Spain': ['LEBL', 'LERS'], 
'La Linea de la Concepcion, Spain': ['LEJR', 'NaN'], 'Irun, Spain': ['LESO', 'NaN'], 'Ponferrada, Spain': ['LELN', 'NaN'], 'Aranjuez, Spain': ['LEMD', 'NaN'], 'Alcoy, Spain': ['LEAL', 'NaN'], 
'San Vicente del Raspeig, Spain': ['LEAL', 'NaN'], 'Merida, Spain': ['LEBZ', 'NaN'], 'Motril, Spain': ['LEGR', 'NaN'], 'Arganda del Rey, Spain': ['LEMD', 'NaN'], 'Zamora, Spain': ['LEVD', 'NaN'], 
'Avila, Spain': ['LEMD', 'NaN'], 'Cerdanyola del Valles, Spain': ['LEBL', 'LERS'], 'Colmenar Viejo, Spain': ['LEMD', 'NaN'], 'Pinto, Spain': ['LEMD', 'NaN'], 'Linares, Spain': ['LEGR', 'NaN'], 
'Huesca, Spain': ['LEHC', 'NaN'], 'Elda, Spain': ['LEAL', 'NaN'], 'Cuenca, Spain': ['LEMD', 'NaN'], 'Tres Cantos, Spain': ['LEMD', 'NaN'], 'Siero, Spain': ['LEAS', 'NaN'], 'Vila-real, Spain': ['LEVC', 'NaN'], 
'Mollet del Valles, Spain': ['LEBL', 'LERS'], 'Rincon de la Victoria, Spain': ['LEMG', 'NaN'], 'Utrera, Spain': ['LEZL', 'NaN'], 'Torrelavega, Spain': ['LEXJ', 'NaN'], 'Segovia, Spain': ['LEMD', 'NaN'], 
'Vic, Spain': ['LEBL', 'LERS'], 'Figueres, Spain': ['LEGE', 'NaN'], 'Gava, Spain': ['LEBL', 'LERS'], 'Mairena del Aljarafe, Spain': ['LEZL', 'NaN'], 'Esplugues de Llobregat, Spain': ['LEBL', 'LERS'], 
'Alzira, Spain': ['LEVC', 'NaN'], 'Denia, Spain': ['LEAL', 'NaN'], 'Sant Feliu de Llobregat, Spain': ['LEBL', 'LERS'], 'Santurtzi, Spain': ['LEBB', 'NaN'], 'Mislata, Spain': ['LEVC', 'NaN'], 
'Puertollano, Spain': ['LERL', 'NaN'], 'Portugalete, Spain': ['LEBB', 'NaN'], 'Alhaurin de la Torre, Spain': ['LEMG', 'NaN'], 'Alcantarilla, Spain': ['LEMI', 'NaN'], 'Lucena, Spain': ['NaN', 'NaN'], 
'Lloret de Mar, Spain': ['LEBL', 'LERS'], 'Blanes, Spain': ['LEBL', 'LERS'], 'Puerto Real, Spain': ['LEJR', 'NaN'], 'Antequera, Spain': ['LEMG', 'NaN'], 'Vilafranca del Penedes, Spain': ['LEBL', 'LERS'], 
'Igualada, Spain': ['LEBL', 'LERS'], 'Soria, Spain': ['NaN', 'NaN'], 'Burjassot, Spain': ['LEVC', 'NaN'], 'La Rinconada, Spain': ['LEZL', 'NaN'], 'El Vendrell, Spain': ['LERS', 'NaN'], 
'Basauri, Spain': ['LEBB', 'NaN'], 'Torre-Pacheco, Spain': ['LEMI', 'NaN'], 'Plasencia, Spain': ['LEBZ', 'NaN'], 'Ecija, Spain': ['LEZL', 'NaN'], 'Ripollet, Spain': ['LEBL', 'LERS'], 
'Errenteria, Spain': ['LESO', 'NaN'], 'Naron, Spain': ['LECO', 'NaN'], 'San Fernando de Henares, Spain': ['LEMD', 'NaN'], 'Olot, Spain': ['LEGE', 'NaN'], 'Los Palacios y Villafranca, Spain': ['LEZL', 'NaN'], 
'Tudela, Spain': ['LEPP', 'NaN'], 'Santa Pola, Spain': ['LEAL', 'NaN'], 'Sant Adria de Besos, Spain': ['LEBL', 'LERS'], 'Oleiros, Spain': ['LECO', 'NaN'], 'Langreo, Spain': ['LEAS', 'NaN'], 
'Vilagarcia de Arousa, Spain': ['LEVX', 'NaN'], 'Don Benito, Spain': ['LEBZ', 'NaN'], 'Aguilas, Spain': ['LEMI', 'NaN'], 'Arroyomolinos, Spain': ['LEMD', 'NaN'], 'Montcada i Reixac, Spain': ['LEBL', 'LERS'], 
'Burriana, Spain': ['LECH', 'NaN'], 'Villajoyosa, Spain': ['LEAL', 'NaN'], 'Cambrils, Spain': ['LERS', 'NaN'], 'Teruel, Spain': ['NaN', 'NaN'], 'Tomelloso, Spain': ['NaN', 'NaN'], 
'Ontinyent, Spain': ['NaN', 'NaN'], 'Galapagar, Spain': ['NaN', 'NaN'], 'Mieres, Spain': ['NaN', 'NaN'], 'Miranda de Ebro, Spain': ['NaN', 'NaN'], 'Yecla, Spain': ['LEMI', 'NaN'], 
'Azuqueca de Henares, Spain': ['NaN', 'NaN'], 'San Javier, Spain': ['LEMI', 'NaN'], 'Andujar, Spain': ['LEGR', 'NaN'], 'Cieza, Spain': ['LEMI', 'NaN'], 'Tortosa, Spain': ['LERS', 'NaN'], 
'Mazarron, Spain': ['LEMI', 'NaN'], 'Sant Joan Despi, Spain': ['NaN', 'NaN'], 'Villena, Spain': ['NaN', 'NaN'], 'Almendralejo, Spain': ['NaN', 'NaN'], 'San Roque, Spain': ['LEJR', 'NaN'], 
'Petrer, Spain': ['NaN', 'NaN'], 'Arteixo, Spain': ['NaN', 'NaN'], 'Aldaia, Spain': ['NaN', 'NaN'], 'Salt, Spain': ['NaN', 'NaN'], 'Aranda de Duero, Spain': ['NaN', 'NaN'], 'Ubeda, Spain': ['NaN', 'NaN'], 
'Totana, Spain': ['NaN', 'NaN'], 'Barbera del Valles, Spain': ['NaN', 'NaN'], 'Castro-Urdiales, Spain': ['LEXJ', 'NaN'], 'Ronda, Spain': ['LEMG', 'NaN'], 'Nijar, Spain': ['LEAM', 'NaN'], 
'Ames, Spain': ['LEST', 'NaN'], 'Navalcarnero, Spain': ['LEMD', 'NaN'], 'Leioa, Spain': ['LEBB', 'NaN'], 'Sitges, Spain': ['LEBL', 'LERS'], 'Manises, Spain': ['LEVC', 'NaN'], 'Illescas, Spain': ['LEMD', 'NaN'], 
'Sant Pere de Ribes, Spain': ['LEBL', 'LERS'], 'La Vall d Uixo, Spain': ['LECH', 'NaN'], 'Calafell, Spain': ['LERS', 'NaN'], 'Xirivella, Spain': ['LEVC', 'NaN'], 'Carballo, Spain': ['LECO', 'NaN'], 
'Alcazar de San Juan, Spain': ['LERL', 'NaN'], 'Coria del Rio, Spain': ['LEZL', 'NaN'], 'Culleredo, Spain': ['LECO', 'NaN'], 'Arcos de la Frontera, Spain': ['LEJR', 'NaN'], 'Hellin, Spain': ['LEAB', 'NaN'], 
'Salou, Spain': ['LERS', 'NaN'], 'Valdepenas, Spain': ['LERL', 'NaN'], 'El Campello, Spain': ['LEAL', 'NaN'], 'Crevillent, Spain': ['LEAL', 'NaN'], 'Camargo, Spain': ['LEXJ', 'NaN'], 
'Xativa, Spain': ['LEVC', 'NaN'], 'Vinaros, Spain': ['LECH', 'NaN'], 'Sesena, Spain': ['LEMD', 'NaN'], 'Catarroja, Spain': ['LEVC', 'NaN'], 'Javea, Spain': ['LEAL', 'NaN'], 'Alaquas, Spain': ['LEVC', 'NaN'], 
'Durango, Spain': ['LEBB', 'NaN'], 'San Andres del Rabanedo, Spain': ['LELN', 'NaN'], 'Carmona, Spain': ['LEZL', 'NaN'], 'Puente Genil, Spain': ['LEGR', 'NaN'], 'Lebrija, Spain': ['LEZL', 'NaN'], 
'Benicarlo, Spain': ['LECH', 'NaN'], 'Rota, Spain': ['LEJR', 'NaN'], 'Pineda de Mar, Spain': ['LEBL', 'LERS'], 'Villaviciosa de Odon, Spain': ['LEMD', 'NaN'], 'Lepe, Spain': ['NaN', 'NaN'], 
'Redondela, Spain': ['LEVX', 'NaN'], 'Premia de Mar, Spain': ['LEBL', 'LERS'], 'Cartama, Spain': ['LEMG', 'NaN'], 'Vicar, Spain': ['LEAM', 'NaN'], 'San Pedro del Pinatar, Spain': ['LEMI', 'NaN'], 
'Camas, Spain': ['LEZL', 'NaN'], 'Sant Vicenc dels Horts, Spain': ['LEBL', 'LERS'], 'Martorell, Spain': ['LEBL', 'LERS'], 'Almassora, Spain': ['LECH', 'NaN'], 'Sueca, Spain': ['LEVC', 'NaN'], 
'Sestao, Spain': ['LEBB', 'NaN'], 'Algemesi, Spain': ['LEVC', 'NaN'], 'Mutxamel, Spain': ['LEAL', 'NaN'], 'Paiporta, Spain': ['LEVC', 'NaN'], 'Alhaurin el Grande, Spain': ['LEMG', 'NaN'], 
                             'Betera, Spain': ['LEVC', 'NaN'], 'Eibar, Spain': ['LEBB', 'NaN']}



# ── Baleares ─────────────────────────────────────────
MALLORCA = {'Palma, Spain': ['LEPA', 'NaN'], 'Calvia, Spain': ['LEPA', 'NaN'], 'Manacor, Spain': ['LEPA', 'NaN'], 'Marratxi, Spain': ['LEPA', 'NaN'], 'Llucmajor, Spain': ['LEPA', 'NaN'], 'Inca, Spain': ['LEPA', 'NaN']}


IBIZA = {'Eivissa, Spain': ['LEIB', 'NaN'], 'Santa Eularia des Riu, Spain': ['LEIB', 'NaN'], 'Sant Josep de sa Talaia, Spain': ['LEIB', 'NaN'], 'Sant Antoni de Portmany, Spain': ['LEIB', 'NaN']}


MENORCA = {'Ciutadella de Menorca, Spain': ['LEMH', 'NaN'], 'Mao, Spain': ['LEMH', 'NaN']}

GRAN_CANARIA = {'Las Palmas de Gran Canaria, Spain': ['GCLP', 'NaN'], 'Telde, Spain': ['GCLP', 'NaN'], 'Santa Lucia de Tirajana, Spain': ['GCLP', 'NaN'], 'San Bartolome de Tirajana, Spain': ['GCLP', 'NaN'], 'Arucas, Spain': ['GCLP', 'NaN'], 'Aguimes, Spain': ['GCLP', 'NaN'], 'Ingenio, Spain': ['GCLP', 'NaN']}

TENERIFE = {'Santa Cruz de Tenerife, Spain': ['GCXO', 'GCTS'], 'San Cristobal de La Laguna, Spain': ['GCXO', 'GCTS'], 'Arona, Spain': ['GCXO', 'GCTS'], 'Granadilla de Abona, Spain': ['GCXO', 'GCTS'], 'Adeje, Spain': ['GCXO', 'GCTS'], 'La Orotava, Spain': ['GCXO', 'GCTS'], 'Los Realejos, Spain': ['GCXO', 'GCTS'], 'Puerto de la Cruz, Spain': ['GCXO', 'GCTS'], 'Candelaria, Spain': ['GCXO', 'GCTS']}

LANZAROTE = {"Arrecife, Spain": ["GCRR", "NaN"]}

FUERTEVENTURA = {'Puerto del Rosario, Spain': ['GCFV', 'NaN'], 'La Oliva, Spain': ['GCFV', 'NaN']}

# ── Todas ───────────────────────────────────────────

SPANISH_CITIES = {'Madrid, Spain': ['LEMD', 'NaN'], 'Barcelona, Spain': ['LEBL', 'LERS'], 'Valencia, Spain': ['LEVC', 'NaN'], 'Sevilla, Spain': ['LEZL', 'NaN'], 'Zaragoza, Spain': ['LEZG', 'NaN'], 'Malaga, Spain': ['LEMG', 'NaN'], 'Murcia, Spain': ['LEMI', 'NaN'], 
 'Alicante, Spain': ['LEAL', 'NaN'], 'Bilbao, Spain': ['LEBB', 'NaN'], 'Cordoba, Spain': ['NaN', 'NaN'], 'Valladolid, Spain': ['LEVD', 'NaN'], 'Vigo, Spain': ['LEVX', 'NaN'], "L'Hospitalet de Llobregat, Spain": ['LEBL', 'LERS'], 
 'Gijon, Spain': ['LEAS', 'NaN'], 'Vitoria-Gasteiz, Spain': ['LEVT', 'NaN'], 'A Coruna, Spain': ['LECO', 'NaN'], 'Elche, Spain': ['LEAL', 'NaN'], 'Granada, Spain': ['LEGR', 'NaN'], 'Terrassa, Spain': ['LEBL', 'LERS'], 
 'Badalona, Spain': ['LEBL', 'LERS'], 'Sabadell, Spain': ['LEBL', 'LERS'], 'Oviedo, Spain': ['LEAS', 'NaN'], 'Cartagena, Spain': ['LEMI', 'NaN'], 'Mostoles, Spain': ['LEMD', 'NaN'], 'Jerez de la Frontera, Spain': ['LEJR', 'NaN'], 
 'Pamplona, Spain': ['LEPP', 'NaN'], 'Almeria, Spain': ['LEAM', 'NaN'], 'Alcala de Henares, Spain': ['LEMD', 'NaN'], 'Leganes, Spain': ['LEMD', 'NaN'], 'Fuenlabrada, Spain': ['LEMD', 'NaN'], 'Getafe, Spain': ['LEMD', 'NaN'], 
 'San Sebastian, Spain': ['LESO', 'NaN'], 'Castellon de la Plana, Spain': ['LECH', 'NaN'], 'Burgos, Spain': ['LEBG', 'NaN'], 'Albacete, Spain': ['LEAB', 'NaN'], 'Santander, Spain': ['LEXJ', 'NaN'], 'Alcorcon, Spain': ['LEMD', 'NaN'], 
 'Marbella, Spain': ['LEMG', 'NaN'], 'Logrono, Spain': ['LELO', 'NaN'], 'Badajoz, Spain': ['LEBZ', 'NaN'], 'Salamanca, Spain': ['LESA', 'NaN'], 'Lleida, Spain': ['LEDA', 'NaN'], 'Huelva, Spain': ['NaN', 'NaN'], 
 'Tarragona, Spain': ['LERS', 'NaN'], 'Torrejon de Ardoz, Spain': ['LEMD', 'NaN'], 'Dos Hermanas, Spain': ['LEZL', 'NaN'], 'Parla, Spain': ['LEMD', 'NaN'], 'Mataro, Spain': ['LEBL', 'LERS'], 'Algeciras, Spain': ['NaN', 'NaN'], 
 'Leon, Spain': ['LELN', 'NaN'], 'Alcobendas, Spain': ['LEMD', 'NaN'], 'Santa Coloma de Gramenet, Spain': ['LEBL', 'LERS'], 'Jaen, Spain': ['LEGR', 'NaN'], 'Cadiz, Spain': ['LEJR', 'NaN'], 'Reus, Spain': ['LERS', 'NaN'], 
 'Roquetas de Mar, Spain': ['LEAM', 'NaN'], 'Girona, Spain': ['LEGE', 'NaN'], 'Ourense, Spain': ['NaN', 'NaN'], 'Barakaldo, Spain': ['LEBB', 'NaN'], 'Rivas-Vaciamadrid, Spain': ['LEMD', 'NaN'], 'Santiago de Compostela, Spain': ['LEST', 'NaN'], 
 'Lugo, Spain': ['NaN', 'NaN'], 'Sant Cugat del Valles, Spain': ['LEBL', 'LERS'], 'Las Rozas de Madrid, Spain': ['LEMD', 'NaN'], 'Lorca, Spain': ['LEMI', 'NaN'], 'Caceres, Spain': ['NaN', 'NaN'], 'San Sebastian de los Reyes, Spain': ['LEMD', 'NaN'], 
 'Torrevieja, Spain': ['LEAL', 'NaN'], 'San Fernando, Spain': ['LEJR', 'NaN'], 'Mijas, Spain': ['LEMG', 'NaN'], 'Cornella de Llobregat, Spain': ['LEBL', 'LERS'], 'Guadalajara, Spain': ['LEMD', 'NaN'], 'El Ejido, Spain': ['LEAM', 'NaN'], 
 'El Puerto de Santa Maria, Spain': ['LEJR', 'NaN'], 'Chiclana de la Frontera, Spain': ['LEJR', 'NaN'], 'Torrent, Spain': ['LEVC', 'NaN'], 'Pozuelo de Alarcon, Spain': ['LEMD', 'NaN'], 'Toledo, Spain': ['LEMD', 'NaN'], 
 'Velez-Malaga, Spain': ['LEMG', 'NaN'], 'Fuengirola, Spain': ['LEMG', 'NaN'], 'Sant Boi de Llobregat, Spain': ['LEBL', 'LERS'], 'Talavera de la Reina, Spain': ['LEMD', 'NaN'], 'Orihuela, Spain': ['LEAL', 'NaN'], 
 'Valdemoro, Spain': ['LEMD', 'NaN'], 'Pontevedra, Spain': ['LEVX', 'NaN'], 'Rubi, Spain': ['LEBL', 'LERS'], 'Coslada, Spain': ['LEMD', 'NaN'], 'Manresa, Spain': ['LEBL', 'LERS'], 'Gandia, Spain': ['LEVC', 'NaN'], 
 'Estepona, Spain': ['LEMG', 'NaN'], 'Benalmadena, Spain': ['LEMG', 'NaN'], 'Molina de Segura, Spain': ['LEMI', 'NaN'], 'Alcala de Guadaira, Spain': ['LEZL', 'NaN'], 'Palencia, Spain': ['LEVD', 'NaN'], 'Getxo, Spain': ['LEBB', 'NaN'], 
 'Ciudad Real, Spain': ['LERL', 'NaN'], 'Aviles, Spain': ['LEAS', 'NaN'], 'Paterna, Spain': ['LEVC', 'NaN'], 'Benidorm, Spain': ['LEAL', 'NaN'], 'Majadahonda, Spain': ['LEMD', 'NaN'], 'Sagunto, Spain': ['LEVC', 'NaN'], 
 'Torremolinos, Spain': ['LEMG', 'NaN'], 'Vilanova i la Geltru, Spain': ['LEBL', 'LERS'], 'Sanlucar de Barrameda, Spain': ['LEJR', 'NaN'], 'Castelldefels, Spain': ['LEBL', 'LERS'], 'Viladecans, Spain': ['LEBL', 'LERS'], 
 'Collado Villalba, Spain': ['LEMD', 'NaN'], 'El Prat de Llobregat, Spain': ['LEBL', 'LERS'], 'Boadilla del Monte, Spain': ['LEMD', 'NaN'], 'Ferrol, Spain': ['LECO', 'NaN'], 'Granollers, Spain': ['LEBL', 'LERS'], 
 'La Linea de la Concepcion, Spain': ['LEJR', 'NaN'], 'Irun, Spain': ['LESO', 'NaN'], 'Ponferrada, Spain': ['LELN', 'NaN'], 'Aranjuez, Spain': ['LEMD', 'NaN'], 'Alcoy, Spain': ['LEAL', 'NaN'], 'San Vicente del Raspeig, Spain': ['LEAL', 'NaN'], 
 'Merida, Spain': ['LEBZ', 'NaN'], 'Motril, Spain': ['LEGR', 'NaN'], 'Arganda del Rey, Spain': ['LEMD', 'NaN'], 'Zamora, Spain': ['LEVD', 'NaN'], 'Avila, Spain': ['LEMD', 'NaN'], 'Cerdanyola del Valles, Spain': ['LEBL', 'LERS'], 
 'Colmenar Viejo, Spain': ['LEMD', 'NaN'], 'Pinto, Spain': ['LEMD', 'NaN'], 'Linares, Spain': ['LEGR', 'NaN'], 'Huesca, Spain': ['LEHC', 'NaN'], 'Elda, Spain': ['LEAL', 'NaN'], 'Cuenca, Spain': ['LEMD', 'NaN'], 
 'Tres Cantos, Spain': ['LEMD', 'NaN'], 'Siero, Spain': ['LEAS', 'NaN'], 'Vila-real, Spain': ['LEVC', 'NaN'], 'Mollet del Valles, Spain': ['LEBL', 'LERS'], 'Rincon de la Victoria, Spain': ['LEMG', 'NaN'], 'Utrera, Spain': ['LEZL', 'NaN'], 
 'Torrelavega, Spain': ['LEXJ', 'NaN'], 'Segovia, Spain': ['LEMD', 'NaN'], 'Vic, Spain': ['LEBL', 'LERS'], 'Figueres, Spain': ['LEGE', 'NaN'], 'Gava, Spain': ['LEBL', 'LERS'], 'Mairena del Aljarafe, Spain': ['LEZL', 'NaN'], 
 'Esplugues de Llobregat, Spain': ['LEBL', 'LERS'], 'Alzira, Spain': ['LEVC', 'NaN'], 'Denia, Spain': ['LEAL', 'NaN'], 'Sant Feliu de Llobregat, Spain': ['LEBL', 'LERS'], 'Santurtzi, Spain': ['LEBB', 'NaN'], 'Mislata, Spain': ['LEVC', 'NaN'], 
 'Puertollano, Spain': ['LERL', 'NaN'], 'Portugalete, Spain': ['LEBB', 'NaN'], 'Alhaurin de la Torre, Spain': ['LEMG', 'NaN'], 'Alcantarilla, Spain': ['LEMI', 'NaN'], 'Lucena, Spain': ['NaN', 'NaN'], 'Lloret de Mar, Spain': ['LEBL', 'LERS'], 
 'Blanes, Spain': ['LEBL', 'LERS'], 'Puerto Real, Spain': ['LEJR', 'NaN'], 'Antequera, Spain': ['LEMG', 'NaN'], 'Vilafranca del Penedes, Spain': ['LEBL', 'LERS'], 'Igualada, Spain': ['LEBL', 'LERS'], 'Soria, Spain': ['NaN', 'NaN'], 
 'Burjassot, Spain': ['LEVC', 'NaN'], 'La Rinconada, Spain': ['LEZL', 'NaN'], 'El Vendrell, Spain': ['LERS', 'NaN'], 'Basauri, Spain': ['LEBB', 'NaN'], 'Torre-Pacheco, Spain': ['LEMI', 'NaN'], 'Plasencia, Spain': ['LEBZ', 'NaN'], 
 'Ecija, Spain': ['LEZL', 'NaN'], 'Ripollet, Spain': ['LEBL', 'LERS'], 'Errenteria, Spain': ['LESO', 'NaN'], 'Naron, Spain': ['LECO', 'NaN'], 'San Fernando de Henares, Spain': ['LEMD', 'NaN'], 'Olot, Spain': ['LEGE', 'NaN'], 
 'Los Palacios y Villafranca, Spain': ['LEZL', 'NaN'], 'Tudela, Spain': ['LEPP', 'NaN'], 'Santa Pola, Spain': ['LEAL', 'NaN'], 'Sant Adria de Besos, Spain': ['LEBL', 'LERS'], 'Oleiros, Spain': ['LECO', 'NaN'], 'Langreo, Spain': ['LEAS', 'NaN'], 
 'Vilagarcia de Arousa, Spain': ['LEVX', 'NaN'], 'Don Benito, Spain': ['LEBZ', 'NaN'], 'Aguilas, Spain': ['LEMI', 'NaN'], 'Arroyomolinos, Spain': ['LEMD', 'NaN'], 'Montcada i Reixac, Spain': ['LEBL', 'LERS'], 'Burriana, Spain': ['LECH', 'NaN'], 
 'Villajoyosa, Spain': ['LEAL', 'NaN'], 'Cambrils, Spain': ['LERS', 'NaN'], 'Teruel, Spain': ['NaN', 'NaN'], 'Tomelloso, Spain': ['NaN', 'NaN'], 'Ontinyent, Spain': ['NaN', 'NaN'], 'Galapagar, Spain': ['NaN', 'NaN'], 
 'Mieres, Spain': ['NaN', 'NaN'], 'Miranda de Ebro, Spain': ['NaN', 'NaN'], 'Yecla, Spain': ['LEMI', 'NaN'], 'Azuqueca de Henares, Spain': ['NaN', 'NaN'], 'San Javier, Spain': ['LEMI', 'NaN'], 'Andujar, Spain': ['LEGR', 'NaN'], 
 'Cieza, Spain': ['LEMI', 'NaN'], 'Tortosa, Spain': ['LERS', 'NaN'], 'Mazarron, Spain': ['LEMI', 'NaN'], 'Sant Joan Despi, Spain': ['NaN', 'NaN'], 'Villena, Spain': ['NaN', 'NaN'], 'Almendralejo, Spain': ['NaN', 'NaN'], 
 'San Roque, Spain': ['LEJR', 'NaN'], 'Petrer, Spain': ['NaN', 'NaN'], 'Arteixo, Spain': ['NaN', 'NaN'], 'Aldaia, Spain': ['NaN', 'NaN'], 'Salt, Spain': ['NaN', 'NaN'], 'Aranda de Duero, Spain': ['NaN', 'NaN'], 'Ubeda, Spain': ['NaN', 'NaN'], 
 'Totana, Spain': ['NaN', 'NaN'], 'Barbera del Valles, Spain': ['NaN', 'NaN'], 'Castro-Urdiales, Spain': ['LEXJ', 'NaN'], 'Ronda, Spain': ['LEMG', 'NaN'], 'Nijar, Spain': ['LEAM', 'NaN'], 'Ames, Spain': ['LEST', 'NaN'], 'Navalcarnero, Spain': ['LEMD', 'NaN'], 
 'Leioa, Spain': ['LEBB', 'NaN'], 'Sitges, Spain': ['LEBL', 'LERS'], 'Manises, Spain': ['LEVC', 'NaN'], 'Illescas, Spain': ['LEMD', 'NaN'], 'Sant Pere de Ribes, Spain': ['LEBL', 'LERS'], 'La Vall d Uixo, Spain': ['LECH', 'NaN'], 
 'Calafell, Spain': ['LERS', 'NaN'], 'Xirivella, Spain': ['LEVC', 'NaN'], 'Carballo, Spain': ['LECO', 'NaN'], 'Alcazar de San Juan, Spain': ['LERL', 'NaN'], 'Coria del Rio, Spain': ['LEZL', 'NaN'], 'Culleredo, Spain': ['LECO', 'NaN'], 
 'Arcos de la Frontera, Spain': ['LEJR', 'NaN'], 'Hellin, Spain': ['LEAB', 'NaN'], 'Salou, Spain': ['LERS', 'NaN'], 'Valdepenas, Spain': ['LERL', 'NaN'], 'El Campello, Spain': ['LEAL', 'NaN'], 'Crevillent, Spain': ['LEAL', 'NaN'], 
 'Camargo, Spain': ['LEXJ', 'NaN'], 'Xativa, Spain': ['LEVC', 'NaN'], 'Vinaros, Spain': ['LECH', 'NaN'], 'Sesena, Spain': ['LEMD', 'NaN'], 'Catarroja, Spain': ['LEVC', 'NaN'], 'Javea, Spain': ['LEAL', 'NaN'], 'Alaquas, Spain': ['LEVC', 'NaN'], 
 'Durango, Spain': ['LEBB', 'NaN'], 'San Andres del Rabanedo, Spain': ['LELN', 'NaN'], 'Carmona, Spain': ['LEZL', 'NaN'], 'Puente Genil, Spain': ['LEGR', 'NaN'], 'Lebrija, Spain': ['LEZL', 'NaN'], 'Benicarlo, Spain': ['LECH', 'NaN'], 
 'Rota, Spain': ['LEJR', 'NaN'], 'Pineda de Mar, Spain': ['LEBL', 'LERS'], 'Villaviciosa de Odon, Spain': ['LEMD', 'NaN'], 'Lepe, Spain': ['NaN', 'NaN'], 'Redondela, Spain': ['LEVX', 'NaN'], 'Premia de Mar, Spain': ['LEBL', 'LERS'], 
 'Cartama, Spain': ['LEMG', 'NaN'], 'Vicar, Spain': ['LEAM', 'NaN'], 'San Pedro del Pinatar, Spain': ['LEMI', 'NaN'], 'Camas, Spain': ['LEZL', 'NaN'], 'Sant Vicenc dels Horts, Spain': ['LEBL', 'LERS'], 'Martorell, Spain': ['LEBL', 'LERS'], 
 'Almassora, Spain': ['LECH', 'NaN'], 'Sueca, Spain': ['LEVC', 'NaN'], 'Sestao, Spain': ['LEBB', 'NaN'], 'Algemesi, Spain': ['LEVC', 'NaN'], 'Mutxamel, Spain': ['LEAL', 'NaN'], 'Paiporta, Spain': ['LEVC', 'NaN'], 
 'Alhaurin el Grande, Spain': ['LEMG', 'NaN'], 'Betera, Spain': ['LEVC', 'NaN'], 'Eibar, Spain': ['LEBB', 'NaN'], 'Palma, Spain': ['LEPA', 'NaN'], 'Las Palmas de Gran Canaria, Spain': ['GCLP', 'NaN'], 
 'Santa Cruz de Tenerife, Spain': ['GCXO', 'GCTS'], 'San Cristobal de La Laguna, Spain': ['GCXO', 'GCTS'], 'Telde, Spain': ['GCLP', 'NaN'], 'Arona, Spain': ['GCXO', 'GCTS'], 'Santa Lucia de Tirajana, Spain': ['GCLP', 'NaN'], 
 'Arrecife, Spain': ['GCRR', 'NaN'], 'Granadilla de Abona, Spain': ['GCXO', 'GCTS'], 'San Bartolome de Tirajana, Spain': ['GCLP', 'NaN'], 'Eivissa, Spain': ['LEIB', 'NaN'], 'Calvia, Spain': ['LEPA', 'NaN'], 'Adeje, Spain': ['GCXO', 'GCTS'], 
 'Manacor, Spain': ['LEPA', 'NaN'], 'Puerto del Rosario, Spain': ['GCFV', 'NaN'], 'La Orotava, Spain': ['GCXO', 'GCTS'], 'Santa Eularia des Riu, Spain': ['LEIB', 'NaN'], 'Marratxi, Spain': ['LEPA', 'NaN'], 'Llucmajor, Spain': ['LEPA', 'NaN'], 
 'Arucas, Spain': ['GCLP', 'NaN'], 'Los Realejos, Spain': ['GCXO', 'GCTS'], 'Inca, Spain': ['LEPA', 'NaN'], 'Aguimes, Spain': ['GCLP', 'NaN'], 'Ingenio, Spain': ['GCLP', 'NaN'], 'Ciutadella de Menorca, Spain': ['LEMH', 'NaN'], 
 'Puerto de la Cruz, Spain': ['GCXO', 'GCTS'], 'Mao, Spain': ['LEMH', 'NaN'], 'La Oliva, Spain': ['GCFV', 'NaN'], 'Sant Josep de sa Talaia, Spain': ['LEIB', 'NaN'], 'Candelaria, Spain': ['GCXO', 'GCTS'], 
 'Sant Antoni de Portmany, Spain': ['LEIB', 'NaN']
 }

#Estaciones de tren 
CITY_TO_TRAIN_STATIONS = {
"A Coruna, Spain": ["A Coruna-Turistico", "A Corunya"], "A Friela, Spain": ["A Friela-Maside"], "A Gudina, Spain": ["A GUDIÑA-PORTA DE GALICIA"], "A Rua, Spain": ["A Rua-Petin"], "Abejera, Spain": ["Abejera"],
"Agoncillo, Spain": ["Agoncillo"], "Agres, Spain": ["Agres"], "Aguilar, Spain": ["Aguilar de Campoo", "Aguilar de Segarra"], "Aguilas, Spain": ["Aguilas"], "Agullent, Spain": ["Agullent"], "Aix, Spain": ["Aix en Provence"],
"Alagon, Spain": ["Alagon"], "Alar, Spain": ["Alar del Rey-San Quirce"], "Albacete, Spain": ["Albacete-Los Llanos"], "Albaida, Spain": ["Albaida"], "Albuixech, Spain": ["Albuixech"], "Alcala, Spain": ["Alcala Henares-Universidad (apd)", "Alcala de Henares", "Alcala de Xivert"],
"Alcanadre, Spain": ["Alcanadre"], "Alcazar, Spain": ["Alcazar de San Juan"], "Alcolea, Spain": ["Alcolea de Cordoba (apt)"], "Alcover, Spain": ["Alcover"], "Alcoy/Alcoi, Spain": ["Alcoy/alcoi"], "Aldealengua, Spain": ["Aldealengua"],
"Alegria, Spain": ["Alegria de Alava-Dulantzi"], "Alfafar, Spain": ["Alfafar-Benetusser"], "Alfaro, Spain": ["Alfaro"], "Algeciras, Spain": ["Algeciras"], "Algemesi, Spain": ["Algemesi"], "Alhama, Spain": ["Alhama de Aragon", "Alhama de Murcia"],
"Alicante/Alacant, Spain": ["Alicante/alacant"], "Aljaima, Spain": ["Aljaima"], "Almadenejos, Spain": ["Almadenejos-Almaden"], "Almagro, Spain": ["Almagro"], "Almansa, Spain": ["Almansa"], "Almargen, Spain": ["Almargen-Canyete La Real"],
"Almassora/Almazora, Spain": ["Almassora/almazora"], "Almazan, Spain": ["Almazan"], "Almenara, Spain": ["Almenara"], "Almendralejo, Spain": ["Almendralejo"], "Almeria, Spain": ["Almeria"], "Almonaster, Spain": ["Almonaster-Cortegana"],
"Almoraima, Spain": ["Almoraima"], "Almorchon, Spain": ["Almorchon"], "Almuradiel, Spain": ["Almuradiel-Viso del Marques"], "Alora, Spain": ["Alora"], "Alpedrete, Spain": ["Alpedrete-Mataespesa"], "Altafulla, Spain": ["Altafulla-Tamarit"],
"Altsasu/Alsasua, Spain": ["Altsasu/alsasua-Estacion", "Altsasu/alsasua-Pueblo"], "Alzira, Spain": ["Alzira"], "Amusco, Spain": ["Amusco"], "Andoain, Spain": ["Andoain-Centro"], "Andujar, Spain": ["Andujar"], "Anglesola, Spain": ["Anglesola"],
"Antequera, Spain": ["Antequera AV", "Antequera-Santa Ana"], "Anzanigo, Spain": ["Anzanigo"], "Arahal, Spain": ["Arahal"], "Araia, Spain": ["Araia"], "Aranjuez, Spain": ["Aranjuez"], "Aranyales, Spain": ["Aranyales de Muel"],
"Aravaca, Spain": ["Aravaca (apd-Cgd)"], "Arbo, Spain": ["Arbo"], "Arcade, Spain": ["Arcade"], "Archena, Spain": ["Archena-Fortuna"], "Arcos, Spain": ["Arcos de Jalon"], "Areas, Spain": ["Areas"],
"Arevalo, Spain": ["Arevalo"], "Ariza, Spain": ["Ariza"], "Arriate, Spain": ["Arriate"], "Arroyo, Spain": ["Arroyo-Malpartida"], "As, Spain": ["As Neves"], "Asamblea, Spain": ["Asamblea de Mad. Entrevias"],
"Asco, Spain": ["Asco"], "Astorga, Spain": ["Astorga"], "Ateca, Spain": ["Ateca"], "Ategorrieta, Spain": ["Ategorrieta (apd)"], "Avila, Spain": ["Avila"], "Aviles, Spain": ["Aviles"],
"Ayerbe, Spain": ["Ayerbe"], "Azuqueca, Spain": ["Azuqueca"], "Baamonde, Spain": ["Baamonde"], "Babilafuente, Spain": ["Babilafuente"], "Badajoz, Spain": ["Badajoz"], "Badules, Spain": ["Badules"],
"Baides, Spain": ["Baides"], "Balsicas, Spain": ["Balsicas-Mar Menor"], "Barallobre, Spain": ["Barallobre"], "Barcelona, Spain": ["Barcelona-Clot-Arago", "Barcelona-Estació de França", "Barcelona-Passeig de Gracia", "Barcelona-Sant Andreu Comtal", "Barcelona-Sants"], "Barcena, Spain": ["Barcena"], "Barra, Spain": ["Barra de Minyo"],
"Barracas, Spain": ["Barracas"], "Barrientos, Spain": ["Barrientos"], "Beasain, Spain": ["Beasain"], "Becerril, Spain": ["Becerril"], "Bell, Spain": ["Bell-Lloc Durgell"], "Bellavista, Spain": ["Bellavista"],
"Bellpuig, Spain": ["Bellpuig"], "Bembibre, Spain": ["Bembibre"], "Benacazon, Spain": ["Benacazon"], "Benalua, Spain": ["Benalua de Guadix"], "Benaojan, Spain": ["Benaojan-Montejaque"], "Benicarlo, Spain": ["Benicarlo-Penyiscola"],
"Benicassim, Spain": ["Benicassim"], "Beniel, Spain": ["Beniel"], "Benifaio, Spain": ["Benifaio-Almussafes"], "Beniganim, Spain": ["Beniganim"], "Betanzos, Spain": ["Betanzos-Cidade", "Betanzos-Infesta"], "Bilbao, Spain": ["Bilbao-Abando Indalecio Prieto"],
"Binefar, Spain": ["Binefar"], "Bobadilla, Spain": ["Bobadilla"], "Bordils, Spain": ["Bordils-Juia"], "Branyuelas, Spain": ["Branyuelas"], "Brazatortas, Spain": ["Brazatortas-Veredas"], "Brinkola, Spain": ["Brinkola-Onyati"],
"Briviesca, Spain": ["Briviesca"], "Bubierca, Spain": ["Bubierca"], "Bufali, Spain": ["Bufali"], "Burgos, Spain": ["Burgos-Rosa Manzano"], "Burriana, Spain": ["Burriana-Alquerias Ninyo Perdido"], "Busdongo, Spain": ["Busdongo"],
"Cabanas, Spain": ["Cabanas-Areal"], "Cabanyas, Spain": ["Cabanyas de Aliste", "Cabanyas de Ebro"], "Cabeza, Spain": ["Cabeza de Buey"], "Cabezon, Spain": ["Cabezon del Pisuerga"], "Cabra, Spain": ["Cabra del Santo Cristo Y Alicun"], "Caceres, Spain": ["Caceres"],
"Cadiz, Spain": ["Cadiz", "Cadiz-Estadio"], "Calaf, Spain": ["Calaf"], "Calahorra, Spain": ["Calahorra"], "Calamocha, Spain": ["Calamocha Nueva"], "Calamonte, Spain": ["Calamonte"], "Calanyas, Spain": ["Calanyas"],
"Calatayud, Spain": ["Calatayud"], "Calatorao, Spain": ["Calatorao"], "Caldearenas, Spain": ["Caldearenas-Aquilue"], "Caldelas, Spain": ["Caldelas"], "Caldes, Spain": ["Caldes de Malavella"], "Callosa, Spain": ["CALLOSA DE SEGURA - COX", "Callosa de Segura"],
"Calzada, Spain": ["Calzada de Asturias"], "Camallera, Spain": ["Camallera"], "Camarles, Spain": ["Camarles-Deltebre"], "Cambre, Spain": ["Cambre"], "Cambrils, Spain": ["CAMBRILS"], "Caminreal, Spain": ["Caminreal-Fuentes Claras"],
"Camp, Spain": ["Camp Tarragona", "Camp-Redo"], "Campanario, Spain": ["Campanario"], "Campanillas, Spain": ["Campanillas (apt)"], "Campillo, Spain": ["Campillo"], "Campillos, Spain": ["Campillos"], "Campo, Spain": ["Campo de Criptana"],
"Campomanes, Spain": ["Campomanes"], "Campus, Spain": ["Campus Universitario Rabanales/ Cordoba"], "Canabal, Spain": ["Canabal"], "Canfranc, Spain": ["Canfranc"], "Cantalapiedra, Spain": ["Cantalapiedra"], "Canyaveral, Spain": ["Canyaveral"],
"Capcanes, Spain": ["Capcanes"], "Carbajales, Spain": ["Carbajales de Alba"], "Carcaixent, Spain": ["Carcaixent"], "Cardenyosa, Spain": ["Cardenyosa de Avila"], "Carinyena, Spain": ["Carinyena"], "Carrascosa, Spain": ["Carrascosa de Henares"],
"Carrion, Spain": ["Carrion de Los Cespedes"], "Cartagena, Spain": ["Cartagena"], "Cartama, Spain": ["Cartama"], "Casas, Spain": ["Casas de Millan"], "Casatejada, Spain": ["Casatejada"], "Casetas, Spain": ["Casetas"],
"Caspe, Spain": ["Caspe"], "Castejon, Spain": ["Castejon de Ebro"], "Castellnou, Spain": ["Castellnou de Seana"], "Castello, Spain": ["Castello"], "Castiello, Spain": ["Castiello-Pueblo"], "Castillejo, Spain": ["Castillejo-Anyover"],
"Castuera, Spain": ["Castuera"], "Catarroja, Spain": ["Catarroja"], "Catoira, Spain": ["Catoira"], "Caudete, Spain": ["Caudete"], "Cazalla, Spain": ["Cazalla-Constantina"], "Cecebre, Spain": ["Cecebre"],
"Cella, Spain": ["Cella"], "Celra, Spain": ["Celra"], "Cerceda, Spain": ["Cerceda-Meirama"], "Cercedilla, Spain": ["Cercedilla"], "Cervera, Spain": ["Cervera"], "Cesantes, Spain": ["Cesantes"],
"Cesuras, Spain": ["Cesuras"], "Cetina, Spain": ["Cetina"], "Chilches, Spain": ["Chilches"], "Cieza, Spain": ["Cieza"], "Cinco, Spain": ["Cinco Casas"], "Cisneros, Spain": ["Cisneros"],
"Ciudad, Spain": ["Ciudad Real"], "Cocentaina, Spain": ["Cocentaina"], "Colera, Spain": ["Colera"], "Collado, Spain": ["Collado Mediano"], "Corcos, Spain": ["Corcos-Aguilarejo"], "Cordoba, Spain": ["Cordoba"],
"Cortes, Spain": ["Cortes de La Frontera", "Cortes de Navarra"], "Coslada, Spain": ["Coslada (apd)"], "Covas, Spain": ["Covas"], "Crespos, Spain": ["Crespos"], "Cubillas, Spain": ["Cubillas de Santa Marta"], "Cuenca, Spain": ["Cuenca Fernando Zobel"],
"Cuencabuena, Spain": ["Cuencabuena"], "Cullera, Spain": ["Cullera"], "Cumbres, Spain": ["Cumbres Mayores"], "Curtis, Spain": ["Curtis"], "Daimiel, Spain": ["Daimiel"], "Don, Spain": ["Don Benito"],
"Dos, Spain": ["Dos Hermanas"], "Duenyas, Spain": ["Duenyas"], "Duesaigues, Spain": ["Duesaigues-Largentera"], "El Burgo, Spain": ["El Burgo Ranero"], "El Carpio, Spain": ["El Carpio"], "El Carrion, Spain": ["El Carrion"],
"El Chorro, Spain": ["El Chorro"], "El Escorial, Spain": ["El Escorial"], "El Espinar, Spain": ["El Espinar"], "El Higueron, Spain": ["El Higueron (apt)"], "El Pedroso, Spain": ["El Pedroso de La Armunya"], "El Pimpollar, Spain": ["El Pimpollar"],
"El Pozo, Spain": ["El Pozo"], "El Puig, Spain": ["El Puig"], "El Romeral, Spain": ["El Romeral"], "El Tamujoso, Spain": ["El Tamujoso"], "Elche, Spain": ["Elche Parque/elx Parc"], "Elche/Elx, Spain": ["Elche/elx Carrus"],
"Elda, Spain": ["Elda-Petrer"], "Elvinya, Spain": ["Elvinya-Universidade"], "Elx, Spain": ["ELX AV"], "Embid, Spain": ["Embid de Jalon"], "Encinacorba, Spain": ["Encinacorba"], "Epila, Spain": ["Epila"],
"Escacena, Spain": ["Escacena"], "Espeluy, Spain": ["Espeluy"], "Espinosa, Spain": ["Espinosa de Henares", "Espinosa de Villagonzalo (apd)"], "Etxarri, Spain": ["Etxarri-Aranatz"], "Fabara, Spain": ["Fabara"], "Faio, Spain": ["Faio-La Pobla de Massaluca (fayon)"],
"Feculas, Spain": ["Feculas-Navarra"], "Ferreruela, Spain": ["Ferreruela", "Ferreruela de Tabara"], "Ferrol, Spain": ["Ferrol"], "Figueres, Spain": ["Figueres", "Figueres Vilafant"], "Filgueira, Spain": ["Filgueira"], "Finyana, Spain": ["Finyana"],
"Flaca, Spain": ["Flaca"], "Flix, Spain": ["Flix"], "Fornells, Spain": ["Fornells de La Selva"], "Fregenal, Spain": ["Fregenal de La Sierra"], "Fresno, Spain": ["Fresno El Viejo"], "Frieira, Spain": ["Frieira"],
"Fromista, Spain": ["Fromista"], "Fuenlabrada, Spain": ["Fuenlabrada"], "Fuente, Spain": ["Fuente del Arco"], "Fuentes, Spain": ["Fuentes de Ebro"], "Gador, Spain": ["Gador"], "Galapagar, Spain": ["Galapagar-La Navata"],
"Gallur, Spain": ["Gallur"], "Gandia, Spain": ["Gandia"], "Garrovilla, Spain": ["Garrovilla-Las Vegas"], "Gaucin, Spain": ["Gaucin"], "Genoves, Spain": ["Genoves"], "Gergal, Spain": ["Gergal"],
"Gibraleon, Spain": ["Gibraleon"], "Gijon, Spain": ["Gijon"], "Girona, Spain": ["Girona"], "Golmes, Spain": ["Golmes"], "Gomecello, Spain": ["Gomecello"], "Grajal, Spain": ["Grajal"],
"Granada, Spain": ["Granada"], "Granollers, Spain": ["Granollers Centre"], "Granyen, Spain": ["Granyen"], "Grijota, Spain": ["Grijota"], "Grisen, Spain": ["Grisen"], "Gros, Spain": ["Gros"],
"Guadalajara, Spain": ["Guadalajara", "Guadalajara - Yebes"], "Guadalcanal, Spain": ["Guadalcanal"], "Guadalmez, Spain": ["Guadalmez-Los Pedroches"], "Guadiana, Spain": ["Guadiana del Caudillo"], "Guadix, Spain": ["Guadix"], "Gualba, Spain": ["Gualba"],
"Guarenya, Spain": ["Guarenya"], "Gudillos, Spain": ["Gudillos"], "Guillarei, Spain": ["Guillarei"], "Guimorcondo, Spain": ["Guimorcondo"], "Guitiriz, Spain": ["Guitiriz"], "Haro, Spain": ["Haro"],
"Hellin, Spain": ["Hellin"], "Hernani, Spain": ["Hernani-Centro"], "Herradon, Spain": ["Herradon-La Canyada"], "Herrera, Spain": ["Herrera (apd)", "Herrera de Pisuerga"], "Hostalric, Spain": ["Hostalric"], "Huelva, Spain": ["Huelva"],
"Huercal, Spain": ["Huercal-Viator"], "Huesca, Spain": ["Huesca"], "Humanes, Spain": ["Humanes", "Humanes de Mohernando"], "Illescas, Spain": ["Illescas"], "Intxaurrondo, Spain": ["Intxaurrondo"], "Irun, Spain": ["Irun"],
"Iznalloz, Spain": ["Iznalloz"], "Jabugo, Spain": ["Jabugo-Galaroza"], "Jaca, Spain": ["Jaca"], "Jadraque, Spain": ["Jadraque"], "Jaen, Spain": ["Jaen"], "Jerez, Spain": ["Jerez Aeropuerto", "Jerez de La Frontera"],
"Jimena, Spain": ["Jimena de La Frontera"], "Jimera, Spain": ["Jimera de Libar"], "Jodar, Spain": ["Jodar-Ubeda"], "Juneda, Spain": ["Juneda"], "L'Hospitalet De, Spain": ["L'HOSPITALET DE L'INFANT"], "L.Enova, Spain": ["L.enova Manuel"],
"La Encina, Spain": ["La Encina"], "La Floresta, Spain": ["La Floresta"], "La Garena, Spain": ["La Garena"], "La Gineta, Spain": ["La Gineta"], "La Granja, Spain": ["La Granja de San Vicente"], "La Llosa, Spain": ["La Llosa"],
"La Palma, Spain": ["La Palma del Condado"], "La Plana, Spain": ["La Plana-Picamoixons"], "La Pobla, Spain": ["La Pobla Llarga", "La Pobla del Duc"], "La Pola, Spain": ["La Pola de Gordon"], "La Puebla, Spain": ["La Puebla de Arganzon", "La Puebla de Hijar"], "La Riba, Spain": ["La Riba"],
"La Robla, Spain": ["La Robla"], "La Roda, Spain": ["La Roda de Albacete"], "La Selva, Spain": ["La Selva del Camp"], "La Zaida, Spain": ["La Zaida-Sastago"], "Laldea, Spain": ["Laldea-Amposta-Tortosa"], "Lalin, Spain": ["Lalin"],
"Lametlla, Spain": ["Lametlla de Mar"], "Lampolla, Spain": ["Lampolla-El Perello-Deltebre"], "Las Cabezas, Spain": ["Las Cabezas de San Juan"], "Las Caldas, Spain": ["Las Caldas de Besaya"], "Las Matas, Spain": ["Las Matas"], "Las Mellizas, Spain": ["Las Mellizas"],
"Las Navas, Spain": ["Las Navas del Marques"], "Las Rozas, Spain": ["Las Rozas (apd)"], "Las Zorreras, Spain": ["Las Zorreras-Navalquejigo"], "Lebrija, Spain": ["Lebrija"], "Lechago, Spain": ["Lechago"], "Leganes, Spain": ["Leganes"],
"Legazpi, Spain": ["Legazpi"], "Leon, Spain": ["Leon"], "Les, Spain": ["Les Borges Blanques", "Les Borges del Camp", "Les Valls"], "Lespluga, Spain": ["Lespluga de Francoli"], "Lezo, Spain": ["Lezo-Errenteria"], "Linarejos, Spain": ["Linarejos-Pedroso"],
"Linares, Spain": ["Linares-Baeza", "Linares-Congostinas"], "Llanca, Spain": ["Llanca"], "Lleida, Spain": ["Lleida"], "Llerena, Spain": ["Llerena"], "Llodio, Spain": ["Llodio"], "Logronyo, Spain": ["Logronyo"],
"Loja, Spain": ["Loja"], "Longares, Spain": ["Longares"], "Lora, Spain": ["Lora del Rio"], "Lorca, Spain": ["Lorca Sutullena"], "Los Angeles, Spain": ["Los Angeles de San Rafael"], "Los Barrios, Spain": ["Los Barrios"],
"Los Corrales, Spain": ["Los Corrales de Buelna"], "Los Molinos, Spain": ["Los Molinos-Guadarrama"], "Los Negrales, Spain": ["Los Negrales"], "Los Prados, Spain": ["Los Prados"], "Los Rosales, Spain": ["Los Rosales"], "Los Santos, Spain": ["Los Santos de Maimona"],
"Luceni, Spain": ["Luceni"], "Lugo, Spain": ["Lugo"], "Macanet, Spain": ["Macanet-Massanes"], "Madrid, Spain": ["Madrid - Atocha Cercanias", "Madrid Pta.Atocha - Almudena Grandes", "Madrid-Chamartin", "Madrid-Nuevos Ministerios", "Madrid-Principe Pio", "Madrid-Ramon Y Cajal", "Madrid-Recoletos"], "Magaz, Spain": ["Magaz"], "Malaga, Spain": ["Malaga C.a", "Malaga Maria Zambrano"],
"Malianyo, Spain": ["Malianyo"], "Manresa, Spain": ["Manresa"], "Manzanares, Spain": ["Manzanares"], "Manzanos, Spain": ["Manzanos"], "Marca, Spain": ["Marca-Falset"], "Marchena, Spain": ["Marchena"],
"Marcilla, Spain": ["Marcilla de Navarra"], "Maria, Spain": ["Maria de Huerva"], "Massalfassar, Spain": ["Massalfassar-Albuixech"], "Massanassa, Spain": ["Massanassa"], "Mataporquera, Spain": ["Mataporquera"], "Matapozuelos, Spain": ["Matapozuelos"],
"Matillas, Spain": ["Matillas"], "Mave, Spain": ["Mave"], "Meco, Spain": ["Meco (apd-Cgd)"], "Medina, Spain": ["Medina del Campo", "Medina del Campo Alta Velocidad"], "Medinaceli, Spain": ["Medinaceli"], "Mengibar, Spain": ["Mengibar-Artichuela (apd-Cgd)"],
"Merida, Spain": ["Merida"], "Mieres, Spain": ["Mieres-Puente"], "Minaya, Spain": ["Minaya"], "Minyo, Spain": ["Minyo"], "Mirabel, Spain": ["Mirabel"], "Miranda, Spain": ["Miranda de Ebro"],
"Mirasierra, Spain": ["Mirasierra-Paco de Lucia"], "Mollerussa, Spain": ["Mollerussa"], "Moncofa, Spain": ["Moncofa"], "Monforte, Spain": ["Monforte de Lemos"], "Monfrague, Spain": ["Monfrague"], "Monreal, Spain": ["Monreal de Ariza", "Monreal del Campo"],
"Montaverner, Spain": ["Montaverner"], "Montblanc, Spain": ["Montblanc"], "Montearagon, Spain": ["Montearagon"], "Montefurado, Spain": ["Montefurado"], "Montijo, Spain": ["Montijo", "Montijo-El Molino"], "Monzon, Spain": ["Monzon de Campos", "Monzon-Rio Cinca"],
"Mora, Spain": ["Mora La Nova", "Mora de Rubielos"], "Morata, Spain": ["Morata de Jalon"], "Moreda, Spain": ["Moreda"], "Mores, Spain": ["Mores"], "Moriscos, Spain": ["Moriscos"], "Murcia, Spain": ["Murcia"],
"Nanclares/Langraiz, Spain": ["Nanclares/langraiz"], "Narros, Spain": ["Narros del Castillo"], "Nava, Spain": ["Nava del Rey"], "Navalmoral, Spain": ["Navalmoral de La Mata"], "Navalperal, Spain": ["Navalperal"], "Navarrete, Spain": ["Navarrete"],
"Navas, Spain": ["Navas de Riofrio- La Losa"], "Neda, Spain": ["Neda"], "Niebla, Spain": ["Niebla"], "Nine, Spain": ["Nine"], "Nistal, Spain": ["Nistal"], "Nonaspe, Spain": ["Nonaspe"],
"Novelda, Spain": ["Novelda-Aspe"], "Nules, Spain": ["Nules-La Vilavella"], "Nulles, Spain": ["Nulles-Brafim"], "O Barco, Spain": ["O Barco de Valdeorras"], "O Burgo, Spain": ["O Burgo Santiago"], "O Carballinyo, Spain": ["O Carballinyo"],
"O Irixo, Spain": ["O Irixo"], "O Porrinyo, Spain": ["O Porrinyo"], "Olite/Erriberri, Spain": ["Olite/erriberri"], "Ontinyent, Spain": ["Ontinyent"], "Ordes, Spain": ["Ordes"], "Ordizia/Ordicia, Spain": ["Ordizia/ordicia"],
"Orihuela, Spain": ["Orihuela-Miguel Hernandez"], "Ormaiztegui, Spain": ["Ormaiztegui"], "Oropesa, Spain": ["Oropesa de Toledo"], "Orpesa, Spain": ["Orpesa"], "Ortigosa, Spain": ["Ortigosa del Monte"], "Os, Spain": ["Os Peares"],
"Osebe, Spain": ["Osebe"], "Osorno, Spain": ["Osorno"], "Osuna, Spain": ["Osuna"], "Otero, Spain": ["Otero-Herreros"], "Ourense, Spain": ["Ourense", "Ourense Turistico"], "Oviedo, Spain": ["Oviedo", "Oviedo-Llamaquique"],
"Oza, Spain": ["Oza Dos Rios"], "Padron, Spain": ["Padron", "Padron-Barbanza"], "Palanquinos, Spain": ["Palanquinos"], "Palencia, Spain": ["Palencia"], "Palma, Spain": ["Palma del Rio"], "Pamplona/Irunya, Spain": ["Pamplona/irunya"],
"Pancorbo, Spain": ["Pancorbo"], "Paracuellos, Spain": ["Paracuellos-Sabinyan"], "Paredes, Spain": ["Paredes de Nava"], "Parga, Spain": ["Parga"], "Pasaia, Spain": ["Pasaia"], "Pedrelo, Spain": ["Pedrelo-Celtigos"],
"Pedrola, Spain": ["Pedrola"], "Pedroso, Spain": ["Pedroso"], "Penyaflor, Spain": ["Penyaflor"], "Penyaranda, Spain": ["Penyaranda de Bracamonte"], "Perbes, Spain": ["Perbes"], "Perlio, Spain": ["Perlio"],
"Pinar, Spain": ["Pinar de Las Rozas"], "Pinya, Spain": ["Pinya"], "Pinyoi, Spain": ["Pinyoi"], "Pitiegua, Spain": ["Pitiegua"], "Pitis, Spain": ["Pitis"], "Pizarra, Spain": ["Pizarra"],
"Plasencia, Spain": ["Plasencia", "Plasencia de Jalon"], "Pola, Spain": ["Pola de Lena"], "Ponferrada, Spain": ["Ponferrada"], "Pontecesures, Spain": ["Pontecesures"], "Pontedeume, Spain": ["Pontedeume"], "Pontevedra, Spain": ["Pontevedra", "Pontevedra-Turistico", "Pontevedra-Universidad"],
"Porqueros, Spain": ["Porqueros"], "Portbou, Spain": ["Portbou"], "Portela, Spain": ["Portela"], "Posadas, Spain": ["Posadas"], "Pousa, Spain": ["Pousa-Crecente"],
"Pozaldez, Spain": ["Pozaldez"], "Pozuelo, Spain": ["Pozuelo"], "Pradell, Spain": ["Pradell de La Teixeta"], "Pucol, Spain": ["Pucol"], "Puebla, Spain": ["Puebla de Sanabria", "Puebla de Valverde"], "Puente, Spain": ["Puente Genil-Herrera", "Puente de Los Fierros"],
"Puerto, Spain": ["Puerto Real", "Puerto de Santa Maria"], "Puertollano, Spain": ["Puertollano"], "Puigverd, Spain": ["Puigverd de Lleida-Artesa de Lleida"], "Purroy, Spain": ["Purroy"], "Querenyo, Spain": ["Querenyo"], "Quero, Spain": ["Quero"],
"Quintana, Spain": ["Quintana Redonda", "Quintana del Puente", "Quintana-Raneros"], "Quintanilla, Spain": ["Quintanilla de Las Torres"], "Quinto, Spain": ["Quinto"], "Rabade, Spain": ["Rabade"], "Rajadell, Spain": ["Rajadell"], "Redondela, Spain": ["Redondela", "Redondela Av", "Redondela-Picota"],
"Reinosa, Spain": ["Reinosa"], "Renedo, Spain": ["Renedo"], "Requena, Spain": ["Requena Utiel"], "Reus, Spain": ["Reus"], "Riba, Spain": ["Riba-Roja Debre"], "Ribadavia, Spain": ["Ribadavia"],
"Ribaforada, Spain": ["Ribaforada"], "Ricla, Spain": ["Ricla-La Almunia"], "Riells, Spain": ["Riells I Viabrea-Breda"], "Riglos, Spain": ["Riglos"], "Rincon, Spain": ["Rincon de Soto"], "Riudecanyes, Spain": ["Riudecanyes-Botarell"],
"Riudellots, Spain": ["Riudellots"], "Robledo, Spain": ["Robledo de Chavela"], "Roca, Spain": ["Roca-Cuper"], "Roda, Spain": ["Roda de Mar"], "Ronda, Spain": ["Ronda"], "Rubielos, Spain": ["Rubielos de Mora"],
"Rueda, Spain": ["Rueda de Jalon-Lumpiaque"], "Sabinyan, Spain": ["Sabinyan"], "Sabinyanigo, Spain": ["Sabinyanigo"], "Sagunt/Sagunto, Spain": ["Sagunt/sagunto"], "Sahagun, Spain": ["Sahagun"], "Salamanca, Spain": ["Salamanca", "Salamanca-La Alamedilla"],
"Salillas, Spain": ["Salillas de Jalon"], "Salomo, Spain": ["Salomo"], "Salvaterra, Spain": ["Salvaterra de Minyo"], "Salvatierra/Agurain, Spain": ["Salvatierra/agurain"], "Samper, Spain": ["Samper"], "San, Spain": ["San Clodio-Quiroga", "San Estevo Do Sil", "San Fernando Henares", "San Fernando-Bahia Sur", "San Juan del Puerto", "San Miguel de Las Duenyas", "San Morales", "San Pablo", "San Pedro Do Sil", "San Pedro del Arroyo", "San Rafael", "San Roque-La Linea", "San Sebastian/donostia", "San Vicente de Alcantara", "San Yago"],
"Sanabria, Spain": ["Sanabria Alta Velocidad"], "Sant, Spain": ["Sant Celoni", "Sant Gabriel", "Sant Guim de Freixenet", "Sant Jordi Desvalls", "Sant Marti Sesgueioles", "Sant Miquel de Fluvia", "Sant Vicenc de Calders", "Sant Vicenc de Castellet", "Sant Vicent Centre"], "Santa, Spain": ["Santa Cruz de Mudela", "Santa Eugenia", "Santa Eulalia del Campo", "Santa Lucia", "Santa Maria Y La Penya", "Santa Maria de Huerta", "Santa Maria de La Alameda-Peguerinos"], "Santander, Spain": ["Santander"], "Santas, Spain": ["Santas Martas"], "Santiago, Spain": ["Santiago de Compostela", "Santiago-Turistico"],
"Sarinyena, Spain": ["Sarinyena"], "Sarracin, Spain": ["Sarracin de Aliste"], "Sarria, Spain": ["Sarria"], "Sarrion, Spain": ["Sarrion"], "Sax, Spain": ["Sax"], "Segorbe, Spain": ["Segorbe"],
"Segovia, Spain": ["Segovia", "Segovia Guiomar"], "Seguers, Spain": ["Seguers-Sant Pere Sallavinera"], "Segunda, Spain": ["Segunda Aguada"], "Sela, Spain": ["Sela"], "Setenil, Spain": ["Setenil"], "Sevilla, Spain": ["Sevilla-San Bernardo", "Sevilla-Santa Justa", "Sevilla-Virgen del Rocio"],
"Siguenza, Spain": ["Siguenza"], "Silla, Spain": ["Silla"], "Sils, Spain": ["Sils"], "Sobradelo, Spain": ["Sobradelo"], "Socuellamos, Spain": ["Socuellamos"], "Soria, Spain": ["Soria"],
"Soto, Spain": ["Soto del Henares"], "Tablada, Spain": ["Tablada"], "Tafalla, Spain": ["Tafalla"], "Talavera, Spain": ["Talavera de La Reina"], "Tardelcuende, Spain": ["Tardelcuende"], "Tardienta, Spain": ["Tardienta"],
"Tarragona, Spain": ["Tarragona"], "Tarrega, Spain": ["Tarrega"], "Teixeiro, Spain": ["Teixeiro"], "Tembleque, Spain": ["Tembleque"], "Terrassa, Spain": ["Terrassa"], "Terrer, Spain": ["Terrer"],
"Teruel, Spain": ["Teruel"], "Tocina, Spain": ["Tocina"], "Toledo, Spain": ["Toledo"], "Tolosa, Spain": ["Tolosa", "Tolosa Centro"], "Toral, Spain": ["Toral de Los Vados"], "Toro, Spain": ["Toro"],
"Torralba, Spain": ["Torralba"], "Torre, Spain": ["Torre del Bierzo", "Torre-Pacheco"], "Torreblanca, Spain": ["Torreblanca"], "Torredembarra, Spain": ["Torredembarra"], "Torrejon, Spain": ["Torrejon de Ardoz"], "Torrelavega, Spain": ["Torrelavega"],
"Torrelodones, Spain": ["Torrelodones"], "Torrijo, Spain": ["Torrijo del Campo"], "Torrijos, Spain": ["Torrijos"], "Tortosa, Spain": ["Tortosa"], "Totana, Spain": ["Totana"], "Tudela, Spain": ["Tudela de Navarra"],
"Uharte, Spain": ["Uharte-Arakil"], "Ujo, Spain": ["Ujo"], "Ulldecona, Spain": ["Ulldecona -Alcanar-La Senia"], "Universidad, Spain": ["Universidad de Alicante"], "Utebo, Spain": ["Utebo"], "Utrera, Spain": ["Utrera"],
"Uxes, Spain": ["Uxes"], "Val, Spain": ["Val de Pilas"], "Valdecilla, Spain": ["Valdecilla"], "Valdelamusa, Spain": ["Valdelamusa"], "Valdepenyas, Spain": ["Valdepenyas"], "Valdestillas, Spain": ["Valdestillas"],
"Valdetorres, Spain": ["Valdetorres"], "Valence, Spain": ["Valence"], "Valencia, Spain": ["Valencia F.s.l-Hospital La Fe", "Valencia Joaquin Sorolla", "Valencia de Alcantara", "Valencia-Cabanyal", "Valencia-Estacio del Nord"], "Valladolid, Spain": ["Valladolid", "Valladolid-Universidad"], "Vallecas, Spain": ["Vallecas"], "Valls, Spain": ["Valls"],
"Vega, Spain": ["Vega-Magaz"], "Veguellina, Spain": ["Veguellina"], "Venta, Spain": ["Venta de Banyos"], "Viana, Spain": ["Viana", "Viana D Castelo"], "Vicalvaro, Spain": ["Vicalvaro"], "Victoria, Spain": ["Victoria Kent"],
"Vigo, Spain": ["Vigo Guixar", "Vigo Urzaiz"], "Vila, Spain": ["Vila-Real", "Vila-Seca"], "Vilabella, Spain": ["Vilabella"], "Vilagarcia, Spain": ["Vilagarcia de Arousa"], "Vilajuiga, Spain": ["Vilajuiga"], "Vilamalla, Spain": ["Vilamalla"],
"Vilamartin, Spain": ["Vilamartin de Valdeorras"], "Vilanova, Spain": ["Vilanova I La Geltru"], "Vilaverd, Spain": ["Vilaverd"], "Vilches, Spain": ["Vilches"], "Villa, Spain": ["Villa del Rio"], "Villabona, Spain": ["Villabona-Zizurkil"],
"Villacanyas, Spain": ["Villacanyas"], "Villada, Spain": ["Villada"], "Villadepalos, Spain": ["Villadepalos"], "Villadoz, Spain": ["Villadoz"], "Villafranca, Spain": ["Villafranca de Los Barros", "Villafranca de Navarra", "Villafranca del Campo"], "Villahermosa, Spain": ["Villahermosa"],
"Villalba, Spain": ["Villalba de Guadarrama"], "Villamanin, Spain": ["Villamanin"], "Villanua, Spain": ["Villanua-Letranz"], "Villanueva, Spain": ["Villanueva de Cordoba-Los Pedroches", "Villanueva de Gallego", "Villanueva de La Serena", "Villanueva del Rio-Minas"], "Villaquiran, Spain": ["Villaquiran"], "Villar, Spain": ["Villar de Gallimazo"],
"Villarrasa, Spain": ["Villarrasa"], "Villarreal, Spain": ["Villarreal de Huerva"], "Villarrobledo, Spain": ["Villarrobledo"], "Villarrubia, Spain": ["Villarrubia de Cordoba"], "Villasequilla, Spain": ["Villasequilla"], "Villavante, Spain": ["Villavante"],
"Villena, Spain": ["Villena", "Villena Av"], "Vimbodi, Spain": ["Vimbodi I Poblet"], "Vinaixa, Spain": ["Vinaixa"], "Vinaros, Spain": ["Vinaros"], "Vitoria/Gasteiz, Spain": ["Vitoria/gasteiz"], "Xativa, Spain": ["Xativa"],
"Yunquera, Spain": ["Yunquera de Henares"], "Zafra, Spain": ["Zafra", "Zafra Feria"], "Zamora, Spain": ["Zamora"], "Zaragoza, Spain": ["Zaragoza Goya", "Zaragoza Miraflores", "Zaragoza Portillo", "Zaragoza-Delicias"], "Zarzalejo, Spain": ["Zarzalejo"], "Zumarraga, Spain": ["Zumarraga"]
}

#---------------- 2) DESCARGA DE GRAFOS OSM E IMPORTACIÓN DE BASES DE DATOS ----------------
def _load_or_build(path: Path, builder):
    if path.exists():
        with path.open("rb") as fh:
            return pickle.load(fh)
    obj = builder()
    with path.open("wb") as fh:
        pickle.dump(obj, fh)
    return obj

G_drive = _load_or_build(Path("spain_drive_graph.pkl"), _build_spain_drive_graph)


railway_filter = ('["railway"~"rail|light_rail|subway|tram|monorail|funicular|narrow_gauge"]')
G_rail = _load_or_build(
    Path("spain_rail_graph.pkl"),
    lambda: _download_graph("Spain", cf=railway_filter)
)

plane_db = mlc.Dataset("https://githubusercontent.com/EDJNet/european_routes/blob/main/data/european_routes_ranking.csv")
data_asset = next(iter(plane_db.data_assets.values()))
plane_db = data_asset.as_dataframe()

rail_db = mlc.Dataset('https://www.kaggle.com/datasets/sergiodezlpez/possible-spanish-train-routes-without-transfer/croissant/download')
data_asset = next(iter(plane_db.data_assets.values()))
rail_db = data_asset.as_dataframe()
# ──────────────────────────────────────────────────────────────────────────────
# 1.  MAPA DE TERRITORIOS  ▸  “PENINSULA”, “MALLORCA”, “IBIZA”, …
# ──────────────────────────────────────────────────────────────────────────────
#  Cada *_SPANISH_CITIES es ahora un diccionario:  {"Palma, Spain": ["LEPA", …]}
TERRITORY_DICTS = {
    "PENINSULA": PENINSULAR_SPANISH_CITIES,
    "MALLORCA":  MALLORCA,
    "IBIZA":     IBIZA,
    "MENORCA":   MENORCA,
    "GRAN_CANARIA":  GRAN_CANARIA,
    "TENERIFE":      TENERIFE,
    "FUERTEVENTURA": FUERTEVENTURA,
    "LANZAROTE":     LANZAROTE,
}

TERRITORY_OF = {
    city: territory
    for territory, d in TERRITORY_DICTS.items()
    for city in d.keys()
}

# ──────────────────────────────────────────────────────────────────────────────
# 2.  PRECALCULAR COORDENADAS GEOGRÁFICAS (una llamada a OSM por ciudad, con caché)
# ──────────────────────────────────────────────────────────────────────────────
@lru_cache(maxsize=None)
def geocode_city(city_name: str):
    return ox.geocode(city_name)

city_coords = {c: geocode_city(c) for c in SPANISH_CITIES}

# ──────────────────────────────────────────────────────────────────────────────
# 3.  OPTIMIZACIONES PARA BÚSQUEDAS EN BASES DE DATOS DE TREN Y AVIÓN
# ──────────────────────────────────────────────────────────────────────────────
if not rail_db.empty:
    rail_db = rail_db.set_index(["departure", "arrival"])
else:
    rail_db = pd.DataFrame(index=pd.MultiIndex.from_tuples([], names=["departure", "arrival"]))

plane_db = plane_db.set_index(["origin_airport_icao", "destination_airport_icao"])


# ──────────────────────────────────────────────────────────────────────────────
# 4.  BUCLE PRINCIPAL  (pares de ciudades no ordenados → dos filas dirigidas)
# ──────────────────────────────────────────────────────────────────────────────
rows = []

for orig, dest in combinations(SPANISH_CITIES.keys(), 2):

    orig_terr, dest_terr = TERRITORY_OF[orig], TERRITORY_OF[dest]
    same_territory = orig_terr == dest_terr

    orig_coord = city_coords[orig]
    dest_coord = city_coords[dest]

    # plantillas de fila (ida y vuelta)
    row_fwd = {"ciudad_proc": orig,  "ciudad_dest": dest,
               "dist_carretera": None, "dist_vía": None, "dist_aire": None}
    row_rev = {"ciudad_proc": dest,  "ciudad_dest": orig,
               "dist_carretera": None, "dist_vía": None, "dist_aire": None}

    # ── 1) CARRETERA ▸  solo si están en el mismo territorio
    if same_territory:
        try:
            km = (
                nx.shortest_path_length(
                    G_drive,
                    ox.distance.nearest_nodes(G_drive, *orig_coord[::-1]),
                    ox.distance.nearest_nodes(G_drive, *dest_coord[::-1]),
                    weight="length",
                ) / 1000  # convertir a kilómetros
            )
        except nx.NetworkXNoPath:
            km = float("nan")

        # • misma ISLA  ➜ solo carretera (ya cumplido aquí)
        row_fwd["dist_carretera"] = row_rev["dist_carretera"] = km

    # ── 2) FERROCARRIL ▸  solo entre ciudades peninsulares
    if same_territory and orig_terr == "PENINSULA":
        orig_stn = CITY_TO_TRAIN_STATIONS.get(orig, [])
        dest_stn = CITY_TO_TRAIN_STATIONS.get(dest, [])
        if any((o, d) in rail_db.index for o in orig_stn for d in dest_stn):
            try:
                km = (
                    nx.shortest_path_length(
                        G_rail,
                        ox.distance.nearest_nodes(G_rail, *orig_coord[::-1]),
                        ox.distance.nearest_nodes(G_rail, *dest_coord[::-1]),
                        weight="length",
                    ) / 1000
                )
            except nx.NetworkXNoPath:
                km = float("nan")

            row_fwd["dist_vía"] = row_rev["dist_vía"] = km

    # ── 3) AVIÓN ▸  (a) territorios distintos o (b) dos ciudades peninsulares
    if (not same_territory) or (orig_terr == dest_terr == "PENINSULA"):
        orig_air = [c for c in SPANISH_CITIES[orig]  if c != "NaN"]
        dest_air = [c for c in SPANISH_CITIES[dest] if c != "NaN"]
        if any((o, d) in plane_db.index for o in orig_air for d in dest_air):
            km = round(geodesic(orig_coord, dest_coord).kilometers, 1)
            row_fwd["dist_aire"] = row_rev["dist_aire"] = km

    rows.extend([row_fwd, row_rev])

# ──────────────────────────────────────────────────────────────────────────────
# 5.  CREAR DATAFRAME Y GUARDAR ARCHIVO EXCEL
# ──────────────────────────────────────────────────────────────────────────────
distance_data = pd.DataFrame(rows, columns=[
    "ciudad_proc", "ciudad_dest",
    "dist_carretera", "dist_vía", "dist_aire"
])

# Guardamos con un nombre único y coherente para todos los scripts
distance_data.to_excel("dataset_distancias_españa.xlsx", index=False)

"""
SCRIPT 2: SIMULACIÓN DE EVENTOS
"""

# dataset_generator.py
import pandas as pd
import numpy as np

# 1. CARGAR DATASET DE DISTANCIAS

def safe_distance(df, origin, dest, column):
    """
    Return a float distance or np.nan if the row/column is missing or NaN.
    """
    sel = df.loc[(df["ciudad_proc"] == origin) &
                 (df["ciudad_dest"] == dest), column]
    if sel.empty:
        return np.nan
    value = sel.iloc[0]
    return value if not pd.isna(value) else np.nan


#    Debe existir el archivo 'dataset_distancias_españa.xlsx' en el mismo directorio
dist_df = pd.read_excel("dataset_distancias_españa.xlsx")

# 2. PARÁMETROS DE GENERACIÓN
TOTAL_OBS = 250
CIUDADES = dist_df["ciudad_proc"].unique().tolist()
DESTINO_FINAL = "Segovia, Spain"  # Debe coincidir exactamente con 'ciudad_dest'
EF_CO2 = {"coche": 0.171, "tren": 0.035, "avion": 0.246}  # kg CO₂ / km

rows = []
np.random.seed(42)
for obs in range(1, TOTAL_OBS + 1):
    origen = np.random.choice(CIUDADES)
    hay_escala = np.random.rand() < 0.20
    escala = np.random.choice([c for c in CIUDADES if c != origen]) if hay_escala else None

    # --- Segmento 1 ---
    modos1 = ["coche", "tren"] if origen == "Madrid, Spain" else ["coche", "tren", "avion"]
    modo1 = np.random.choice(modos1)
    filtro1 = (dist_df["ciudad_proc"] == origen) & (dist_df["ciudad_dest"] == (escala or DESTINO_FINAL))
    if modo1 == "coche":
        km1 = safe_distance(dist_df, origen, (escala or DESTINO_FINAL), "dist_carretera")
    elif modo1 == "tren":
        km1 = safe_distance(dist_df, origen, (escala or DESTINO_FINAL), "dist_vía")
    else:
        km1 = safe_distance(dist_df, origen, (escala or DESTINO_FINAL), "dist_aire")

    if np.isnan(km1):
        continue

    co2_1 = km1 * EF_CO2[modo1]

    total_km = km1
    total_huella = co2_1
    transporte_str = modo1

    # --- Segmento 2 (si hay escala) ---
    if hay_escala:
        modo2 = np.random.choice(["coche", "tren", "avion"])
        filtro2 = (dist_df["ciudad_proc"] == escala) & (dist_df["ciudad_dest"] == DESTINO_FINAL)
    if modo2 == "coche":
        km2 = safe_distance(dist_df, escala, DESTINO_FINAL, "dist_carretera")
    elif modo2 == "tren":
        km2 = safe_distance(dist_df, escala, DESTINO_FINAL, "dist_vía")
    else:
        km2 = safe_distance(dist_df, escala, DESTINO_FINAL, "dist_aire")

        co2_2 = km2 * EF_CO2[modo2]
    
        if np.isnan(km2):
            continue

        total_km += km2
        total_huella += co2_2
        transporte_str += f" + {modo2}"

    rows.append({
        "nº_observación":   obs,
        "sede_origen":      origen,
        "km_totales":       round(total_km, 2),
        "transporte":       transporte_str,
        "huella_CO2_kg":    round(total_huella, 2)
    })

# 3. CREAR DATAFRAME Y GUARDAR
df = pd.DataFrame(rows)
df.to_csv("caso1.csv", index=False)

# 4. GENERAR DUMMIES Y EXPORTAR

df = df.dropna(subset=["km_totales", "huella_CO2_kg"])
df_dummy = pd.get_dummies(df, columns=["sede_origen", "transporte"], drop_first=True)
df_dummy.to_csv("caso1_dummy.csv", index=False)


"""
CASO 3: MODELO
"""

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from codecarbon import EmissionsTracker
from codecarbon import OfflineEmissionsTracker

# Configuración de CodeCarbon
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
        save_to_file=save_to_file
        )

# 1. CARGAR DATASET GENERADO
#    Asegúrate de ejecutar primero dataset_generator.py
df = pd.read_csv("caso1_dummy.csv")

try:
    df = pd.read_csv("caso1_dummy.csv")
except FileNotFoundError as e:
    raise SystemExit("Necesitas ejecutar primero Script 2 (genera 'caso1_dummy.csv').") from e


# 2. PREPARAR DATOS
X = df.drop(["nº_observación", "huella_CO2_kg"], axis=1)
y = df["huella_CO2_kg"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. INICIAR CODECARBON
tracker.start()

# 4. ENTRENAR REGRESIÓN LINEAL
lr = LinearRegression()
lr.fit(X_train, y_train)

# 5. DETENER RASTREADOR Y OBTENER EMISIONES
emissions_kg = tracker.stop()

# 6. EVALUACIÓN

y_pred = lr.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
r2  = r2_score(y_test, y_pred)

log(f"MSE en test: {mse:.2f}")
log(f"R² en test: {r2:.2f}")
log(f"Emisiones estimadas durante el fit: {emissions_kg:.4f} kg CO₂")

# 7. PREDICCIONES DE EJEMPLO ─────────────────────────────────────
# Creamos un DataFrame con las mismas columnas que X_train,
# rellenamos con ceros y dejamos que el modelo responda.
demo_raw = pd.DataFrame([
    {'km_totales': 100,  'huella_CO2_kg': np.nan},   # placeholder cols
    {'km_totales': 500,  'huella_CO2_kg': np.nan},
    {'km_totales': 1000, 'huella_CO2_kg': np.nan}
])

# Reindex para que coincidan las columnas con las del modelo
demo = demo_raw.reindex(columns=X_train.columns, fill_value=0)
predicciones = lr.predict(demo)

log("\n=== Predicciones de ejemplo ===")
for params, pred in zip([100, 500, 1000], predicciones):
    log(f"{params:>4} km totales  →  {pred:6.2f} kg CO₂")


"""
SCRIPT 4: CARBON COMPENSATION CALCULATOR
"""

class CarbonCalculator:
    def __init__(self):
        # Datos de especies de árboles (kg CO2/año)
        self.species_data = {
            'Quercus_ilex': {
                'min_age': 10,  # Edad mínima para absorción significativa
                'absorption_range': (84, 151),  # kg CO2/año (pequeño a grande)
                'description': 'Encina (Quercus ilex): árbol mediterráneo resistente',
                'cost_per_tree': 35.00,  # Costo estimado por árbol (EUR)
                'maintenance_cost': 5.00,  # Costo anual de mantenimiento (EUR)
                'survival_rate': 0.85  # Tasa de supervivencia estimada
            },
            'Pinus_pinea': {
                'min_age': 15,
                'absorption_by_age': {
                    15: 0.40 * 1000,  # Convertir Mg a kg
                    30: 2.5 * 1000,
                    50: 15.8 * 1000,
                    100: 106.20 * 1000
                },
                'description': 'Pino piñonero (Pinus pinea): crecimiento lento pero alta absorción a largo plazo',
                'cost_per_tree': 25.00,  # Más económico que Quercus
                'maintenance_cost': 3.50,  # Menor mantenimiento
                'survival_rate': 0.90  # Mayor tasa de supervivencia
            }
        }
        
        # Definición de las opciones de reforestación
        self.reforestation_options = {
            '100_quercus': {
                'name': '100% Quercus ilex',
                'description': 'Opción tradicional con encinas solamente',
                'composition': [('Quercus_ilex', 1.0)]
            },
            '50_50_mix': {
                'name': '50% Quercus - 50% Pinus',
                'description': 'Combinación equilibrada de ambas especies',
                'composition': [('Quercus_ilex', 0.5), ('Pinus_pinea', 0.5)]
            },
            '100_pinus': {
                'name': '100% Pinus pinea',
                'description': 'Opción rápida y económica con pinos solamente',
                'composition': [('Pinus_pinea', 1.0)]
            }
        }
    
    def calculate_biomass_co2(self, dry_biomass_kg):
        """Calcula el CO2 absorbido basado en la biomasa seca del árbol"""
        return dry_biomass_kg * 0.5 * 3.67
    
    def get_absorption_rate(self, species, tree_age=None, tree_size='medium'):
        """Obtiene la tasa de absorción para una especie en particular"""
        if species not in self.species_data:
            raise ValueError(f"Especie no soportada. Opciones: {list(self.species_data.keys())}")
        
        species_info = self.species_data[species]
        
        if species == 'Quercus_ilex':
            if tree_size == 'small':
                return species_info['absorption_range'][0]
            elif tree_size == 'large':
                return species_info['absorption_range'][1]
            else:
                # Valor promedio si no se especifica tamaño
                return sum(species_info['absorption_range'])/2
        elif species == 'Pinus_pinea':
            if not tree_age:
                raise ValueError("Para Pinus pinea debe especificar la edad del árbol")
            
            # Interpolación lineal para edades no definidas exactamente
            ages = sorted(species_info['absorption_by_age'].keys())
            if tree_age in ages:
                return species_info['absorption_by_age'][tree_age]
            else:
                # Encontrar los puntos más cercanos para interpolación
                lower_age = max(a for a in ages if a <= tree_age)
                upper_age = min(a for a in ages if a >= tree_age)
                
                lower_abs = species_info['absorption_by_age'][lower_age]
                upper_abs = species_info['absorption_by_age'][upper_age]
                
                # Interpolación lineal
                return lower_abs + (upper_abs - lower_abs) * (tree_age - lower_age) / (upper_age - lower_age)
    
    def compare_reforestation_options(self, total_co2, tree_age_pinus=15, tree_size_quercus='medium'):
        """
        Compara las tres opciones de reforestación para una huella de carbono dada
        
        Args:
            total_co2: Huella total de CO2 a compensar (kg)
            tree_age_pinus: Edad inicial de los pinos (para opciones que los incluyan)
            tree_size_quercus: Tamaño de las encinas (pequeño, medio, grande)
        
        Returns:
            Diccionario con análisis comparativo de todas las opciones
        """
        comparison = {}
        
        for option_key, option_data in self.reforestation_options.items():
            # Calcular número de árboles de cada tipo
            total_trees = 0
            trees_by_species = {}
            costs = {
                'initial': 0.0,
                'annual_maintenance': 0.0,
                'total_5yr': 0.0,
                'total_10yr': 0.0
            }
            
            for species, proportion in option_data['composition']:
                # Calcular absorción por árbol
                if species == 'Quercus_ilex':
                    absorption = self.get_absorption_rate(species, tree_size=tree_size_quercus)
                else:
                    absorption = self.get_absorption_rate(species, tree_age=tree_age_pinus)
                
                # Calcular árboles necesarios (considerando proporción)
                trees_needed = (total_co2 / absorption) * proportion
                trees_by_species[species] = trees_needed
                total_trees += trees_needed
                
                # Calcular costos
                species_info = self.species_data[species]
                costs['initial'] += trees_needed * species_info['cost_per_tree']
                costs['annual_maintenance'] += trees_needed * species_info['maintenance_cost']
            
            # Calcular costos a 5 y 10 años
            costs['total_5yr'] = costs['initial'] + (costs['annual_maintenance'] * 5)
            costs['total_10yr'] = costs['initial'] + (costs['annual_maintenance'] * 10)
            
            # Calcular tiempo estimado de compensación
            compensation_time = self.calculate_compensation_time_mixed(
                total_co2, option_data['composition'], 
                tree_age_pinus, tree_size_quercus)
            
            # Almacenar resultados de la opción
            comparison[option_key] = {
                'name': option_data['name'],
                'description': option_data['description'],
                'total_trees': total_trees,
                'trees_by_species': trees_by_species,
                'compensation_time_years': compensation_time,
                'costs': costs,
                'absorption_rate_kg_per_year': self.calculate_annual_absorption(
                    option_data['composition'], tree_age_pinus, tree_size_quercus)
            }
        
        return comparison
    
    def calculate_compensation_time_mixed(self, total_co2, composition, tree_age_pinus, tree_size_quercus):
        """
        Calcula el tiempo requerido para absorber completamente el CO2 con una mezcla de especies
        """
        years_required = 0
        remaining_co2 = total_co2
        
        while remaining_co2 > 0 and years_required < 100:  # Límite de 100 años
            years_required += 1
            annual_absorption = 0
            
            for species, proportion in composition:
                if species == 'Quercus_ilex':
                    current_age = years_required  # Asumimos plantación de árboles jóvenes
                    if current_age >= self.species_data[species]['min_age']:
                        absorption = self.get_absorption_rate(species, tree_size=tree_size_quercus)
                        annual_absorption += absorption * (total_co2 / self.get_absorption_rate(
                            species, tree_size=tree_size_quercus)) * proportion
                elif species == 'Pinus_pinea':
                    current_age = tree_age_pinus + years_required
                    if current_age >= self.species_data[species]['min_age']:
                        absorption = self.get_absorption_rate(species, tree_age=current_age)
                        annual_absorption += absorption * (total_co2 / self.get_absorption_rate(
                            species, tree_age=tree_age_pinus)) * proportion
            
            remaining_co2 -= annual_absorption
            if remaining_co2 < 0:
                remaining_co2 = 0
        
        return years_required
    
    def calculate_annual_absorption(self, composition, tree_age_pinus, tree_size_quercus):
        """
        Calcula la absorción anual promedio en los primeros 10 años
        """
        total_absorption = 0
        
        for species, proportion in composition:
            if species == 'Quercus_ilex':
                absorption = self.get_absorption_rate(species, tree_size=tree_size_quercus)
                effective_years = max(0, 10 - self.species_data[species]['min_age'])
                total_absorption += absorption * proportion * (effective_years / 10)
            elif species == 'Pinus_pinea':
                abs_initial = self.get_absorption_rate(species, tree_age=tree_age_pinus)
                abs_final = self.get_absorption_rate(species, tree_age=tree_age_pinus+10)
                total_absorption += ((abs_initial + abs_final) / 2) * proportion
        
        return total_absorption

    def get_detailed_option(self, option_key, total_co2, tree_age_pinus=15, tree_size_quercus='medium'):
        """
        Obtiene información detallada de una opción específica
        
        Args:
            option_key: '100_quercus', '50_50_mix' o '100_pinus'
            total_co2: Huella de carbono a compensar (kg)
            tree_age_pinus: Edad inicial de los pinos
            tree_size_quercus: Tamaño de las encinas
        
        Returns:
            Diccionario con todos los detalles de la opción seleccionada
        """
        if option_key not in self.reforestation_options:
            raise ValueError(f"Opción no válida. Use: {list(self.reforestation_options.keys())}")
        
        # Calcular todas las opciones
        all_options = self.compare_reforestation_options(
            total_co2, tree_age_pinus, tree_size_quercus)
        
        return all_options[option_key]

# Ejemplo de uso con selección programática directa
if __name__ == "__main__":
    try:
        # Intentar obtener la huella de carbono del modelo de script 3
        from sklearn.linear_model import LinearRegression
        import pandas as pd
        
        # Cargar los datos y modelo del script 3
        df = pd.read_csv("caso1_dummy.csv")
        X = df.drop(["nº_observación", "huella_CO2_kg"], axis=1)
        y = df["huella_CO2_kg"]
        
        # Entrenar el modelo si no existe
        try:
            lr = LinearRegression()
            lr.fit(X, y)
            
            # Calcular la huella de carbono promedio
            huella_co2 = y.mean()
        except Exception as e:
            log(f"Error al cargar el modelo: {e}")
            log("Usando valor por defecto de 7500 kg CO2")
            huella_co2 = 7500
    except Exception as e:
        log(f"Error al cargar los datos: {e}")
        log("Usando valor por defecto de 7500 kg CO2")
        huella_co2 = 7500
    
    # 1. Inicializar calculadora
    calculator = CarbonCalculator()
    
    # 2. Calcular todas las opciones
    log("\nCalculando opciones de compensación...\n")
    opciones = calculator.compare_reforestation_options(
        total_co2=huella_co2,
        tree_age_pinus=15,
        tree_size_quercus='medium'
    )
    
    # 3. Selección programática directa (elige una de estas tres líneas)
    opcion_elegida = opciones['100_quercus']  # Opción 1: 100% Quercus
    # opcion_elegida = opciones['50_50_mix']   # Opción 2: 50% Quercus - 50% Pinus
    # opcion_elegida = opciones['100_pinus']   # Opción 3: 100% Pinus
    
    # 4. Mostrar resultados de la opción seleccionada
    log("\n=== OPCIÓN SELECCIONADA ===")
    log(f"{opcion_elegida['name']}")
    log(f"Descripción: {opcion_elegida['description']}")
    log(f"\nPara compensar {huella_co2:.2f} kg de CO2:")
    log(f"• Total árboles necesarios: {opcion_elegida['total_trees']:.0f}")
    
    # Detalle por especie
    log("\nDesglose por especie:")
    for especie, cantidad in opcion_elegida['trees_by_species'].items():
        log(f"  - {especie.replace('_', ' ')}: {cantidad:.0f} unidades")
    
    # Tiempo y costos
    log(f"\n• Tiempo estimado de compensación: {opcion_elegida['compensation_time_years']} años")
    log(f"• Absorción anual promedio: {opcion_elegida['absorption_rate_kg_per_year']:.0f} kg CO2/año")
    log(f"\nCostos estimados:")
    log(f"  - Costo inicial: {opcion_elegida['costs']['initial']:.2f}€")
    log(f"  - Mantenimiento anual: {opcion_elegida['costs']['annual_maintenance']:.2f}€")
    log(f"  - Costo total a 5 años: {opcion_elegida['costs']['total_5yr']:.2f}€")
    log(f"  - Costo total a 10 años: {opcion_elegida['costs']['total_10yr']:.2f}€")