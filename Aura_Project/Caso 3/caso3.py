"""
SCRIPT 1: DISTANCIAS
"""

import pandas as pd
from itertools import combinations
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import time
from datetime import datetime
import logging
import mlcroissant as mlc
import json
from pathlib import Path

# Configuración de logging
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
log_filename = f"AURA_CASO3_TEST_LOG_{timestamp}.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename, mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
log = logging.info  # Alias para usar el log como si fuera print()

# 1. Cargar el CSV con las ciudades y su país
df = mlc.Dataset('https://www.kaggle.com/datasets/ibrarhussain123/world-largest-cities-by-population-2024/croissant/download')
data_asset = next(iter(df.data_assets.values()))
df = data_asset.as_dataframe()

# 2. Crear formato ciudad, país y geocodificar cada ciudad una vez
# -------------------------------------------------------------------
#  C A M B I O   C L A V E   →  coordenadas sin depender de Nominatim
#  Inserta este bloque justo después de cargar el dataframe `df`
# -------------------------------------------------------------------
import json
from pathlib import Path
from geopy.geocoders import Nominatim

# Catálogo (≈ 40 000 ciudades) con lat/lon ya incluidos
WORLD_CITIES_URL = (
    "https://gist.githubusercontent.com"
    "/ofou/9c33f377d16e033924f74fa3cce49296/raw/worldcities.csv"
)

aux_df = (
    pd.read_csv(WORLD_CITIES_URL, usecols=["city", "country", "lat", "lng"])
      .assign(key=lambda d: d["city"].str.strip().str.lower()
                           + ", "
                           + d["country"].str.strip().str.lower())
)

coords_catalog = dict(
    zip(aux_df["key"], zip(aux_df["lat"], aux_df["lng"]))
)

# Caché en disco para ejecuciones futuras
CACHE_FILE = Path("city_coords.json")
if CACHE_FILE.exists():
    coordinates: dict[str, tuple[float, float]] = {
        k: tuple(v) for k, v in json.loads(CACHE_FILE.read_text()).items()
    }
else:
    coordinates = {}

# Geocodificador solo como “plan B”
geolocator = Nominatim(user_agent="city-distance-demo")

def _get_coords(city: str, country: str) -> tuple[float, float] | None:
    key = f"{city.strip().lower()}, {country.strip().lower()}"
    if key in coords_catalog:              # ‼️ 99 % de los casos
        return coords_catalog[key]

    # Solo llega aquí lo que no está en el catálogo
    loc = geolocator.geocode(f"{city}, {country}")
    if loc:
        return (loc.latitude, loc.longitude)
    return None

# Completar diccionario `coordinates`
for _, row in df.iterrows():
    city_fmt = f"{row['city'].strip()}, {row['country'].strip()}"
    if city_fmt in coordinates:            # ya en caché
        continue
    coords = _get_coords(row["city"], row["country"])
    if coords:
        coordinates[city_fmt] = coords
    else:
        log(f"⚠️ Sin coordenadas: {city_fmt}")
    time.sleep(1)                          # cortesía con Nominatim

# Guardar caché para la próxima vez
CACHE_FILE.write_text(json.dumps(coordinates))
# -------------------------------------------------------------------


for i, row in df.iterrows():
    # Formatear como "Ciudad, País"
    city_formatted = f"{row['city'].strip()}, {row['country'].strip()}"
    query = city_formatted  # Usar el mismo formato para la búsqueda
    
    location = geolocator.geocode(query)
    if location:
        coordinates[city_formatted] = (
            location.latitude,
            location.longitude
        )
    else:
        log(f"⚠️ No se pudo geocodificar: {query}")
    time.sleep(1)  # Respeto al límite de 1 req/sec de Nominatim

# 3. Calcular distancias entre pares de ciudades
records = []
for (city1, coord1), (city2, coord2) in combinations(coordinates.items(), 2):
    distance_km = geodesic(coord1, coord2).km
    records.append({
        "ciudad1": city1,
        "ciudad2": city2,
        "distancia": distance_km
    })

# 4. Guardar en Excel
dis_df = pd.DataFrame(records)
dis_df.to_excel("dataset_distancias_mundo.xlsx", index=False)
log(dis_df.head())

"""
SCRIPT 2.1: DATASET DE ASISTENCIA
"""

import pandas as pd
import numpy as np

# 1. Cargar datos
df = pd.read_excel("distancias_mundo.xlsx")
class_df = mlc.Dataset('https://www.kaggle.com/datasets/teejmahal20/airline-passenger-satisfaction/croissant/download')
data_asset = next(iter(class_df.data_assets.values()))
class_df = data_asset.as_dataframe()

# 2. Preparar listas de ciudades
CIUDADES_ESPANOLAS = []
CIUDADES_EXTRANJERAS = []
for _, row in df.iterrows():
    for col in ["ciudad1", "ciudad2"]:
        ciudad = row[col]
        if ", Spain" in ciudad:
            CIUDADES_ESPANOLAS.append(ciudad)
        else:
            CIUDADES_EXTRANJERAS.append(ciudad)
CIUDADES_ESPANOLAS = list(set(CIUDADES_ESPANOLAS))
CIUDADES_EXTRANJERAS = list(set(CIUDADES_EXTRANJERAS))

# 3. Función para buscar distancia en cualquier orden
def get_distance(orig: str, dest: str) -> float:
    """
    Devuelve la distancia (km) entre dos ciudades.
    Primero intenta el Excel; si no está, calcula geodésica
    usando el diccionario `coordinates` (catálogo + caché).
    """
    # 1) ¿está en el Excel?
    mask = (
        ((df["ciudad1"] == orig) & (df["ciudad2"] == dest)) |
        ((df["ciudad1"] == dest) & (df["ciudad2"] == orig))
    )
    if not df.loc[mask, "distancia"].empty:
        return float(df.loc[mask, "distancia"].iloc[0])

    # 2) Fallback sin llamadas externas
    try:
        coord1 = coordinates[orig]
        coord2 = coordinates[dest]
    except KeyError:
        raise ValueError(f"Coordenadas no encontradas para {orig} o {dest}")

    return geodesic(coord1, coord2).km

# 4. Simulación
asistencia = 32104
df_gen = pd.DataFrame(columns=["procedencia","escala","distancia","clase","huella"])

for i in range(asistencia):
    # 4.1 Procedencia: 20% española, 80% extranjera
    if np.random.rand() < 0.2:
        proc = np.random.choice(CIUDADES_ESPANOLAS)
    else:
        proc = np.random.choice(CIUDADES_EXTRANJERAS)
    df_gen.loc[i, "procedencia"] = proc

    # 4.2 Escala & distancia
    if proc == "Madrid, Spain":
        escala = np.nan
        dist = 0.0
    else:
        if np.random.rand() < 0.7:  # vuelo directo
            escala = np.nan
            base_km = get_distance(proc, "Madrid, Spain")
            dist = base_km * (1 + np.random.uniform(0, 0.1))
        else:  # con escala
            posibles = [
                r["ciudad2"] for _, r in df.iterrows()
                if r["ciudad1"] == proc
                and get_distance(proc, r["ciudad2"]) < get_distance(proc, "Madrid, Spain")
            ]
            escala = np.random.choice(posibles) if posibles else np.nan
            if pd.isna(escala):
                base_km = get_distance(proc, "Madrid, Spain")
                dist = base_km * (1 + np.random.uniform(0, 0.1))
            else:
                d1 = get_distance(proc, escala)
                d2 = get_distance(escala, "Madrid, Spain")
                dist = (d1 + d2) * (1 + np.random.uniform(0, 0.1))

    df_gen.loc[i, ["escala", "distancia"]] = [escala, dist]

    # 4.3 Clase (según distribución en classes.csv) (https://www.kaggle.com/datasets/teejmahal20/airline-passenger-satisfaction)
    probs = class_df["Class"].value_counts(normalize=True)
    clase = np.random.choice(probs.index, p=probs.values)
    df_gen.loc[i, "clase"] = clase

    # 4.4 Huella de carbono con sus coeficientes
    if clase == "Business":
        factor = 0.22652 if dist < 2500 else 0.42882
    elif clase == "Eco Plus":
        factor = 0.23659 if dist < 2500 else 0.225
    else:  # Economy
        factor = 0.15102 if dist < 2500 else 0.14787

    huella = dist * factor * (1 + np.random.uniform(-0.1, 0.1))
    df_gen.loc[i, "huella"] = huella

# 5. Introducir ~15% de missing values
n_missing = int(asistencia * 0.15)
rows_to_blank = np.random.choice(df_gen.index, size=n_missing, replace=False)
cols = ["escala", "distancia", "clase", "huella"]
for r in rows_to_blank:
    c = np.random.choice(cols)
    df_gen.at[r, c] = np.nan

# 6. Guardar
df_gen.to_excel("asistencia.xlsx", index=False)
log(df_gen.head()) ############################################################MIRAR ERROR

"""
CASO 2.2: MODELO DE ASISTENCIA
"""

import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error, r2_score
from codecarbon import OfflineEmissionsTracker

# 1. Cargar datos
df = pd.read_excel("asistencia.xlsx")

# eliminar observaciones sin valor de huella ─ el modelo no admite NaN en y
df = df.dropna(subset=["huella"]).reset_index(drop=True)

# 2. Separar características (X) y objetivo (y)
X = df[["procedencia", "escala", "distancia", "clase"]]
y = df["huella"]

# 3. Definir transformaciones de preprocesamiento

# 3.1 Variables numéricas
numeric_features = ["distancia"]
numeric_transformer = Pipeline(steps=[
    ("imputar_media", SimpleImputer(strategy="mean")),
    ("escalar", StandardScaler())
])

# 3.2 Variables categóricas
categorical_features = ["procedencia", "escala", "clase"]
categorical_transformer = Pipeline(steps=[
    ("imputar_constante", SimpleImputer(strategy="constant", fill_value="missing")),
    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse=False))
])

# 3.3 Combinador
preprocessor = ColumnTransformer(transformers=[
    ("num", numeric_transformer, numeric_features),
    ("cat", categorical_transformer, categorical_features)
])

# 4. Definir múltiples modelos MLP con diferentes parámetros
mlp_params = [
    {
        'hidden_layer_sizes': (64, 32),
        'activation': 'relu',
        'solver': 'adam',
        'learning_rate': 'adaptive'
    },
    {
        'hidden_layer_sizes': (128, 64),
        'activation': 'tanh',
        'solver': 'adam',
        'learning_rate': 'constant'
    },
    {
        'hidden_layer_sizes': (32, 32, 32),
        'activation': 'relu',
        'solver': 'sgd',
        'learning_rate': 'adaptive'
    },
    {
        'hidden_layer_sizes': (100, 50, 25),
        'activation': 'tanh',
        'solver': 'lbfgs',
        'learning_rate': 'constant'
    },
    {
        'hidden_layer_sizes': (80, 40),
        'activation': 'relu',
        'solver': 'adam',
        'learning_rate': 'invscaling'
    }
]

# 5. División train/test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 6. Entrenar y evaluar todos los modelos
best_mse = float('inf')
best_model = None
best_predictions = None
best_r2 = None

# Configuración de CodeCarbon
pue = 1.12
country_iso_code = 'ESP'
region='ESP'
cloud_provider='gcp'
cloud_region='europe-southwest1'
country_2letter_iso_code = 'ES'
measure_power_secs = 30
save_to_file=False

# Configuración para el primer tracker
tracker1 = OfflineEmissionsTracker(
        country_iso_code=country_iso_code,
        region=region,
        cloud_provider=cloud_provider,
        cloud_region=cloud_region,
        country_2letter_iso_code=country_2letter_iso_code,
        measure_power_secs=measure_power_secs,
        pue=pue,
        save_to_file=save_to_file
        )

tracker1.start()


for i, params in enumerate(mlp_params, 1):
    # Crear pipeline con los parámetros actuales de MLP
    current_mlp = MLPRegressor(
        **params,
        alpha=0.0001,
        max_iter=500,
        random_state=42
    )
    
    current_pipeline = Pipeline(steps=[
        ("preprocesador", preprocessor),
        ("modelo", current_mlp)
    ])
    
    # Entrenar y evaluar
    current_pipeline.fit(X_train, y_train)
    y_pred = current_pipeline.predict(X_test)
    current_mse = mean_squared_error(y_test, y_pred)
    current_r2 = r2_score(y_test, y_pred)
    
    log(f"\nResultados del Modelo {i}:")
    log(f"Parámetros: {params}")
    log(f"Error Cuadrático Medio: {current_mse:.4f}")
    log(f"R²: {current_r2:.4f}")
    
    # Actualizar mejor modelo si el actual es mejor
    if current_mse < best_mse:
        best_mse = current_mse
        best_model = current_pipeline
        best_predictions = y_pred
        best_r2 = current_r2

emissions1 = tracker1.stop()

log("\n=== Resultados del Mejor Modelo ===")
log(f"Mejor Error Cuadrático Medio: {best_mse:.4f}")
log(f"Mejor R²: {best_r2:.4f}")
log(f"Emisiones estimadas: {emissions1:.4f} kg CO₂")

# Predicciones de ejemplo
ejemplo_params = pd.DataFrame([
    {'procedencia': 'Paris, France', 'escala': 0, 'distancia': 200, 'clase': 'Eco'},
    {'procedencia': 'Barcelona, Spain', 'escala': 1, 'distancia': 321, 'clase': 'EcoPlus'},
    {'procedencia': 'Berlin, Germany', 'escala': 0, 'distancia': 4123, 'clase': 'Business'}
])

predicciones = best_model.predict(ejemplo_params)

log("\n=== Predicciones con Parámetros Específicos ===")
for i, (params, pred) in enumerate(zip(ejemplo_params.to_dict('records'), predicciones)):
    log(f"\nCaso {i+1}:")
    for key, value in params.items():
        log(f"{key}: {value}")
    log(f"Huella de carbono estimada: {pred:.2f} kg CO₂")

"""
SCRIPT 3.1: DATASET DE MULTIMEDIA
"""

import numpy as np
import pandas as pd

# Número de observaciones
n = 2103

# Semilla para reproducibilidad
np.random.seed(42)

# Parámetros previos
screens = np.random.randint(1, 21, size=n)
speakers = np.random.randint(2, 51, size=n)
size_noise = np.random.normal(0, 2, size=n)
total_size = np.round(screens * 5 + speakers * 0.5 + size_noise, 2)
distance = np.round(np.random.uniform(10, 3000, size=n), 2)
power_noise = np.random.normal(0, 5, size=n)
power_kw = np.round(np.clip(speakers * 2 + power_noise, 0.1, None), 2)

# Nuevo parámetro: duración del concierto (horas, entre 1 y 6)
duration = np.round(np.random.uniform(1, 6, size=n), 2)

# Coeficientes de emisión
coef_elec = 0.19338  # por kWh
coef_truck = 0.89061  # por km

# Cálculo de huella de carbono con duración
# Emisión electricidad: coef_elec * power_kw * duration
# Emisión transporte: coef_truck * distance
base_cf = coef_elec * power_kw * duration + coef_truck * distance
noise_cf = np.random.normal(0, base_cf * 0.05)  # 5% de ruido
carbon_footlog = np.round(base_cf + noise_cf, 2)

# Construir DataFrame
df = pd.DataFrame({
    'número de pantallas': screens,
    'número de altavoces': speakers,
    'tamaño total': total_size,
    'distancia de viaje': distance,
    'kWh de medios': power_kw,
    'horas de uso': duration,
    'huella': carbon_footlog
})

df.to_excel('huella_carbono_multimedia.xlsx', index=False)

"""
SCRIPT 3.2: MODELO DE MULTIMEDIA
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

class _DummyTracker:          # fallback si codecarbon no está disponible
    def start(self):          # mantiene la misma interfaz
        pass
    def stop(self):
        return 0.0
    
# Intentar importar codecarbon
use_tracker = False
try:
    from codecarbon import EmissionsTracker
    use_tracker = True
except ImportError:
    log("Advertencia: codecarbon no está instalado. Se omite medición de emisiones.")


df = pd.read_excel('huella_carbono_multimedia.xlsx')

# Preparar datos
X = df.drop('huella', axis=1)
y = df['huella']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Definir modelos RFR
models = {
    'RFR_default': RandomForestRegressor(random_state=42),
    'RFR_100_estimators': RandomForestRegressor(n_estimators=100, random_state=42),
    'RFR_200_estimators_maxdepth10': RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42),
    'RFR_min_samples_leaf5': RandomForestRegressor(n_estimators=100, min_samples_leaf=5, random_state=42),
    'RFR_max_features_sqrt': RandomForestRegressor(n_estimators=100, max_features='sqrt', random_state=42)
}

# Iniciar rastreador
if use_tracker:                                   # variable que ya existía
    tracker = EmissionsTracker(output_dir="codecarbon_logs",
                               project_name="RF_Multimedia")
else:
    tracker = _DummyTracker()
tracker.start()

# Entrenar y evaluar
best_mse = float('inf')
best_model_name = None
best_model = None
best_predictions = None
best_r2 = None

for name, model in models.items():
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    current_mse = mean_squared_error(y_test, preds)
    current_r2 = r2_score(y_test, preds)
    
    log(f"\nResultados del Modelo: {name}")
    log(f"Error Cuadrático Medio: {current_mse:.4f}")
    log(f"R²: {current_r2:.4f}")
    
    if current_mse < best_mse:
        best_mse = current_mse
        best_model_name = name
        best_model = model
        best_predictions = preds
        best_r2 = current_r2

emissions = tracker.stop()

log("\n=== Resultados del Mejor Modelo ===")
log(f"Modelo: {best_model_name}")
log(f"Mejor Error Cuadrático Medio: {best_mse:.4f}")
log(f"Mejor R²: {best_r2:.4f}")
log(f"Emisiones estimadas: {emissions:.4f} kg CO₂")

"""
SCRIPT 4: CARBON COMPENSATION CALCULATOR
"""
from pathlib import Path

def _read_emission(path: str) -> float:
    """
    Devuelve el valor numérico que hay en `path`
    (0.0 si no existe o el contenido no es convertible a float).
    """
    try:
        return float(Path(path).read_text().strip())
    except (FileNotFoundError, ValueError):
        return 0.0

EM_22 = _read_emission("emissions_22.txt")   # generado por SCRIPT 2.2
EM_32 = _read_emission("emissions_32.txt")   # generado por SCRIPT 3.2
HUELLA_MODELOS = EM_22 + EM_32
log(f"• Huella combinada de modelos: {HUELLA_MODELOS:.4f} kg CO₂")


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
        # Intentar obtener la huella de carbono de los modelos de las secciones 2.2 y 3.2
        from sklearn.linear_model import LinearRegression
        import pandas as pd
        import numpy as np
        
        # Cargar los datos de ambas secciones
        df_2_2 = pd.read_csv("caso3_dummy.csv")  # Datos de sección 2.2
        df_3_2 = pd.read_csv("caso3_dummy.csv")  # Datos de sección 3.2
        
        # Entrenar modelo para sección 2.2
        try:
            X_2_2 = df_2_2.drop(["nº_observación", "huella_CO2_kg"], axis=1)
            y_2_2 = df_2_2["huella_CO2_kg"]
            lr_2_2 = LinearRegression()
            lr_2_2.fit(X_2_2, y_2_2)
            huella_co2_2_2 = y_2_2.mean()
        except Exception as e:
            log(f"Error al cargar el modelo de sección 2.2: {e}")
            huella_co2_2_2 = 3750  # Mitad del valor por defecto
        
        # Entrenar modelo para sección 3.2
        try:
            X_3_2 = df_3_2.drop(["nº_observación", "huella_CO2_kg"], axis=1)
            y_3_2 = df_3_2["huella_CO2_kg"]
            lr_3_2 = LinearRegression()
            lr_3_2.fit(X_3_2, y_3_2)
            huella_co2_3_2 = y_3_2.mean()
        except Exception as e:
            log(f"Error al cargar el modelo de sección 3.2: {e}")
            huella_co2_3_2 = 3750  # Mitad del valor por defecto
        
        # Combinar las huellas de carbono de ambas secciones
        huella_co2 = huella_co2_2_2 + huella_co2_3_2
        
    except Exception as e:
        log(f"Error al cargar los datos: {e}")
        log("Usando valor por defecto de 7500 kg CO2")
        huella_co2 = HUELLA_MODELOS
        if huella_co2 == 0.0:
            raise SystemExit(
                "No se han encontrado emissions_22.txt ni emissions_32.txt.\n"
                "Ejecuta primero los scripts 2.2 y 3.2 para generar esos archivos."
            )    
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