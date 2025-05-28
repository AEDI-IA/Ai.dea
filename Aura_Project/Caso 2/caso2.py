"""
SCRIPT 1: DISTANCIAS
"""

from __future__ import annotations

import json
import os
import time
from functools import lru_cache
from itertools import combinations
import networkx as nx
import osmnx as ox
import pandas as pd
from geopy.distance import geodesic
import mlcroissant as mlc
import logging
from datetime import datetime
#---------------- 1) LISTAS DE CIUDADES Y PAISES ----------------

# ── Ajustes globales OSMnx ───────────────────────────────────
ox.settings.overpass_settings = '[out:json][timeout:600]'     # 10 min
ox.settings.overpass_endpoint = 'https://overpass.kumi.systems/api/interpreter'
ox.settings.max_query_area_size = 2e7     # 20.000 km² – evita troceos excesivos
ox.settings.use_cache = True              # guarda la respuesta en disco ~/.cache
ox.settings.log_console = True            # ver logs en pantalla

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


# ── Peninsulares e insulares ─────────────────────────────────────────

CONTINENTAL_EUROPEAN_CITIES = {'A Coruña, Spain': ['LECO', 'LEST'], 'Aachen, Germany': ['ETNG', 'EHBK'], 'Aalborg, Denmark': ['EKYT', 'EKSN'], 'Aarhus, Denmark': ['EKAH', 'EKKA'], 
                               'Aiberdeen, United Kingdom': ['EGPD', 'EGPN'], 'Aix-en-Provence, France': ['LFML', 'LFMY'], 'Almetevsk, Russia': ['UWKB', 'UWKE'], 'Alacant, Spain': ['LEAL', 'LELC'], 
                               'Albacete, Spain': ['LEAB', 'LERI'], 'Alcalá de Henares, Spain': ['LETO', 'LEMD'], 'Alchevsk, Ukraine': ['RU-0282', 'RU-0211'], 'Alcobendas, Spain': ['LEMD', 'LETO'], 
                               'Alcorcón, Spain': ['LECU', 'LEGT'], 'Algeciras, Spain': ['LXGB', 'GMTN'], 'Almada, Portugal': ['LPPT', 'LPMT'], 'Almere, Netherlands': ['EHLE', 'EHAM'], 
                               'Almería, Spain': ['LEAM', 'LEGA'], 'Amadora, Portugal': ['LPPT', 'LPCS'], 'Amersfoort, Netherlands': ['EHLE', 'EHDL'], 'Amiens, France': ['LFAY', 'LFOI'], 
                               'Anderlecht, Belgium': ['EBBR', 'EBBE'], 'Angers, France': ['LFJR', 'LFOV'], 'Antwerpen, Belgium': ['EBAW', 'EHWO'], 'Apeldoorn, Netherlands': ['EHDL', 'EHLE'], 
                               'Arad, Romania': ['LRAR', 'LRTR'], 'Argenteuil, France': ['LFPB', 'LFPV'], 'Arkhangelsk, Russia': ['ULAA', 'ULAH'], 'Armavir, Russia': ['URMT', 'RU-10062'], 
                               'Arnhem, Netherlands': ['EHDL', 'EHVK'], 'Arzamas, Russia': ['RU-0043', 'UWGG'], "Astrakhan', Russia": ['URWA', 'RU-0303'], 'Athens, Greece': ['LGEL', 'LGAV'], 
                               'Atyrau, Kazakhstan': ['UATG', "NaN"], 'Augsburg, Germany': ['EDMA', 'ETSL'], 'Babruisk, Babrujsk, Belarus': ['UMNB', 'UMOO'], 'Bacau, Romania': ['LRBC', 'LRIA'], 
                               'Badajoz, Spain': ['LEBZ', 'LPEV'], 'Badalona, Spain': ['LEBL', 'ES-0109'], 'Baia Mare, Romania': ['LRBM', 'LRSM'], 'Baki, Azerbaijan': ['AZ-0001', 'UBBB'], 
                               'Balakovo, Russia': ['UWSB', 'RU-3709'], 'Balashikha, Russia': ['UUMU', 'RU-10054'], 'Banja Luka, Bosnia and Herzegovina': ['LQBK', 'LQTZ'], 'Barakaldo, Spain': ['LEBB', 'LEVT'], 
                               'Baranavichy, Belarus': ['UMMA', 'BY-0006'], 'Barcelona, Spain': ['LEBL', 'ES-0109'], 'Bari, Italy': ['LIBD', 'LIBV'], 'Barysau, Belarus': ['UMMS', 'UMOO'], 
                               'Basel, Switzerland': ['LFSB', 'LSZG'], 'Bataisk, Russia': ['RU-0372', 'URRP'], 'Belgorod, Russia': ['UUOB', 'UKHH'], 'Beograd, Serbia': ['LYBE', 'LYBT'], 'Berdiansk, Ukraine': ['UKDB', 'UKCM'], 
                               'Berezniki, Russia': ["NaN", "NaN"], 'Bergen, Norway': ['ENBR', 'ENSO'], 'Bergisch Gladbach, Germany': ['EDDK', 'ETNN'], 'Berlin, Germany': ['EDDB', 'ETSH'], 'Bern, Switzerland': ['LSZB', 'LSZG'], 
                               'Besançon, France': ['LFQW', 'LFGJ'], 'Bialystok, Poland': ['UMMG', 'UMBB'], 'Bielefeld, Germany': ['EDLP', 'ETHB'], 'Bielsko-Biala, Poland': ['EPKK', 'LKMT'], 
                               'Bila Tserkva, Ukraine': ['UA-0025', 'UKKK'], 'Bilbo, Spain': ['LEBB', 'LEVT'], 'Birmingham, United Kingdom': ['EGBB', 'EGBE'], 'Blackburn, United Kingdom': ['EGNO', 'EGNH'], 
                               'Blackpool, United Kingdom': ['EGNH', 'EGNO'], 'Bochum, Germany': ['EDLW', 'EDDL'], 'Bologna, Italy': ['LIPE', 'LIPK'], 'Bolos, Greece': ['LGBL', 'LGSK'], 
                               'Bolton, United Kingdom': ['EGCC', 'EGNO'], 'Bolzano, Italy': ['LIPB', 'LOWI'], 'Bonn, Germany': ['EDDK', 'ETNN'], 'Bordeaux, France': ['LFBD', 'LFCH'], 
                               'Botosani, Romania': ['LRSV', 'UKLN'], 'Bottrop, Germany': ['EDDL', 'EDLN'], 'Boulogne-Billancourt, France': ['LFPV', 'LFPN'], 'Bournemouth, United Kingdom': ['EGHH', 'EGHI'], 
                               'Bradford, United Kingdom': ['EGNM', 'EGXG'], 'Braga, Portugal': ['LPBR', 'LPVL'], 'Braila, Romania': ['LR79', 'LRTC'], 'Brasov, Romania': ['LRBV', 'LR82'], 'Bratislava, Slovakia': ['LZIB', 'LZMC'], 
                               'Braunschweig, Germany': ['EDVE', 'ETHC'], 'Breda, Netherlands': ['EHGR', 'EHWO'], 'Bremen, Germany': ['EDDW', 'ETND'], 'Bremerhaven, Germany': ['ETMN', 'EDDW'], 'Brescia, Italy': ['LIPO', 'LIPL'], 
                               'Brest (Finisterre), France': ['LFRB', 'LFRL'], 'Brest, Belarus': ['UMBB', 'BY-0006'], 'Briansk, Russia': ['UUBP', 'RU-0240'], 'Brighton & Hove, United Kingdom': ['EGKA', 'EGKK'], 
                               'Bristol, United Kingdom': ['EGGD', 'EGDY'], 'Brno, Czechia': ['LKTB', 'LKNA'], 'Brugge, Belgium': ['EBOS', 'EBFN'], 'Bruxelles - Brussel, Belgium': ['EBBR', 'EBBE'], 'Bucuresti, Romania': ['LRBS', 'LROP'], 
                               'Budapest, Hungary': ['LHBP', 'LHTL'], 'Burgas, Bulgaria': ['LBBG', 'BG-JAM'], 'Burgos, Spain': ['LEBG', 'LEVT'], 'Buzau, Romania': ['LR82', 'LR79'], 'Bydgoszcz, Poland': ['EPBY', 'EPIR'], 
                               'Bytom, Poland': ['EPKT', 'EPKK'], 'Bérgamo, Italy': ['LIME', 'LIML'], 'Caen, France': ['LFRK', 'LFRG'], 'Cambridge, United Kingdom': ['EGSC', 'EGUN'], 'Cardiff, United Kingdom': ['EGFF', 'EGDX'], 
                               'Cartagena, Spain': ['LELC', 'LEMI'], 'Castellón de la Plana, Spain': ['LECH', 'LEVC'], 'Charleroi, Belgium': ['EBCI', 'EBFS'], 'Cheboksary, Russia': ['UWKS', 'UWKJ'], 
                               'Chelmsford, United Kingdom': ['EGSS', 'EGMC'], 'Chemnitz, Germany': ['EDAC', 'EDDC'], 'Cherepovets, Russia': ['ULWC', 'RU-10056'], 'Cherkasy, Ukraine': ['UKKE', 'UA-0025'], 
                               'Cherkessk, Russia': ['URMM', 'URMT'], 'Chernigiv, Ukraine': ['UA-0005', 'UKBB'], 'Chernivtsi, Ukraine': ['UKLN', 'LRSV'], 'Chisinau, Moldavia': ['LUKK', 'LUTR'], 
                               'Chorzów, Poland': ['EPKT', 'EPKK'], 'St Albans, United Kingdom': ['EGGW', 'EGWU'], 'Westminster, United Kingdom': ['EGLC', 'EGWU'], 'Clermont-Ferrand, France': ['LFLC', 'LFLV'], 
                               'Cluj-Napoca, Romania': ['LRCL', 'LRCT'], 'Colchester, United Kingdom': ['EGUW', 'EGMC'], 'Constanta, Romania': ['LRCK', 'LR80'], 'Coventry, United Kingdom': ['EGBE', 'EGBB'], 
                               'Coímbra, Portugal': ['LPCO', 'LPMR'], 'Craiova, Romania': ['LRCV', 'LBPL'], 'Crawley, United Kingdom': ['EGKK', 'EGKB'], 'Czestochowa, Poland': ['EPKT', 'EPLK'], 'Cádiz, Spain': ['LERT', 'LEJR'], 
                               'Córdoba, Spain': ['LEBA', 'LEMO'], 'Dabrowa Gornicza, Poland': ['EPKT', 'EPKK'], 'Darmstadt, Germany': ['EDFE', 'EDDF'], 'Debrecen, Hungary': ['LHDC', 'LROD'], 'Den Haag, Netherlands': ['EHRD', 'EHAM'], 
                               'Derbent, Russia': ['URML', 'UBBY'], 'Derby, United Kingdom': ['EGNX', 'EGBN'], 'Dijon, France': ['LFSD', 'LFGJ'], 'Dimitrovgrad, Russia': ['UWLW', 'UWWW'], 'Dnipro, Ukraine': ['UA-0005', 'UKKM'], 
                               'Dniprodzerzhinsk, Ukraine': ["NaN", "NaN"], 'Donetsk, Russia': ['RU-0282', 'URRP'], 'Donostia, Spain': ['LESO', 'LFBZ'], 'Dordrecht, Netherlands': ['EHRD', 'EHGR'], 'Dortmund, Germany': ['EDLW', 'EDDL'], 
                               'Dos Hermanas, Spain': ['LEZL', 'LEMO'], 'Dresden, Germany': ['EDDC', 'EDAC'], 'Duisburg, Germany': ['EDDL', 'EDLN'], 'Dundee, United Kingdom': ['EGPN', 'EGQL'], 'Durrës, Albania': ['LATI', 'LAKV'], 
                               'Dzerzhinsk, Russia': ['UWGG', 'RU-0217'], 'Düsseldorf, Germany': ['EDDL', 'EDLN'], 'Ede, Netherlands': ['EHDL', 'EHLE'], 'Edinburgh, United Kingdom': ['EGPH', 'EGQL'], 'Eindhoven, Netherlands': ['EHEH', 'EHBD'], 
                               'Elblag, Poland': ['EPMB', 'EPGD'], "Elektrostal', Russia": ['UUMU', 'UUBW'], 'Elets, Russia': ['RU-0016', 'UUOL'], 'Elista, Russia': ['URWI', "NaN"], 'Elx, Spain': ['LEAL', 'LELC'], 
                               'Emmen, Netherlands': ['EHGG', 'EHTW'], "Engel's, Russia": ['XRMU', 'URMG'], 'Enschede, Netherlands': ['EHTW', 'EDDG'], 'Erewan, Armenia': ['UDYE', 'UDYZ'], 'Erfurt, Germany': ['EDDE', 'EDGE'], 'Erlangen, Germany': ['EDDN', 'EDQA'], 
                               'Espoo, Finland': ['EFHK', 'EETN'], 'Essen, Germany': ['EDDL', 'EDLW'], 'Exeter, United Kingdom': ['EGTE', 'EGDC'], 'Ferrara, Italy': ['LIPE', 'LIPK'], 'Florence, Italy': ['LIRQ', 'LIQS'], 
                               'Foggia, Italy': ['LIBF', 'LIBA'], 'Forlì, Italy': ['LIPK', 'LIPC'], 'Frankfurt am Main, Germany': ['EDDF', 'EDFE'], 'Freiburg im Breisgau, Germany': ['LFGA', 'EDTL'], 'Fuenlabrada, Spain': ['LEGT', 'LECU'], 
                               'Fürth, Germany': ['EDDN', 'EDQA'], 'G@nc@, Azerbaijan': ["NaN", "NaN"], 'Galati, Romania': ['LUCH', 'UA-0028'], 'Gdansk, Poland': ['EPGD', 'EPMB'], 'Gdynia, Poland': ['EPGD', 'EPCE'], 
                               'Gelsenkirchen, Germany': ['EDDL', 'EDLW'], 'Genève, Switzerland': ['LSGG', 'LFLI'], 'Getafe, Spain': ['LEGT', 'LECU'], 'Ghent, Belgium': ['EBKT', 'EBCV'], 'Gijón, Spain': ['LEAS', 'LELN'], 
                               'Giugliano de Campania, Italy': ['LIRN', 'LIRM'], 'Glasgow, United Kingdom': ['EGPF', 'EGPK'], 'Gliwice, Poland': ['EPKT', 'LKMT'], 'Gloucester, United Kingdom': ['EGBJ', 'EGVA'], 
                               "Gomel', Homiel, Belarus": ['UMGG', 'UMNB'], 'Gorlivka, Ukraine': ['RU-0211', 'URRT'], 'Gorzów Wielkopolski, Poland': ['EPZG', 'EPMI'], 'Gothenburg, Sweden': ['ESGP', 'ESGG'], 
                               'Granada, Spain': ['LEGA', 'LEGR'], 'Graz, Austria': ['LOWG', 'LOXZ'], 'Grenoble, France': ['LFLS', 'LFLB'], 'Grodna, Hrodna, Belarus': ['UMMG', 'EYVI'], 'Groningen, Netherlands': ['EHGG', 'EHLW'],
                                'Groznyi, Russia': ['URMG', 'XRMU'], 'Gyor, Hungary': ['LHPR', 'LZIB'], 'Gyowmri, Armenia': ["NaN", "NaN"], 'Génova, Italy': ['LIMJ', 'LIMR'], 'Göttingen, Germany': ['EDVK', 'ETHF'], 
                                'Haarlem, Netherlands': ['EHAM', 'EHRD'], 'Haarlemmermeer, Netherlands': ['EHAM', 'EHRD'], 'Hagen, Germany': ['EDLW', 'EDDL'], 'Halle, Germany': ['EDDP', 'EDUZ'], 'Hamburg, Germany': ['EDDH', 'EDHI'], 
                                'Hamm, Germany': ['ETAD', 'ELLX'], 'Hannover, Germany': ['EDDV', 'ETNW'], 'Heidelberg, Germany': ['EDFM', 'EDFE'], 'Heilbronn, Germany': ['EDTY', 'EDDS'], 'Helsinki, Finland': ['EFHK', 'EETN'], 
                                'Herne, Germany': ['EDLW', 'EDDL'], 'Huddersfield, United Kingdom': ['EGNM', 'EGXG'], 'Huelva, Spain': ['LERT', 'LPFR'], "Iaroslavl', Russia": ['UUBA', 'UUBK'], 'Iasi, Romania': ['LRIA', 'LUBL'], 
                                'Ievpatoriia, Russia': ["NaN", "NaN"], 'Ingolstadt, Germany': ['ETSI', 'ETSN'], 'Innsbruck, Austria': ['LOWI', 'LIPB'], 'Ioannina, Greece': ['LGIO', 'LGKR'], 'Ioshkar-Ola, Russia': ['UWKJ', 'RU-4421'], 
                                'Ipswich, United Kingdom': ['EGUW', 'EGXH'], 'Istanbul, Turquía': ['LTBA', 'LTBX'], "Ivano-Frankivs'k, Ukraine": ['UKLI', 'UKLL'], 'Ivanovo, Russia': ['RU-5672', 'UUBI'], 'Izhevsk, Russia': ['USII', "NaN"], 
                                'Jaén, Spain': ['LEGR', 'LEGA'], 'Jena, Germany': ['EDDE', 'EDAC'], 'Jerez de la Frontera, Spain': ['LEJR', 'LERT'], 'Jyväskylä, Finland': ['EFJY', 'EFHA'], 'Kaliningrad, Russia': ['RU-0028', 'UMKK'], 
                                'Kaluga, Russia': ['UUBC', 'RU-3686'], 'Kamyshin, Russia': ['XRWL', "NaN"], 'Karlsruhe, Germany': ['EDSB', 'EDFM'], 'Kassel, Germany': ['EDVK', 'ETHF'], 'Katowice, Poland': ['EPKT', 'EPKK'], 
                                'Kaunas, Lithuania': ['EYKA', 'EYKD'], "Kazan', Russia": ['UWKG', 'UWKD'], 'Kerch, Russia': ['UUEE', 'UUMO'], 'Khania, Greece': ['LGSA', 'LGIR'], 'Kharkiv, Ukraine': ['UKHH', 'UUOB'], 
                                'Khasaviurt, Russia': ['XRMU', 'URMG'], 'Kherson, Ukraine': ['UKOH', 'UKFY'], 'Khimki, Russia': ['UUEE', 'UUWW'], "Khmel'nits'kii, Ukraine": ["NaN", "NaN"], 'Kiel, Germany': ['EDHK', 'ETNH'], 
                                'Kielce, Poland': ['EPRA', 'EPTM'], 'Kingston upon Hull, United Kingdom': ['EGNJ', 'EGXG'], 'Kirov, Russia': ['USKK', "NaN"], 'Kirovograd, Ukraine': ['UKDR', 'UKKE'], 'Kislovodsk, Russia': ['URMM', 'URMN'], 
                                'Kiyiv, Ukraine': ['UKKK', 'UKBB'], 'Klaipeda, Lithuania': ['EYPA', 'EVLA'], 'Koblenz, Germany': ['ETSB', 'EDFH'], 'Kolomna, Russia': ['UUMT', 'UUBW'], 'Koroliov, Russia': ['UUMU', 'UUEE'], 
                                'Kosice, Slovakia': ['LZKZ', 'UKLU'], 'Kostroma, Russia': ['UUBA', 'RU-5672'], 'Koszalin, Poland': ['EPSN', 'EPMI'], 'Kovrov, Russia': ['RU-10048', 'UUBI'], 'Kragujevats, Serbia': ["NaN", "NaN"], 
                                'Kraków, Poland': ['EPKK', 'EPKT'], "Kramators'k, Ukraine": ["NaN", "NaN"], 'Krasnodar, Russia': ['RU-0090', 'URKK'], 'Krefeld, Germany': ['EDLN', 'EDDL'], 'Kremenchuk, Ukraine': ['UKKE', 'UKDR'], 
                                'Krivii rig, Ukraine': ["NaN", "NaN"], 'Kuopio, Finland': ['EFKU', 'EFVR'], 'Kursk, Russia': ['UUOK', 'UUOB'], 'Köln, Germany': ['EDDK', 'ETNN'], 'København, Denmark': ['EKCH', 'EKRK'], 
                                "L'Hospitalet de Llobregat, Spain": ['LEBL', 'ES-0109'], "L'viv, Ukraine": ['UKDD', 'UKDE'], 'Lahti, Finland': ['EFUT', 'EFPR'], 'Larisa, Greece': ['LGBL', 'LGKZ'], 'Latina, Italy': ['LIRL', 'LIRA'], 
                                'Lausanne, Switzerland': ['LSMP', 'LFLI'], 'Le Havre, France': ['LFOH', 'LFRG'], 'Le Mans, France': ['LFRM', 'LFJR'], 'Leeds, United Kingdom': ['EGNM', 'EGXG'], 'Leganés, Spain': ['LECU', 'LEGT'], 
                                'Leicester, United Kingdom': ['EGNX', 'EGBN'], 'Leiden, Netherlands': ['EHRD', 'EHAM'], 'Leipzig, Germany': ['EDDP', 'EDAC'], 'Lemesos, Cyprus': ['LCRA', 'LCPH'], 'Leukosia, Cyprus': ['LCEN', 'LCGK'], 
                                'Leverkusen, Germany': ['EDDK', 'ETNN'], 'León, Spain': ['LELN', 'LEAS'], 'Liberec, Czechia': ['EDBR', 'LKVO'], 'Lille, France': ['LFQQ', 'EBKT'], 'Limoges, France': ['LFBL', 'LFBX'], 
                                'Linköping, Sweden': ['ESSL', 'ESCF'], 'Linz, Austria': ['LOWL', 'LOWS'], 'Lipetsk, Russia': ['RU-0016', 'UUOL'], 'Lisboa, Portugal': ['LPPT', 'LPMT'], 'Liubertsy, Russia': ['RU-10054', 'UUBW'], 
                                'Liverpool, United Kingdom': ['EGGP', 'EGNR'], 'Livorno, Italy': ['LIRJ', 'LIRS'], 'Liège, Belgium': ['EBLG', 'EHBK'], 'Ljbljana, Slovenia': ["NaN", "NaN"], 'Lleida, Spain': ['LEDA', 'LERS'], 
                                'Lodz, Poland': ['EPLL', 'EPLK'], 'Logroño, Spain': ['LELO', 'LEVT'], 'London, United Kingdom': ['EGLC', 'EGWU'], 'Lublin, Poland': ['EPLB', 'EPDE'], 'Ludwigshafen am Rhein, Germany': ['EDFM', 'EDFE'], 
                                "Lugans'k, Russia": ["NaN", "NaN"], 'Luton, United Kingdom': ['EGGW', 'EGTC'], "Luts'k, Ukraine": ["NaN", "NaN"], 'Luxembourg, Luxembourg': ['ELLX', 'LFQE'], 'Lyon, France': ['LFLY', 'LFLL'], 
                                'Lübeck, Germany': ['EDHL', 'EDDH'], 'Maastricht, Netherlands': ['EHBK', 'ETNG'], 'Madrid, Spain': ['LECU', 'LEMD'], 'Magdeburg, Germany': ['EDUZ', 'EDVE'], 'Magiliou, Mahilou, Belarus': ["NaN", "NaN"], 
                                'Maikop, Russia': ['RU-10062', 'URKK'], 'Mainz, Germany': ['ETOU', 'EDFZ'], 'Makhachkala, Russia': ['URML', 'XRMU'], 'Makiyivka, Ukraine': ['RU-0211', 'UKCM'], 'Malmö, Sweden': ['EKCH', 'ESMS'], 
                                'Manchester, United Kingdom': ['EGCC', 'EGGP'], 'Mannheim, Germany': ['EDFM', 'EDFE'], 'Marbella, Spain': ['LEMG', 'LXGB'], 'Marseille, France': ['LFML', 'LFMQ'], 'Mataró, Spain': ['LEBL', 'ES-0109'], 
                                'Mazyr, Mazyr, Belarus': ['UMNB', 'UMGG'], "Melitopol', Ukraine": ['UA-0020', 'UKDB'], 'Metz, France': ['LFJL', 'LFQE'], 'Middlesbrough, United Kingdom': ['EGNV', 'EGXE'], 
                                'Mikolayiv, Ukraine': ['UKON', 'UKOH'], 'Milan, Italy': ['LIML', 'LILN'], 'Milton Keynes, United Kingdom': ['EGTC', 'EGGW'], 'Ming@cevir, Azerbaijan': ["NaN", "NaN"], 'Minsk, Belarus': ['UMMS', 'UMMA'], 
                                'Miskolc, Hungary': ['LZKZ', 'LHDC'], 'Modena, Italy': ['LIPE', 'LIMP'], 'Moers, Germany': ['EDDL', 'EDLN'], 'Montpellier, France': ['LFMT', 'LFTW'], 'Montreuil, France': ['LFAT', 'LFOI'], 
                                'Monza, Italy': ['LIML', 'LILN'], 'Moscow, Russia': ['UUMO', 'UUWW'], 'Mulhouse, France': ['LFSB', 'LFGA'], 'Murcia, Spain': ['LERI', 'LEMI'], 'Murom, Russia': ['RU-0043', 'RU-10048'], 
                                'Mytishchi, Russia': ['UUMU', 'UUEE'], 'Málaga, Spain': ['LEMG', 'LEGR'], 'Móstoles, Spain': ['LECU', 'LEGT'], 'Mönchengladbach, Germany': ['EDLN', 'EDDL'], 'Mülheim an der Ruhr, Germany': ['EDDL', 'EDLN'], 
                                'München, Germany': ['EDMO', 'EDDM'], 'Münster, Germany': ['EDDG', 'EDLW'], 'Naberezhnye Chelny, Russia': ['UWKE', 'UWKB'], "Nal'chik, Russia": ['URMN', 'URMO'], 'Namur, Belgium': ['EBCI', 'EBFS'], 
                                'Nancy, France': ['LFSN', 'LFSO'], 'Nantes, France': ['LFRS', 'LFRZ'], 'Napoli, Italy': ['LIRN', 'LIRM'], "Nazran', Russia": ['URMO', 'URMS'], 'Neftekamsk, Russia': ['USII', 'UWKE'], 
                                'Neuss, Germany': ['EDDL', 'EDLN'], 'Nevinnomyssk, Russia': ['URMT', 'URMM'], 'Newcastle upon Tyne, United Kingdom': ['EGNT', 'EGNV'], 'Newport, United Kingdom': ['EGGD', 'EGFF'], 
                                'Nice, France': ['LFMN', 'LFMD'], 'Nijmegen, Netherlands': ['EHVK', 'EHDL'], "Nikopol', Ukraine": ['UA-0047', 'UKDE'], 'Nish, Serbia': ['LYNI', 'BKPR'], 'Nizhnekamsk, Russia': ['UWKE', 'UWKB'], 
                                'Nizhnii Novgorod, Russia': ['RU-0217', 'UWGG'], 'Noginsk, Russia': ['UUMU', 'UUBW'], 'Northampton, United Kingdom': ['EGTC', 'EGBE'], 'Norwich, United Kingdom': ['EGSH', 'EGXH'], 
                                'Nottingham, United Kingdom': ['EGBN', 'EGNX'], 'Novara, Italy': ['LIMN', 'LIMC'], 'Novi Sad, Serbia': ['LYBT', 'LYBE'], 'Novocheboksarsk, Russia': ['UWKS', 'RU-4421'], 
                                'Novocherkassk, Russia': ['URRP', 'RU-0372'], 'Novomoskovsk, Russia': ['RU-10059', 'UUMT'], 'Novorossiisk, Russia': ['URKG', 'RU-0089'], 'Novoshakhtinsk, Russia': ['URRP', 'RU-0372'], 
                                'Nîmes, France': ['LFTW', 'LFMS'], 'Nürnberg, Germany': ['EDDN', 'EDQA'], 'Oberhausen, Germany': ['EDDL', 'EDLN'], 'Obninsk, Russia': ['RU-10053', 'RU-0764'], 'Odense, Denmark': ['EKOD', 'EKSB'], 
                                'Odesa, Ukraine': ['UKOO', 'LUTR'], 'Odintsovo, Russia': ['UUWW', 'UUMO'], 'Offenbach am Main, Germany': ['EDDF', 'EDFE'], "Oktiabr'skii, Russia": ['USCM', "NaN"], 'Oldemburg, Germany': ["NaN", "NaN"], 
                                'Olsztyn, Poland': ['EPSY', 'EPMB'], 'Opole, Poland': ['EPKT', 'EPWR'], 'Oradea, Romania': ['LROD', 'LHDC'], 'Oral, Kazakhstan': ['UARR', "NaN"], 'Orekhovo-Zuevo, Russia': ['UUMU', 'UUBW'], 
                                'Orenburg, Russia': ['UWOO', "NaN"], 'Oriol, Russia': ['UUBP', 'UUOK'], 'Orléans, France': ['LFOJ', 'LFOC'], 'Orsha, Orsa, Belarus': ['BY-0001', 'UMOO'], 'Orsk, Russia': ['UWOR', 'UATT'], 
                                'Oslo, Norway': ['ENGM', 'ENRY'], 'Osnabrück, Germany': ['EDDG', 'ETND'], 'Ostrava, Czechia': ['LKMT', 'LZZI'], 'Oulu, Finland': ['EFOU', 'EFKE'], 'Ourense, Spain': ['LPBG', 'LEVX'], 
                                'Oviedo, Spain': ['LEAS', 'LELN'], 'Oxford, United Kingdom': ['EGTK', 'EGUB'], 'Paderborn, Germany': ['EDLP', 'EDVK'], 'Padova, Italy': ['LIPU', 'LIPS'], 'Pamplona, Spain': ['LEPP', 'LESO'], 
                                'Paris, France': ['LFPV', 'LFPB'], 'Parla, Spain': ['LEGT', 'LECU'], 'Parma, Italy': ['LIMP', 'LIMS'], 'Patra, Greece': ['LGRX', 'LGAD'], 'Pavlograd, Ukraine': ['UKDD', 'UKDE'], 
                                'Penza, Russia': ['UWPP', 'UWPS'], 'Peristeri, Greece': ['LGEL', 'LGAV'], "Perm', Russia": ['USPP', "NaN"], 'Perpiñán, France': ['LFMP', 'LFMK'], 'Perugia, Italy': ['LIRZ', 'LIRV'], 
                                'Pescara, Italy': ['LIBP', 'LIRG'], 'Peterborough, United Kingdom': ['EGXT', 'EGYE'], 'Petrozavodsk, Russia': ['ULPP', 'ULPB'], 'Pforzheim, Germany': ['EDDS', 'EDSB'], 'Piacenza, Italy': ['LIMS', 'LIMP'], 
                                'Piatigorsk, Russia': ['URMM', 'URMN'], 'Pinsk, Pinsk, Belarus': ['BY-0006', 'UMMA'], 'Piraeus, Greece': ['LGEL', 'LGAV'], 'Pitesti, Romania': ['LRCV', 'LROP'], 'Pleven, Bulgaria': ['LBPL', 'LBGO'], 
                                'Plock, Poland': ['EPMO', 'EPLY'], 'Ploiesti, Romania': ['LROP', 'LRBS'], 'Plovdiv, Bulgaria': ['LBPD', 'LBPG'], 'Plymouth, United Kingdom': ['EGHQ', 'EGTE'], 'Plzen, Czechia': ['LKLN', 'LKKV'], 
                                'Podgorica, Montenegro': ['LYPG', 'LYTV'], "Podol'sk, Russia": ['UUMO', 'UUDD'], 'Poltava, Ukraine': ['UKKE', "NaN"], 'Poole, United Kingdom': ['EGHH', 'EGDM'], 'Porto, Portugal': ['LPPR', 'LPVL'], 
                                'Portsmouth, United Kingdom': ['EGHI', 'EGHL'], 'Potsdam, Germany': ['EDDB', 'ETSH'], 'Poznan, Poland': ['EPPO', 'EPKS'], 'Prague, Czechia': ['LKKB', 'LKPR'], 'Prato, Italy': ['LIRQ', 'LIRP'], 
                                'Preston, United Kingdom': ['EGNO', 'EGNH'], 'Prishtina, Kosovo': ['BKPR', 'LWSK'], 'Pskov, Russia': ['ULOO', 'RU-0064'], 'Pécs, Hungary': ['LHPP', 'LHTA'], 'Radom, Poland': ['EPRA', 'EPDE'], 
                                'Ravenna, Italy': ['LIPK', 'LIPC'], 'Reading, United Kingdom': ['EGLK', 'EGUB'], 'Recklinghausen, Germany': ['EDLW', 'EDDL'], 'Regensburg, Germany': ['ETIH', 'ETSI'], 'Reggio di Calabria, Italy': ['LICR', 'LICC'], 
                                "Reggio nell'Emilia, Italy": ['LIMP', 'LIPE'], 'Reims, France': ['LFOK', 'LFQV'], 'Remscheid, Germany': ['EDDL', 'EDDK'], 'Rennes, France': ['LFRN', 'LFRD'], 'Reus, Spain': ['LERS', 'LEDA'], 
                                'Reutlingen, Germany': ['EDDS', 'ETHL'], 'Reykjavík, Iceland': ['BIRK', 'BIKF'], "Riazan', Russia": ['RU-10059', 'UUMT'], 'Riga, Latvia': ['EVRA', 'EVTA'], 'Rijeka, Croatia': ['LDRI', 'LDPL'], 
                                'Rimini, Italy': ['LIPR', 'LIPC'], 'Rivne, Ukraine': ['UKLR', "NaN"], 'Rome, Italy': ['LIRU', 'LIRA'], 'Rostock, Germany': ['ETNL', 'EKMB'], 'Rostov-na-Donu, Russia': ['RU-0372', 'URRP'], 
                                'Rotherham, United Kingdom': ['EGXG', 'EGNM'], 'Rotterdam, Netherlands': ['EHRD', 'EHAM'], 'Rouen, France': ['LFOP', 'LFOE'], 'Ruda Slaska, Poland': ['EPKT', 'EPKK'], 'Ruse, Bulgaria': ['LRBS', 'LBGO'], 
                                'Rybinsk, Russia': ['UUBK', 'RU-10056'], 'Rybnik, Poland': ['LKMT', 'EPKT'], 'Rzeszów, Poland': ['EPRZ', 'UKLL'], 'Saarbrücken, Germany': ['EDDR', 'ETAR'], 'Sabadell, Spain': ['LEBL', 'ES-0109'], 
                                'Saint Helens, United Kingdom': ['EGTK', 'EGUB'], 'Saint Petersburg, Russia': ['RU-0001', 'ULLI'], 'Saint-Denis, France': ['LFPB', 'LFPG'], 'Saint-Étienne, France': ['LFMH', 'LFLY'], 
                                'Salamanca, Spain': ['LESA', 'LEVD'], 'Salavat, Russia': ['UWUU', "NaN"], 'Salerno, Italy': ['LIRI', 'LIRN'], 'Salford, United Kingdom': ['EGCC', 'EGGP'], 'Saligorsk, Salihorsk, Belarus': ['UMMA', 'UMNB'], 
                                'Salzburg, Austria': ['LOWS', 'LOWL'], 'Samara, Russia': ['RU-2344', 'UWWG'], 'Santa Coloma de Gramanet, Spain': ['LEBL', 'ES-0109'], 'Santander, Spain': ['LEXJ', 'LEBB'], 
                                'Sarajevo, Bosnia and Herzegovina': ['LQSA', 'LQTZ'], 'Saransk, Russia': ['UWPS', 'RU-6558'], 'Saratov, Russia': ['RU-8602', 'UWSG'], 'Schaerbeek, Belgium': ['EBBR', 'EBBE'], 
                                'Serpukhov, Russia': ['RU-10053', 'UUDD'], "Sevastopol', Russia": ['UUEE', 'UUMO'], 'Severodvinsk, Russia': ['ULAH', 'ULAA'], 'Seville, Spain': ['LEZL', 'LEMO'], 'Shakhty, Russia': ['URRP', 'RU-0372'], 
                                'Shchiolkovo, Russia': ["NaN", "NaN"], 'Sheffield, United Kingdom': ['EGXG', 'EGCC'], 'Sibiu, Romania': ['LRSB', 'LRTM'], "Sieverodonets'k, Ukraine": ["NaN", "NaN"], "Simferopol', Russia": ["NaN", "NaN"], 
                                'Skopje, North Macedonia': ['LWSK', 'BKPR'], 'Slough, United Kingdom': ['EGLL', 'EGWU'], "Slov'ians'k, Ukraine": ["NaN", "NaN"], 'Smolensk, Russia': ['RU-10076', 'RU-4609'], 'Sochi, Russia': ['URSS', 'UG0U'], 
                                'Sofiia, Bulgaria': ["NaN", "NaN"], 'Solingen, Germany': ['EDDL', 'EDDK'], 'Sosnowiec, Poland': ['EPKT', 'EPKK'], 'Southampton, United Kingdom': ['EGHI', 'EGHH'], 'Southend-on-Sea, United Kingdom': ['EGMC', 'EGLC'], 
                                'Split, Croatia': ['LDSP', 'LDSB'], 'Stara Zagora, Bulgaria': ['BG-JAM', 'LBPD'], 'Staryi Oskol, Russia': ['RU-8363', 'UUOO'], 'Stavanger, Norway': ['ENZV', 'ENHD'], "Stavropol', Russia": ['RU-0128', 'URMM'], 
                                'Sterlitamak, Russia': ['UWUU', "NaN"], 'Stockholm, Sweden': ['ESSB', 'ESSA'], 'Stockport, United Kingdom': ['EGCC', 'EGGP'], 'Stoke-on-Trent, United Kingdom': ['EGCC', 'EGOS'], 
                                'Strasbourg, France': ['LFST', 'EDTL'], 'Stuttgart, Germany': ['EDDS', 'EDTY'], 'Sumi, Ukraine': ["NaN", "NaN"], 'Sumqayit, Azerbaijan': ['UB12', 'AZ-0013'], 'Sunderland, United Kingdom': ['EGNT', 'EGNV'], 
                                'Swansea, United Kingdom': ['EGFH', 'EGDX'], 'Swindon, United Kingdom': ['EGVA', 'EGVN'], 'Syktyvkar, Russia': ['UUYY', "NaN"], "Syzran', Russia": ['RU-2344', 'UWWW'], 'Szczecin, Poland': ['EPSC', 'EDAH'], 
                                'Szeged, Hungary': ['LHKE', 'LRAR'], 'Taganrog, Russia': ['RU-0211', 'URRT'], 'Tallinn, Estonia': ['EETN', 'EEEI'], 'Tambov, Russia': ['RU-4339', 'UUOT'], 'Tampere, Finland': ['EFTP', 'EFHA'], 
                                'Tarento, Italy': ['LIBG', 'LIBV'], 'Targu Mures, Romania': ['LRTM', 'LRCT'], 'Tarnów, Poland': ['EPRZ', 'EPKK'], 'Tarragona, Spain': ['LERS', 'LEBL'], 'Telford, United Kingdom': ['EGWC', 'EGOS'], 
                                'Terni, Italy': ['LIRV', 'LIRZ'], "Ternopil', Ukraine": ['UKLH', 'UKLI'], 'Terrassa, Spain': ['LEBL', 'ES-0109'], 'Thessalonike, Greece': ['LGTS', 'LGKV'], 'Tilburg, Netherlands': ['EHGR', 'EHEH'], 
                                'Timisoara, Romania': ['LRTR', 'LRAR'], 'Tirana, Albania': ['LATI', 'LAKV'], 'Tiraspol, Moldavia': ['LUTR', 'LUKK'], "Tol'iatti, Russia": ["NaN", "NaN"], 'Torrejón de Ardoz, Spain': ['LETO', 'LEMD'], 
                                'Torun, Poland': ['EPIR', 'EPBY'], 'Toulon, France': ['LFTH', 'LFMQ'], 'Toulouse, France': ['LFBO', 'LFBF'], 'Tours, France': ['LFOT', 'LFRM'], 'Trento, Italy': ['LIDT', 'LIPB'], 
                                'Trier, Germany': ['ETAD', 'ELLX'], 'Trieste, Italy': ['LJPZ', 'LIPQ'], 'Trondheim, Norway': ['ENVA', 'ENOL'], 'Tula, Russia': ['UUBC', 'RU-3686'], 'Turin, Italy': ['LIMA', 'LIMF'], 
                                'Turku, Finland': ['EFTU', 'EFPO'], 'Tuzla, Bosnia and Herzegovina': ['LQTZ', 'LQSA'], "Tver', Russia": ['UUEM', 'RU-9937'], 'Tychy, Poland': ['EPKT', 'EPKK'], 'Ufa, Russia': ['UWUU', "NaN"], 
                                "Ul'ianovsk, Russia": ["NaN", "NaN"], 'Ulm, Germany': ['ETHL', 'EDJA'], 'Uppsala, Sweden': ['ESSA', 'ESSB'], 'Utrecht, Netherlands': ['EHAM', 'EHLE'], 'Uzhgorod, Ukraine': ['UKLU', 'LZKZ'], 
                                'Valladolid, Spain': ['LEVD', 'LESA'], 'València, Spain': ['LEVC', 'LECH'], 'Vantaa, Finland': ['EFHK', 'EFPR'], 'Varna, Bulgaria': ['LBWN', 'LBWB'], 'Velikii Novgorod, Russia': ['RU-9345', 'RU-10055'], 
                                'Venezia, Italy': ['LIPZ', 'LIPH'], 'Verona, Italy': ['LIPX', 'LIPO'], 'Vicenza, Italy': ['LIPU', 'LIDT'], 'Vigo, Spain': ['LEVX', 'LPBR'], 'Vila Nova de Gaia, Portugal': ['LPPR', 'LPVL'], 
                                'Villeurbanne, France': ['LFLY', 'LFLL'], 'Vilnius, Lithuania': ['EYVI', 'EYKA'], 'Vinnitsia, Ukraine': ['UKWW', 'LUBM'], 'Vitoria, Spain': ['LEVT', 'LELO'], 'Vitsebsk, Viciebsk, Belarus': ['UMII', 'BY-0001'], 
                                'Vladikavkaz, Russia': ['URMO', 'URMS'], 'Vladimir, Russia': ['RU-10048', 'UUBI'], 'Volgodonsk, Russia': ["NaN", "NaN"], 'Volgograd, Russia': ['URWW', 'RU-0304'], 'Vologda, Russia': ["NaN", "NaN"], 
                                'Volzhskii, Russia': ["NaN", "NaN"], 'Voronezh, Russia': ['RU-8363', 'UUOO'], 'Västerås, Sweden': ['ESOW', 'ESSU'], 'Wakefield, United Kingdom': ['EGNM', 'EGXG'], 'Walbrzych, Poland': ['EPWR', 'LKPD'], 
                                'Walsall, United Kingdom': ['EGBB', 'EGWC'], 'Warszawa, Poland': ['EPWA', 'EPMO'], 'Wien, Austria': ['LOWW', 'LOAN'], 'Wiesbaden, Germany': ['ETOU', 'EDFZ'], 'Winterthur, Switzerland': ['LSMD', 'LSZH'], 
                                'Wloclawek, Poland': ['EPIR', 'EPLY'], 'Wolfsburg, Germany': ['EDVE', 'ETHC'], 'Wolverhampton, United Kingdom': ['EGWC', 'EGBB'], 'Wroclaw, Poland': ['EPWR', 'EPKS'], 'Wuppertal, Germany': ['EDDL', 'EDLW'], 
                                'Würzburg, Germany': ['ETHN', 'EDQA'], 'York, United Kingdom': ['EGXG', 'EGXZ'], 'Zaanstad, Netherlands': ['EHAM', 'EHLE'], 'Zabrze, Poland': ['EPKT', 'EPKK'], 'Zagreb, Croatia': ['LDZA', 'LJCE'], 
                                'Zaporizhzhia, Ukraine': ['UKDE', 'UKDD'], 'Zaragoza, Spain': ['LEZG', 'LEDA'], 'Zhitomir, Ukraine': ['UKKO', 'UA-0025'], 'Zhukovskii, Russia': ["NaN", "NaN"], 'Zielona Góra, Poland': ['EPZG', 'EDBR'], 
                                'Zoetermeer, Netherlands': ['EHRD', 'EHAM'], 'Zwolle, Netherlands': ['EHLE', 'EHDL'], 'Zürich, Switzerland': ['LSMD', 'LSZH'], 'bat`umi, Georgia': ["NaN", "NaN"], 'k`ut`aisi, Georgia': ["NaN", "NaN"], 
                                'rust`avi, Georgia': ["NaN", "NaN"], 'tbilisi, Georgia': ['UG24', 'UGTB'], 'Amsterdam, Netherlands': ['EHAM', 'EHLE'], 'Örebro, Sweden': ['ESOE', 'ESKK'], 'Hertogenbosch, Netherlands': ['EHEH', 'EHVK']}

INSULAR_EUROPEAN_CITIES = {'Heraklion, Greece': ['LGIR', 'LGST'], 'Belfast, United Kingdom': ['EGAC', 'EGAA'], 'Cork, Republic of Ireland': ['EICK', 'EIKY'], 'Dublin, Republic of Ireland': ['EIDW', 'EIME'], 'Palma, Spain': ['LEPA', 'LEIB'], 
                           'Rhodes, Greece': ['LGRP', 'LTBS'], 'Cagliari, Italy': ['LIEE', 'LIED'], 'Sassari, Italy': ['LIEO', 'LIEA'], 'Catania, Italy': ['LICC', 'LICZ'], 'Messina, Italy': ['LICR', 'LICC'], 'Palermo, Italy': ['LICP', 'LICJ'], 
                           'Siracusa, Italy': ['LICC', 'LICZ']}


# ── diferentes islas ─────────────────────────────────────────
IRELAND = {'Cork, Republic of Ireland' :['EICK', 'EIKY'], 'Dublin, Republic of Ireland':['EIDW', 'EIME'], 'Belfast, United Kingdom' :['EGAC', 'EGAA']}

SICILY = {'Catania, Italy': ['LICC', 'LICZ'], 'Messina, Italy': ['LICR', 'LICC'], 'Palermo, Italy': ['LICP', 'LICJ'], 'Siracusa, Italy': ['LICC', 'LICZ']}

SARDINIA = {'Cagliari, Italy': ['LIEE', 'LIED'], 'Sassari, Italy': ['LIEO', 'LIEA']}

NO_TRAIN = {'Heraklion, Greece': ['LGIR', 'LGST'], 'Palma, Spain': ['LEPA', 'LEIB'], 'Rhodes, Greece': ['LGRP', 'LTBS']}

# ── todas ────────────────────────────────────────────────────

EUROPEAN_CITIES = {'A Coruña, Spain': ['LECO', 'LEST'], 'Aachen, Germany': ['ETNG', 'EHBK'], 'Aalborg, Denmark': ['EKYT', 'EKSN'], 'Aarhus, Denmark': ['EKAH', 'EKKA'], 
                    'Aiberdeen, United Kingdom': ['EGPD', 'EGPN'], 'Aix-en-Provence, France': ['LFML', 'LFMY'], 'Almetevsk, Russia': ['UWKB', 'UWKE'], 'Alacant, Spain': ['LEAL', 'LELC'], 
                    'Albacete, Spain': ['LEAB', 'LERI'], 'Alcalá de Henares, Spain': ['LETO', 'LEMD'], 'Alchevsk, Ukraine': ['RU-0282', 'RU-0211'], 'Alcobendas, Spain': ['LEMD', 'LETO'], 
                    'Alcorcón, Spain': ['LECU', 'LEGT'], 'Algeciras, Spain': ['LXGB', 'GMTN'], 'Almada, Portugal': ['LPPT', 'LPMT'], 'Almere, Netherlands': ['EHLE', 'EHAM'], 
                    'Almería, Spain': ['LEAM', 'LEGA'], 'Amadora, Portugal': ['LPPT', 'LPCS'], 'Amersfoort, Netherlands': ['EHLE', 'EHDL'], 'Amiens, France': ['LFAY', 'LFOI'], 
                    'Anderlecht, Belgium': ['EBBR', 'EBBE'], 'Angers, France': ['LFJR', 'LFOV'], 'Antwerpen, Belgium': ['EBAW', 'EHWO'], 'Apeldoorn, Netherlands': ['EHDL', 'EHLE'], 
                    'Arad, Romania': ['LRAR', 'LRTR'], 'Argenteuil, France': ['LFPB', 'LFPV'], 'Arkhangelsk, Russia': ['ULAA', 'ULAH'], 'Armavir, Russia': ['URMT', 'RU-10062'], 
                    'Arnhem, Netherlands': ['EHDL', 'EHVK'], 'Arzamas, Russia': ['RU-0043', 'UWGG'], "Astrakhan', Russia": ['URWA', 'RU-0303'], 'Athens, Greece': ['LGEL', 'LGAV'], 
                    'Atyrau, Kazakhstan': ['UATG', "NaN"], 'Augsburg, Germany': ['EDMA', 'ETSL'], 'Babruisk, Babrujsk, Belarus': ['UMNB', 'UMOO'], 'Bacau, Romania': ['LRBC', 'LRIA'], 
                    'Badajoz, Spain': ['LEBZ', 'LPEV'], 'Badalona, Spain': ['LEBL', 'ES-0109'], 'Baia Mare, Romania': ['LRBM', 'LRSM'], 'Baki, Azerbaijan': ['AZ-0001', 'UBBB'], 
                    'Balakovo, Russia': ['UWSB', 'RU-3709'], 'Balashikha, Russia': ['UUMU', 'RU-10054'], 'Banja Luka, Bosnia and Herzegovina': ['LQBK', 'LQTZ'], 'Barakaldo, Spain': ['LEBB', 'LEVT'], 
                    'Baranavichy, Belarus': ['UMMA', 'BY-0006'], 'Barcelona, Spain': ['LEBL', 'ES-0109'], 'Bari, Italy': ['LIBD', 'LIBV'], 'Barysau, Belarus': ['UMMS', 'UMOO'], 
                    'Basel, Switzerland': ['LFSB', 'LSZG'], 'Bataisk, Russia': ['RU-0372', 'URRP'], 'Belgorod, Russia': ['UUOB', 'UKHH'], 'Beograd, Serbia': ['LYBE', 'LYBT'], 'Berdiansk, Ukraine': ['UKDB', 'UKCM'], 
                    'Berezniki, Russia': ["NaN", "NaN"], 'Bergen, Norway': ['ENBR', 'ENSO'], 'Bergisch Gladbach, Germany': ['EDDK', 'ETNN'], 'Berlin, Germany': ['EDDB', 'ETSH'], 'Bern, Switzerland': ['LSZB', 'LSZG'], 
                    'Besançon, France': ['LFQW', 'LFGJ'], 'Bialystok, Poland': ['UMMG', 'UMBB'], 'Bielefeld, Germany': ['EDLP', 'ETHB'], 'Bielsko-Biala, Poland': ['EPKK', 'LKMT'], 
                    'Bila Tserkva, Ukraine': ['UA-0025', 'UKKK'], 'Bilbo, Spain': ['LEBB', 'LEVT'], 'Birmingham, United Kingdom': ['EGBB', 'EGBE'], 'Blackburn, United Kingdom': ['EGNO', 'EGNH'], 
                    'Blackpool, United Kingdom': ['EGNH', 'EGNO'], 'Bochum, Germany': ['EDLW', 'EDDL'], 'Bologna, Italy': ['LIPE', 'LIPK'], 'Bolos, Greece': ['LGBL', 'LGSK'], 
                    'Bolton, United Kingdom': ['EGCC', 'EGNO'], 'Bolzano, Italy': ['LIPB', 'LOWI'], 'Bonn, Germany': ['EDDK', 'ETNN'], 'Bordeaux, France': ['LFBD', 'LFCH'], 
                    'Botosani, Romania': ['LRSV', 'UKLN'], 'Bottrop, Germany': ['EDDL', 'EDLN'], 'Boulogne-Billancourt, France': ['LFPV', 'LFPN'], 'Bournemouth, United Kingdom': ['EGHH', 'EGHI'], 
                    'Bradford, United Kingdom': ['EGNM', 'EGXG'], 'Braga, Portugal': ['LPBR', 'LPVL'], 'Braila, Romania': ['LR79', 'LRTC'], 'Brasov, Romania': ['LRBV', 'LR82'], 'Bratislava, Slovakia': ['LZIB', 'LZMC'], 
                    'Braunschweig, Germany': ['EDVE', 'ETHC'], 'Breda, Netherlands': ['EHGR', 'EHWO'], 'Bremen, Germany': ['EDDW', 'ETND'], 'Bremerhaven, Germany': ['ETMN', 'EDDW'], 'Brescia, Italy': ['LIPO', 'LIPL'], 
                    'Brest (Finisterre), France': ['LFRB', 'LFRL'], 'Brest, Belarus': ['UMBB', 'BY-0006'], 'Briansk, Russia': ['UUBP', 'RU-0240'], 'Brighton & Hove, United Kingdom': ['EGKA', 'EGKK'], 
                    'Bristol, United Kingdom': ['EGGD', 'EGDY'], 'Brno, Czechia': ['LKTB', 'LKNA'], 'Brugge, Belgium': ['EBOS', 'EBFN'], 'Bruxelles - Brussel, Belgium': ['EBBR', 'EBBE'], 'Bucuresti, Romania': ['LRBS', 'LROP'], 
                    'Budapest, Hungary': ['LHBP', 'LHTL'], 'Burgas, Bulgaria': ['LBBG', 'BG-JAM'], 'Burgos, Spain': ['LEBG', 'LEVT'], 'Buzau, Romania': ['LR82', 'LR79'], 'Bydgoszcz, Poland': ['EPBY', 'EPIR'], 
                    'Bytom, Poland': ['EPKT', 'EPKK'], 'Bérgamo, Italy': ['LIME', 'LIML'], 'Caen, France': ['LFRK', 'LFRG'], 'Cambridge, United Kingdom': ['EGSC', 'EGUN'], 'Cardiff, United Kingdom': ['EGFF', 'EGDX'], 
                    'Cartagena, Spain': ['LELC', 'LEMI'], 'Castellón de la Plana, Spain': ['LECH', 'LEVC'], 'Charleroi, Belgium': ['EBCI', 'EBFS'], 'Cheboksary, Russia': ['UWKS', 'UWKJ'], 
                    'Chelmsford, United Kingdom': ['EGSS', 'EGMC'], 'Chemnitz, Germany': ['EDAC', 'EDDC'], 'Cherepovets, Russia': ['ULWC', 'RU-10056'], 'Cherkasy, Ukraine': ['UKKE', 'UA-0025'], 
                    'Cherkessk, Russia': ['URMM', 'URMT'], 'Chernigiv, Ukraine': ['UA-0005', 'UKBB'], 'Chernivtsi, Ukraine': ['UKLN', 'LRSV'], 'Chisinau, Moldavia': ['LUKK', 'LUTR'], 
                    'Chorzów, Poland': ['EPKT', 'EPKK'], 'St Albans, United Kingdom': ['EGGW', 'EGWU'], 'Westminster, United Kingdom': ['EGLC', 'EGWU'], 'Clermont-Ferrand, France': ['LFLC', 'LFLV'], 
                    'Cluj-Napoca, Romania': ['LRCL', 'LRCT'], 'Colchester, United Kingdom': ['EGUW', 'EGMC'], 'Constanta, Romania': ['LRCK', 'LR80'], 'Coventry, United Kingdom': ['EGBE', 'EGBB'], 
                    'Coímbra, Portugal': ['LPCO', 'LPMR'], 'Craiova, Romania': ['LRCV', 'LBPL'], 'Crawley, United Kingdom': ['EGKK', 'EGKB'], 'Czestochowa, Poland': ['EPKT', 'EPLK'], 'Cádiz, Spain': ['LERT', 'LEJR'], 
                    'Córdoba, Spain': ['LEBA', 'LEMO'], 'Dabrowa Gornicza, Poland': ['EPKT', 'EPKK'], 'Darmstadt, Germany': ['EDFE', 'EDDF'], 'Debrecen, Hungary': ['LHDC', 'LROD'], 'Den Haag, Netherlands': ['EHRD', 'EHAM'], 
                    'Derbent, Russia': ['URML', 'UBBY'], 'Derby, United Kingdom': ['EGNX', 'EGBN'], 'Dijon, France': ['LFSD', 'LFGJ'], 'Dimitrovgrad, Russia': ['UWLW', 'UWWW'], 'Dnipro, Ukraine': ['UA-0005', 'UKKM'], 
                    'Dniprodzerzhinsk, Ukraine': ["NaN", "NaN"], 'Donetsk, Russia': ['RU-0282', 'URRP'], 'Donostia, Spain': ['LESO', 'LFBZ'], 'Dordrecht, Netherlands': ['EHRD', 'EHGR'], 'Dortmund, Germany': ['EDLW', 'EDDL'], 
                    'Dos Hermanas, Spain': ['LEZL', 'LEMO'], 'Dresden, Germany': ['EDDC', 'EDAC'], 'Duisburg, Germany': ['EDDL', 'EDLN'], 'Dundee, United Kingdom': ['EGPN', 'EGQL'], 'Durrës, Albania': ['LATI', 'LAKV'], 
                    'Dzerzhinsk, Russia': ['UWGG', 'RU-0217'], 'Düsseldorf, Germany': ['EDDL', 'EDLN'], 'Ede, Netherlands': ['EHDL', 'EHLE'], 'Edinburgh, United Kingdom': ['EGPH', 'EGQL'], 'Eindhoven, Netherlands': ['EHEH', 'EHBD'], 
                    'Elblag, Poland': ['EPMB', 'EPGD'], "Elektrostal', Russia": ['UUMU', 'UUBW'], 'Elets, Russia': ['RU-0016', 'UUOL'], 'Elista, Russia': ['URWI', "NaN"], 'Elx, Spain': ['LEAL', 'LELC'], 
                    'Emmen, Netherlands': ['EHGG', 'EHTW'], "Engel's, Russia": ['XRMU', 'URMG'], 'Enschede, Netherlands': ['EHTW', 'EDDG'], 'Erewan, Armenia': ['UDYE', 'UDYZ'], 'Erfurt, Germany': ['EDDE', 'EDGE'], 'Erlangen, Germany': ['EDDN', 'EDQA'], 
                    'Espoo, Finland': ['EFHK', 'EETN'], 'Essen, Germany': ['EDDL', 'EDLW'], 'Exeter, United Kingdom': ['EGTE', 'EGDC'], 'Ferrara, Italy': ['LIPE', 'LIPK'], 'Florence, Italy': ['LIRQ', 'LIQS'], 
                    'Foggia, Italy': ['LIBF', 'LIBA'], 'Forlì, Italy': ['LIPK', 'LIPC'], 'Frankfurt am Main, Germany': ['EDDF', 'EDFE'], 'Freiburg im Breisgau, Germany': ['LFGA', 'EDTL'], 'Fuenlabrada, Spain': ['LEGT', 'LECU'], 
                    'Fürth, Germany': ['EDDN', 'EDQA'], 'G@nc@, Azerbaijan': ["NaN", "NaN"], 'Galati, Romania': ['LUCH', 'UA-0028'], 'Gdansk, Poland': ['EPGD', 'EPMB'], 'Gdynia, Poland': ['EPGD', 'EPCE'], 
                    'Gelsenkirchen, Germany': ['EDDL', 'EDLW'], 'Genève, Switzerland': ['LSGG', 'LFLI'], 'Getafe, Spain': ['LEGT', 'LECU'], 'Ghent, Belgium': ['EBKT', 'EBCV'], 'Gijón, Spain': ['LEAS', 'LELN'], 
                    'Giugliano de Campania, Italy': ['LIRN', 'LIRM'], 'Glasgow, United Kingdom': ['EGPF', 'EGPK'], 'Gliwice, Poland': ['EPKT', 'LKMT'], 'Gloucester, United Kingdom': ['EGBJ', 'EGVA'], 
                    "Gomel', Homiel, Belarus": ['UMGG', 'UMNB'], 'Gorlivka, Ukraine': ['RU-0211', 'URRT'], 'Gorzów Wielkopolski, Poland': ['EPZG', 'EPMI'], 'Gothenburg, Sweden': ['ESGP', 'ESGG'], 
                    'Granada, Spain': ['LEGA', 'LEGR'], 'Graz, Austria': ['LOWG', 'LOXZ'], 'Grenoble, France': ['LFLS', 'LFLB'], 'Grodna, Hrodna, Belarus': ['UMMG', 'EYVI'], 'Groningen, Netherlands': ['EHGG', 'EHLW'],
                    'Groznyi, Russia': ['URMG', 'XRMU'], 'Gyor, Hungary': ['LHPR', 'LZIB'], 'Gyowmri, Armenia': ["NaN", "NaN"], 'Génova, Italy': ['LIMJ', 'LIMR'], 'Göttingen, Germany': ['EDVK', 'ETHF'], 
                    'Haarlem, Netherlands': ['EHAM', 'EHRD'], 'Haarlemmermeer, Netherlands': ['EHAM', 'EHRD'], 'Hagen, Germany': ['EDLW', 'EDDL'], 'Halle, Germany': ['EDDP', 'EDUZ'], 'Hamburg, Germany': ['EDDH', 'EDHI'], 
                    'Hamm, Germany': ['ETAD', 'ELLX'], 'Hannover, Germany': ['EDDV', 'ETNW'], 'Heidelberg, Germany': ['EDFM', 'EDFE'], 'Heilbronn, Germany': ['EDTY', 'EDDS'], 'Helsinki, Finland': ['EFHK', 'EETN'], 
                    'Herne, Germany': ['EDLW', 'EDDL'], 'Huddersfield, United Kingdom': ['EGNM', 'EGXG'], 'Huelva, Spain': ['LERT', 'LPFR'], "Iaroslavl', Russia": ['UUBA', 'UUBK'], 'Iasi, Romania': ['LRIA', 'LUBL'], 
                    'Ievpatoriia, Russia': ["NaN", "NaN"], 'Ingolstadt, Germany': ['ETSI', 'ETSN'], 'Innsbruck, Austria': ['LOWI', 'LIPB'], 'Ioannina, Greece': ['LGIO', 'LGKR'], 'Ioshkar-Ola, Russia': ['UWKJ', 'RU-4421'], 
                    'Ipswich, United Kingdom': ['EGUW', 'EGXH'], 'Istanbul, Turquía': ['LTBA', 'LTBX'], "Ivano-Frankivs'k, Ukraine": ['UKLI', 'UKLL'], 'Ivanovo, Russia': ['RU-5672', 'UUBI'], 'Izhevsk, Russia': ['USII', "NaN"], 
                    'Jaén, Spain': ['LEGR', 'LEGA'], 'Jena, Germany': ['EDDE', 'EDAC'], 'Jerez de la Frontera, Spain': ['LEJR', 'LERT'], 'Jyväskylä, Finland': ['EFJY', 'EFHA'], 'Kaliningrad, Russia': ['RU-0028', 'UMKK'], 
                    'Kaluga, Russia': ['UUBC', 'RU-3686'], 'Kamyshin, Russia': ['XRWL', "NaN"], 'Karlsruhe, Germany': ['EDSB', 'EDFM'], 'Kassel, Germany': ['EDVK', 'ETHF'], 'Katowice, Poland': ['EPKT', 'EPKK'], 
                    'Kaunas, Lithuania': ['EYKA', 'EYKD'], "Kazan', Russia": ['UWKG', 'UWKD'], 'Kerch, Russia': ['UUEE', 'UUMO'], 'Khania, Greece': ['LGSA', 'LGIR'], 'Kharkiv, Ukraine': ['UKHH', 'UUOB'], 
                    'Khasaviurt, Russia': ['XRMU', 'URMG'], 'Kherson, Ukraine': ['UKOH', 'UKFY'], 'Khimki, Russia': ['UUEE', 'UUWW'], "Khmel'nits'kii, Ukraine": ["NaN", "NaN"], 'Kiel, Germany': ['EDHK', 'ETNH'], 
                    'Kielce, Poland': ['EPRA', 'EPTM'], 'Kingston upon Hull, United Kingdom': ['EGNJ', 'EGXG'], 'Kirov, Russia': ['USKK', "NaN"], 'Kirovograd, Ukraine': ['UKDR', 'UKKE'], 'Kislovodsk, Russia': ['URMM', 'URMN'], 
                    'Kiyiv, Ukraine': ['UKKK', 'UKBB'], 'Klaipeda, Lithuania': ['EYPA', 'EVLA'], 'Koblenz, Germany': ['ETSB', 'EDFH'], 'Kolomna, Russia': ['UUMT', 'UUBW'], 'Koroliov, Russia': ['UUMU', 'UUEE'], 
                    'Kosice, Slovakia': ['LZKZ', 'UKLU'], 'Kostroma, Russia': ['UUBA', 'RU-5672'], 'Koszalin, Poland': ['EPSN', 'EPMI'], 'Kovrov, Russia': ['RU-10048', 'UUBI'], 'Kragujevats, Serbia': ["NaN", "NaN"], 
                    'Kraków, Poland': ['EPKK', 'EPKT'], "Kramators'k, Ukraine": ["NaN", "NaN"], 'Krasnodar, Russia': ['RU-0090', 'URKK'], 'Krefeld, Germany': ['EDLN', 'EDDL'], 'Kremenchuk, Ukraine': ['UKKE', 'UKDR'], 
                    'Krivii rig, Ukraine': ["NaN", "NaN"], 'Kuopio, Finland': ['EFKU', 'EFVR'], 'Kursk, Russia': ['UUOK', 'UUOB'], 'Köln, Germany': ['EDDK', 'ETNN'], 'København, Denmark': ['EKCH', 'EKRK'], 
                    "L'Hospitalet de Llobregat, Spain": ['LEBL', 'ES-0109'], "L'viv, Ukraine": ['UKDD', 'UKDE'], 'Lahti, Finland': ['EFUT', 'EFPR'], 'Larisa, Greece': ['LGBL', 'LGKZ'], 'Latina, Italy': ['LIRL', 'LIRA'], 
                    'Lausanne, Switzerland': ['LSMP', 'LFLI'], 'Le Havre, France': ['LFOH', 'LFRG'], 'Le Mans, France': ['LFRM', 'LFJR'], 'Leeds, United Kingdom': ['EGNM', 'EGXG'], 'Leganés, Spain': ['LECU', 'LEGT'], 
                    'Leicester, United Kingdom': ['EGNX', 'EGBN'], 'Leiden, Netherlands': ['EHRD', 'EHAM'], 'Leipzig, Germany': ['EDDP', 'EDAC'], 'Lemesos, Cyprus': ['LCRA', 'LCPH'], 'Leukosia, Cyprus': ['LCEN', 'LCGK'], 
                    'Leverkusen, Germany': ['EDDK', 'ETNN'], 'León, Spain': ['LELN', 'LEAS'], 'Liberec, Czechia': ['EDBR', 'LKVO'], 'Lille, France': ['LFQQ', 'EBKT'], 'Limoges, France': ['LFBL', 'LFBX'], 
                    'Linköping, Sweden': ['ESSL', 'ESCF'], 'Linz, Austria': ['LOWL', 'LOWS'], 'Lipetsk, Russia': ['RU-0016', 'UUOL'], 'Lisboa, Portugal': ['LPPT', 'LPMT'], 'Liubertsy, Russia': ['RU-10054', 'UUBW'], 
                    'Liverpool, United Kingdom': ['EGGP', 'EGNR'], 'Livorno, Italy': ['LIRJ', 'LIRS'], 'Liège, Belgium': ['EBLG', 'EHBK'], 'Ljbljana, Slovenia': ["NaN", "NaN"], 'Lleida, Spain': ['LEDA', 'LERS'], 
                    'Lodz, Poland': ['EPLL', 'EPLK'], 'Logroño, Spain': ['LELO', 'LEVT'], 'London, United Kingdom': ['EGLC', 'EGWU'], 'Lublin, Poland': ['EPLB', 'EPDE'], 'Ludwigshafen am Rhein, Germany': ['EDFM', 'EDFE'], 
                    "Lugans'k, Russia": ["NaN", "NaN"], 'Luton, United Kingdom': ['EGGW', 'EGTC'], "Luts'k, Ukraine": ["NaN", "NaN"], 'Luxembourg, Luxembourg': ['ELLX', 'LFQE'], 'Lyon, France': ['LFLY', 'LFLL'], 
                    'Lübeck, Germany': ['EDHL', 'EDDH'], 'Maastricht, Netherlands': ['EHBK', 'ETNG'], 'Madrid, Spain': ['LECU', 'LEMD'], 'Magdeburg, Germany': ['EDUZ', 'EDVE'], 'Magiliou, Mahilou, Belarus': ["NaN", "NaN"], 
                    'Maikop, Russia': ['RU-10062', 'URKK'], 'Mainz, Germany': ['ETOU', 'EDFZ'], 'Makhachkala, Russia': ['URML', 'XRMU'], 'Makiyivka, Ukraine': ['RU-0211', 'UKCM'], 'Malmö, Sweden': ['EKCH', 'ESMS'], 
                    'Manchester, United Kingdom': ['EGCC', 'EGGP'], 'Mannheim, Germany': ['EDFM', 'EDFE'], 'Marbella, Spain': ['LEMG', 'LXGB'], 'Marseille, France': ['LFML', 'LFMQ'], 'Mataró, Spain': ['LEBL', 'ES-0109'], 
                    'Mazyr, Mazyr, Belarus': ['UMNB', 'UMGG'], "Melitopol', Ukraine": ['UA-0020', 'UKDB'], 'Metz, France': ['LFJL', 'LFQE'], 'Middlesbrough, United Kingdom': ['EGNV', 'EGXE'], 
                    'Mikolayiv, Ukraine': ['UKON', 'UKOH'], 'Milan, Italy': ['LIML', 'LILN'], 'Milton Keynes, United Kingdom': ['EGTC', 'EGGW'], 'Ming@cevir, Azerbaijan': ["NaN", "NaN"], 'Minsk, Belarus': ['UMMS', 'UMMA'], 
                    'Miskolc, Hungary': ['LZKZ', 'LHDC'], 'Modena, Italy': ['LIPE', 'LIMP'], 'Moers, Germany': ['EDDL', 'EDLN'], 'Montpellier, France': ['LFMT', 'LFTW'], 'Montreuil, France': ['LFAT', 'LFOI'], 
                    'Monza, Italy': ['LIML', 'LILN'], 'Moscow, Russia': ['UUMO', 'UUWW'], 'Mulhouse, France': ['LFSB', 'LFGA'], 'Murcia, Spain': ['LERI', 'LEMI'], 'Murom, Russia': ['RU-0043', 'RU-10048'], 
                    'Mytishchi, Russia': ['UUMU', 'UUEE'], 'Málaga, Spain': ['LEMG', 'LEGR'], 'Móstoles, Spain': ['LECU', 'LEGT'], 'Mönchengladbach, Germany': ['EDLN', 'EDDL'], 'Mülheim an der Ruhr, Germany': ['EDDL', 'EDLN'], 
                    'München, Germany': ['EDMO', 'EDDM'], 'Münster, Germany': ['EDDG', 'EDLW'], 'Naberezhnye Chelny, Russia': ['UWKE', 'UWKB'], "Nal'chik, Russia": ['URMN', 'URMO'], 'Namur, Belgium': ['EBCI', 'EBFS'], 
                    'Nancy, France': ['LFSN', 'LFSO'], 'Nantes, France': ['LFRS', 'LFRZ'], 'Napoli, Italy': ['LIRN', 'LIRM'], "Nazran', Russia": ['URMO', 'URMS'], 'Neftekamsk, Russia': ['USII', 'UWKE'], 
                    'Neuss, Germany': ['EDDL', 'EDLN'], 'Nevinnomyssk, Russia': ['URMT', 'URMM'], 'Newcastle upon Tyne, United Kingdom': ['EGNT', 'EGNV'], 'Newport, United Kingdom': ['EGGD', 'EGFF'], 
                    'Nice, France': ['LFMN', 'LFMD'], 'Nijmegen, Netherlands': ['EHVK', 'EHDL'], "Nikopol', Ukraine": ['UA-0047', 'UKDE'], 'Nish, Serbia': ['LYNI', 'BKPR'], 'Nizhnekamsk, Russia': ['UWKE', 'UWKB'], 
                    'Nizhnii Novgorod, Russia': ['RU-0217', 'UWGG'], 'Noginsk, Russia': ['UUMU', 'UUBW'], 'Northampton, United Kingdom': ['EGTC', 'EGBE'], 'Norwich, United Kingdom': ['EGSH', 'EGXH'], 
                    'Nottingham, United Kingdom': ['EGBN', 'EGNX'], 'Novara, Italy': ['LIMN', 'LIMC'], 'Novi Sad, Serbia': ['LYBT', 'LYBE'], 'Novocheboksarsk, Russia': ['UWKS', 'RU-4421'], 
                    'Novocherkassk, Russia': ['URRP', 'RU-0372'], 'Novomoskovsk, Russia': ['RU-10059', 'UUMT'], 'Novorossiisk, Russia': ['URKG', 'RU-0089'], 'Novoshakhtinsk, Russia': ['URRP', 'RU-0372'], 
                    'Nîmes, France': ['LFTW', 'LFMS'], 'Nürnberg, Germany': ['EDDN', 'EDQA'], 'Oberhausen, Germany': ['EDDL', 'EDLN'], 'Obninsk, Russia': ['RU-10053', 'RU-0764'], 'Odense, Denmark': ['EKOD', 'EKSB'], 
                    'Odesa, Ukraine': ['UKOO', 'LUTR'], 'Odintsovo, Russia': ['UUWW', 'UUMO'], 'Offenbach am Main, Germany': ['EDDF', 'EDFE'], "Oktiabr'skii, Russia": ['USCM', "NaN"], 'Oldemburg, Germany': ["NaN", "NaN"], 
                    'Olsztyn, Poland': ['EPSY', 'EPMB'], 'Opole, Poland': ['EPKT', 'EPWR'], 'Oradea, Romania': ['LROD', 'LHDC'], 'Oral, Kazakhstan': ['UARR', "NaN"], 'Orekhovo-Zuevo, Russia': ['UUMU', 'UUBW'], 
                    'Orenburg, Russia': ['UWOO', "NaN"], 'Oriol, Russia': ['UUBP', 'UUOK'], 'Orléans, France': ['LFOJ', 'LFOC'], 'Orsha, Orsa, Belarus': ['BY-0001', 'UMOO'], 'Orsk, Russia': ['UWOR', 'UATT'], 
                    'Oslo, Norway': ['ENGM', 'ENRY'], 'Osnabrück, Germany': ['EDDG', 'ETND'], 'Ostrava, Czechia': ['LKMT', 'LZZI'], 'Oulu, Finland': ['EFOU', 'EFKE'], 'Ourense, Spain': ['LPBG', 'LEVX'], 
                    'Oviedo, Spain': ['LEAS', 'LELN'], 'Oxford, United Kingdom': ['EGTK', 'EGUB'], 'Paderborn, Germany': ['EDLP', 'EDVK'], 'Padova, Italy': ['LIPU', 'LIPS'], 'Pamplona, Spain': ['LEPP', 'LESO'], 
                    'Paris, France': ['LFPV', 'LFPB'], 'Parla, Spain': ['LEGT', 'LECU'], 'Parma, Italy': ['LIMP', 'LIMS'], 'Patra, Greece': ['LGRX', 'LGAD'], 'Pavlograd, Ukraine': ['UKDD', 'UKDE'], 
                    'Penza, Russia': ['UWPP', 'UWPS'], 'Peristeri, Greece': ['LGEL', 'LGAV'], "Perm', Russia": ['USPP', "NaN"], 'Perpiñán, France': ['LFMP', 'LFMK'], 'Perugia, Italy': ['LIRZ', 'LIRV'], 
                    'Pescara, Italy': ['LIBP', 'LIRG'], 'Peterborough, United Kingdom': ['EGXT', 'EGYE'], 'Petrozavodsk, Russia': ['ULPP', 'ULPB'], 'Pforzheim, Germany': ['EDDS', 'EDSB'], 'Piacenza, Italy': ['LIMS', 'LIMP'], 
                    'Piatigorsk, Russia': ['URMM', 'URMN'], 'Pinsk, Pinsk, Belarus': ['BY-0006', 'UMMA'], 'Piraeus, Greece': ['LGEL', 'LGAV'], 'Pitesti, Romania': ['LRCV', 'LROP'], 'Pleven, Bulgaria': ['LBPL', 'LBGO'], 
                    'Plock, Poland': ['EPMO', 'EPLY'], 'Ploiesti, Romania': ['LROP', 'LRBS'], 'Plovdiv, Bulgaria': ['LBPD', 'LBPG'], 'Plymouth, United Kingdom': ['EGHQ', 'EGTE'], 'Plzen, Czechia': ['LKLN', 'LKKV'], 
                    'Podgorica, Montenegro': ['LYPG', 'LYTV'], "Podol'sk, Russia": ['UUMO', 'UUDD'], 'Poltava, Ukraine': ['UKKE', "NaN"], 'Poole, United Kingdom': ['EGHH', 'EGDM'], 'Porto, Portugal': ['LPPR', 'LPVL'], 
                    'Portsmouth, United Kingdom': ['EGHI', 'EGHL'], 'Potsdam, Germany': ['EDDB', 'ETSH'], 'Poznan, Poland': ['EPPO', 'EPKS'], 'Prague, Czechia': ['LKKB', 'LKPR'], 'Prato, Italy': ['LIRQ', 'LIRP'], 
                    'Preston, United Kingdom': ['EGNO', 'EGNH'], 'Prishtina, Kosovo': ['BKPR', 'LWSK'], 'Pskov, Russia': ['ULOO', 'RU-0064'], 'Pécs, Hungary': ['LHPP', 'LHTA'], 'Radom, Poland': ['EPRA', 'EPDE'], 
                    'Ravenna, Italy': ['LIPK', 'LIPC'], 'Reading, United Kingdom': ['EGLK', 'EGUB'], 'Recklinghausen, Germany': ['EDLW', 'EDDL'], 'Regensburg, Germany': ['ETIH', 'ETSI'], 'Reggio di Calabria, Italy': ['LICR', 'LICC'], 
                    "Reggio nell'Emilia, Italy": ['LIMP', 'LIPE'], 'Reims, France': ['LFOK', 'LFQV'], 'Remscheid, Germany': ['EDDL', 'EDDK'], 'Rennes, France': ['LFRN', 'LFRD'], 'Reus, Spain': ['LERS', 'LEDA'], 
                    'Reutlingen, Germany': ['EDDS', 'ETHL'], 'Reykjavík, Iceland': ['BIRK', 'BIKF'], "Riazan', Russia": ['RU-10059', 'UUMT'], 'Riga, Latvia': ['EVRA', 'EVTA'], 'Rijeka, Croatia': ['LDRI', 'LDPL'], 
                    'Rimini, Italy': ['LIPR', 'LIPC'], 'Rivne, Ukraine': ['UKLR', "NaN"], 'Rome, Italy': ['LIRU', 'LIRA'], 'Rostock, Germany': ['ETNL', 'EKMB'], 'Rostov-na-Donu, Russia': ['RU-0372', 'URRP'], 
                    'Rotherham, United Kingdom': ['EGXG', 'EGNM'], 'Rotterdam, Netherlands': ['EHRD', 'EHAM'], 'Rouen, France': ['LFOP', 'LFOE'], 'Ruda Slaska, Poland': ['EPKT', 'EPKK'], 'Ruse, Bulgaria': ['LRBS', 'LBGO'], 
                    'Rybinsk, Russia': ['UUBK', 'RU-10056'], 'Rybnik, Poland': ['LKMT', 'EPKT'], 'Rzeszów, Poland': ['EPRZ', 'UKLL'], 'Saarbrücken, Germany': ['EDDR', 'ETAR'], 'Sabadell, Spain': ['LEBL', 'ES-0109'], 
                    'Saint Helens, United Kingdom': ['EGTK', 'EGUB'], 'Saint Petersburg, Russia': ['RU-0001', 'ULLI'], 'Saint-Denis, France': ['LFPB', 'LFPG'], 'Saint-Étienne, France': ['LFMH', 'LFLY'], 
                    'Salamanca, Spain': ['LESA', 'LEVD'], 'Salavat, Russia': ['UWUU', "NaN"], 'Salerno, Italy': ['LIRI', 'LIRN'], 'Salford, United Kingdom': ['EGCC', 'EGGP'], 'Saligorsk, Salihorsk, Belarus': ['UMMA', 'UMNB'], 
                    'Salzburg, Austria': ['LOWS', 'LOWL'], 'Samara, Russia': ['RU-2344', 'UWWG'], 'Santa Coloma de Gramanet, Spain': ['LEBL', 'ES-0109'], 'Santander, Spain': ['LEXJ', 'LEBB'], 
                    'Sarajevo, Bosnia and Herzegovina': ['LQSA', 'LQTZ'], 'Saransk, Russia': ['UWPS', 'RU-6558'], 'Saratov, Russia': ['RU-8602', 'UWSG'], 'Schaerbeek, Belgium': ['EBBR', 'EBBE'], 
                    'Serpukhov, Russia': ['RU-10053', 'UUDD'], "Sevastopol', Russia": ['UUEE', 'UUMO'], 'Severodvinsk, Russia': ['ULAH', 'ULAA'], 'Seville, Spain': ['LEZL', 'LEMO'], 'Shakhty, Russia': ['URRP', 'RU-0372'], 
                    'Shchiolkovo, Russia': ["NaN", "NaN"], 'Sheffield, United Kingdom': ['EGXG', 'EGCC'], 'Sibiu, Romania': ['LRSB', 'LRTM'], "Sieverodonets'k, Ukraine": ["NaN", "NaN"], "Simferopol', Russia": ["NaN", "NaN"], 
                    'Skopje, North Macedonia': ['LWSK', 'BKPR'], 'Slough, United Kingdom': ['EGLL', 'EGWU'], "Slov'ians'k, Ukraine": ["NaN", "NaN"], 'Smolensk, Russia': ['RU-10076', 'RU-4609'], 'Sochi, Russia': ['URSS', 'UG0U'], 
                    'Sofiia, Bulgaria': ["NaN", "NaN"], 'Solingen, Germany': ['EDDL', 'EDDK'], 'Sosnowiec, Poland': ['EPKT', 'EPKK'], 'Southampton, United Kingdom': ['EGHI', 'EGHH'], 'Southend-on-Sea, United Kingdom': ['EGMC', 'EGLC'], 
                    'Split, Croatia': ['LDSP', 'LDSB'], 'Stara Zagora, Bulgaria': ['BG-JAM', 'LBPD'], 'Staryi Oskol, Russia': ['RU-8363', 'UUOO'], 'Stavanger, Norway': ['ENZV', 'ENHD'], "Stavropol', Russia": ['RU-0128', 'URMM'], 
                    'Sterlitamak, Russia': ['UWUU', "NaN"], 'Stockholm, Sweden': ['ESSB', 'ESSA'], 'Stockport, United Kingdom': ['EGCC', 'EGGP'], 'Stoke-on-Trent, United Kingdom': ['EGCC', 'EGOS'], 
                    'Strasbourg, France': ['LFST', 'EDTL'], 'Stuttgart, Germany': ['EDDS', 'EDTY'], 'Sumi, Ukraine': ["NaN", "NaN"], 'Sumqayit, Azerbaijan': ['UB12', 'AZ-0013'], 'Sunderland, United Kingdom': ['EGNT', 'EGNV'], 
                    'Swansea, United Kingdom': ['EGFH', 'EGDX'], 'Swindon, United Kingdom': ['EGVA', 'EGVN'], 'Syktyvkar, Russia': ['UUYY', "NaN"], "Syzran', Russia": ['RU-2344', 'UWWW'], 'Szczecin, Poland': ['EPSC', 'EDAH'], 
                    'Szeged, Hungary': ['LHKE', 'LRAR'], 'Taganrog, Russia': ['RU-0211', 'URRT'], 'Tallinn, Estonia': ['EETN', 'EEEI'], 'Tambov, Russia': ['RU-4339', 'UUOT'], 'Tampere, Finland': ['EFTP', 'EFHA'], 
                    'Tarento, Italy': ['LIBG', 'LIBV'], 'Targu Mures, Romania': ['LRTM', 'LRCT'], 'Tarnów, Poland': ['EPRZ', 'EPKK'], 'Tarragona, Spain': ['LERS', 'LEBL'], 'Telford, United Kingdom': ['EGWC', 'EGOS'], 
                    'Terni, Italy': ['LIRV', 'LIRZ'], "Ternopil', Ukraine": ['UKLH', 'UKLI'], 'Terrassa, Spain': ['LEBL', 'ES-0109'], 'Thessalonike, Greece': ['LGTS', 'LGKV'], 'Tilburg, Netherlands': ['EHGR', 'EHEH'], 
                    'Timisoara, Romania': ['LRTR', 'LRAR'], 'Tirana, Albania': ['LATI', 'LAKV'], 'Tiraspol, Moldavia': ['LUTR', 'LUKK'], "Tol'iatti, Russia": ["NaN", "NaN"], 'Torrejón de Ardoz, Spain': ['LETO', 'LEMD'], 
                    'Torun, Poland': ['EPIR', 'EPBY'], 'Toulon, France': ['LFTH', 'LFMQ'], 'Toulouse, France': ['LFBO', 'LFBF'], 'Tours, France': ['LFOT', 'LFRM'], 'Trento, Italy': ['LIDT', 'LIPB'], 
                    'Trier, Germany': ['ETAD', 'ELLX'], 'Trieste, Italy': ['LJPZ', 'LIPQ'], 'Trondheim, Norway': ['ENVA', 'ENOL'], 'Tula, Russia': ['UUBC', 'RU-3686'], 'Turin, Italy': ['LIMA', 'LIMF'], 
                    'Turku, Finland': ['EFTU', 'EFPO'], 'Tuzla, Bosnia and Herzegovina': ['LQTZ', 'LQSA'], "Tver', Russia": ['UUEM', 'RU-9937'], 'Tychy, Poland': ['EPKT', 'EPKK'], 'Ufa, Russia': ['UWUU', "NaN"], 
                    "Ul'ianovsk, Russia": ["NaN", "NaN"], 'Ulm, Germany': ['ETHL', 'EDJA'], 'Uppsala, Sweden': ['ESSA', 'ESSB'], 'Utrecht, Netherlands': ['EHAM', 'EHLE'], 'Uzhgorod, Ukraine': ['UKLU', 'LZKZ'], 
                    'Valladolid, Spain': ['LEVD', 'LESA'], 'València, Spain': ['LEVC', 'LECH'], 'Vantaa, Finland': ['EFHK', 'EFPR'], 'Varna, Bulgaria': ['LBWN', 'LBWB'], 'Velikii Novgorod, Russia': ['RU-9345', 'RU-10055'], 
                    'Venezia, Italy': ['LIPZ', 'LIPH'], 'Verona, Italy': ['LIPX', 'LIPO'], 'Vicenza, Italy': ['LIPU', 'LIDT'], 'Vigo, Spain': ['LEVX', 'LPBR'], 'Vila Nova de Gaia, Portugal': ['LPPR', 'LPVL'], 
                    'Villeurbanne, France': ['LFLY', 'LFLL'], 'Vilnius, Lithuania': ['EYVI', 'EYKA'], 'Vinnitsia, Ukraine': ['UKWW', 'LUBM'], 'Vitoria, Spain': ['LEVT', 'LELO'], 'Vitsebsk, Viciebsk, Belarus': ['UMII', 'BY-0001'], 
                    'Vladikavkaz, Russia': ['URMO', 'URMS'], 'Vladimir, Russia': ['RU-10048', 'UUBI'], 'Volgodonsk, Russia': ["NaN", "NaN"], 'Volgograd, Russia': ['URWW', 'RU-0304'], 'Vologda, Russia': ["NaN", "NaN"], 
                    'Volzhskii, Russia': ["NaN", "NaN"], 'Voronezh, Russia': ['RU-8363', 'UUOO'], 'Västerås, Sweden': ['ESOW', 'ESSU'], 'Wakefield, United Kingdom': ['EGNM', 'EGXG'], 'Walbrzych, Poland': ['EPWR', 'LKPD'], 
                    'Walsall, United Kingdom': ['EGBB', 'EGWC'], 'Warszawa, Poland': ['EPWA', 'EPMO'], 'Wien, Austria': ['LOWW', 'LOAN'], 'Wiesbaden, Germany': ['ETOU', 'EDFZ'], 'Winterthur, Switzerland': ['LSMD', 'LSZH'], 
                    'Wloclawek, Poland': ['EPIR', 'EPLY'], 'Wolfsburg, Germany': ['EDVE', 'ETHC'], 'Wolverhampton, United Kingdom': ['EGWC', 'EGBB'], 'Wroclaw, Poland': ['EPWR', 'EPKS'], 'Wuppertal, Germany': ['EDDL', 'EDLW'], 
                    'Würzburg, Germany': ['ETHN', 'EDQA'], 'York, United Kingdom': ['EGXG', 'EGXZ'], 'Zaanstad, Netherlands': ['EHAM', 'EHLE'], 'Zabrze, Poland': ['EPKT', 'EPKK'], 'Zagreb, Croatia': ['LDZA', 'LJCE'], 
                    'Zaporizhzhia, Ukraine': ['UKDE', 'UKDD'], 'Zaragoza, Spain': ['LEZG', 'LEDA'], 'Zhitomir, Ukraine': ['UKKO', 'UA-0025'], 'Zhukovskii, Russia': ["NaN", "NaN"], 'Zielona Góra, Poland': ['EPZG', 'EDBR'], 
                    'Zoetermeer, Netherlands': ['EHRD', 'EHAM'], 'Zwolle, Netherlands': ['EHLE', 'EHDL'], 'Zürich, Switzerland': ['LSMD', 'LSZH'], 'bat`umi, Georgia': ["NaN", "NaN"], 'k`ut`aisi, Georgia': ["NaN", "NaN"], 
                    'rust`avi, Georgia': ["NaN", "NaN"], 'tbilisi, Georgia': ['UG24', 'UGTB'], 'Amsterdam, Netherlands': ['EHAM', 'EHLE'], 'Örebro, Sweden': ['ESOE', 'ESKK'], 'Hertogenbosch, Netherlands': ['EHEH', 'EHVK'],
                    'Heraklion, Greece': ['LGIR', 'LGST'], 'Belfast, United Kingdom': ['EGAC', 'EGAA'], 'Cork, Republic of Ireland': ['EICK', 'EIKY'], 'Dublin, Republic of Ireland': ['EIDW', 'EIME'], 'Palma, Spain': ['LEPA', 'LEIB'], 
                    'Rhodes, Greece': ['LGRP', 'LTBS'], 'Cagliari, Italy': ['LIEE', 'LIED'], 'Sassari, Italy': ['LIEO', 'LIEA'], 'Catania, Italy': ['LICC', 'LICZ'], 'Messina, Italy': ['LICR', 'LICC'], 'Palermo, Italy': ['LICP', 'LICJ'], 
                    'Siracusa, Italy': ['LICC', 'LICZ']}

SPANISH_CITIES = [c for c in CONTINENTAL_EUROPEAN_CITIES if ", Spain" in c]

# ─────────────── 1. MAPEO DE TERRITORIOS ─────────────────────────────

SPANISH_CITIES = [c for c in CONTINENTAL_EUROPEAN_CITIES if ", Spain" in c]

TERRITORY_DICTS: dict[str, list[str]] = {
    "CONTINENT": CONTINENTAL_EUROPEAN_CITIES,
    "IRELAND":   IRELAND,
    "SICILY":    SICILY,
    "SARDINIA":  SARDINIA,
    "SPAIN":     SPANISH_CITIES,
}
TERRITORY_OF = {
    city: terr for terr, cities in TERRITORY_DICTS.items() for city in cities
}

# ─────── 2. GRAFO FERROVIARIO (descarga + caché) ─────────────────────
RAIL_GRAPH_PATH = "europe_rail.graphml"
if os.path.exists(RAIL_GRAPH_PATH):
    log("✓ Grafo ferroviario cargado desde disco.")
    G_rail = ox.load_graphml(RAIL_GRAPH_PATH)
else:
    log("• Descargando mosaicos ferroviarios de Europa (una sola vez)…")
    north, south, east, west = 72.0, 34.0, 32.0, -25.0
    step = 5
    rail_filter = (
        '["railway"~"rail|light_rail|subway|tram|monorail|funicular|narrow_gauge"]'
    )
    tile_paths: list[str] = []

    for lat in range(int(south), int(north), step):
        for lon in range(int(west), int(east), step):
            tile_file = f"europe_rail_tile_{lat}_{lon}.graphml"
            if os.path.exists(tile_file):
                tile_paths.append(tile_file)
                continue
            bbox = (lat + step,   # north
                    lat,          # south
                    lon + step,   # east
                    lon)          # west

            try:
                G_tile = ox.graph_from_bbox(
                    bbox,
                    network_type="all_private",   # obligatorio cuando usamos custom_filter
                    custom_filter=rail_filter,
                    retain_all=True,
                )
                ox.save_graphml(G_tile, tile_file)
                tile_paths.append(tile_file)
                log(f"  ✓ guardado {tile_file}")
            except Exception as e:
                log(f"  ✗ error en mosaico ({lat},{lon}) – {e}")
            time.sleep(2)

    G_rail = nx.compose_all(ox.load_graphml(p) for p in tile_paths)
    ox.save_graphml(G_rail, RAIL_GRAPH_PATH)
    log("✓ Grafo ferroviario combinado guardado en disco.")

# ─────── 3. GRAFO VIAL ESPAÑA + NODOS CERCANOS ───────────────────────
log("• Cargando grafo vial de España…")
G_drive = ox.graph_from_place("Spain", network_type="drive", simplify=True, retain_all=True)
log("  ✓ grafo vial listo – nodos:", len(G_drive.nodes))

@lru_cache(maxsize=None)
def _nearest_drive_node(city: str) -> int | None:
    if city not in SPANISH_CITIES:
        return None
    lat, lon = city_coords[city]
    try:
        return ox.distance.nearest_nodes(G_drive, lon, lat)
    except (KeyError, ValueError):
        return None

@lru_cache(maxsize=None)
def car_distance_km(city_a: str, city_b: str) -> float | None:
    na = _nearest_drive_node(city_a)
    nb = _nearest_drive_node(city_b)
    if na is None or nb is None:
        return None
    try:
        metres = nx.shortest_path_length(G_drive, na, nb, weight="length")
        return round(metres / 1000, 1)
    except nx.NetworkXNoPath:
        return None

# ─────── 4. BASES DE DATOS DE VUELOS Y TRENES ────────────────────────
plane_db = mlc.Dataset("https://githubusercontent.com/EDJNet/european_routes/blob/main/data/european_routes_ranking.csv")
data_asset = next(iter(plane_db.data_assets.values()))
plane_db = data_asset.as_dataframe()

rail_db = mlc.Dataset("https://github.com/EDJNet/european_routes/blob/ef44d05cf5f0cf59f635c1f546bd471359f49161/data_train_routes/train_routes.csv")
data_asset = next(iter(rail_db.data_assets.values()))
rail_db = data_asset.as_dataframe()


# ─────── 5. GEOCODIFICACIÓN CON CACHÉ ────────────────────────────────
GEOCODE_JSON = "city_coords.json"
if os.path.exists(GEOCODE_JSON):
    with open(GEOCODE_JSON) as fp:
        city_coords: dict[str, tuple[float, float]] = {
            k: tuple(v) for k, v in json.load(fp).items()
        }
else:
    log("• Geocodificando todas las ciudades (puede tardar)…")

    @lru_cache(maxsize=None)
    def _geocode_city(name: str) -> tuple[float, float]:
        return ox.geocode(name)

    EUROPEAN_CITIES = (
        CONTINENTAL_EUROPEAN_CITIES
        + IRELAND
        + SICILY
        + SARDINIA
    )
    city_coords = {c: _geocode_city(c) for c in EUROPEAN_CITIES}
    with open(GEOCODE_JSON, "w") as fp:
        json.dump(city_coords, fp)

# ─────── 6. BUCLE PRINCIPAL DE DISTANCIAS ─────────────────────────────
rows: list[dict[str, object]] = []
all_cities = list(city_coords)

log("• Calculando distancias entre pares de ciudades…")
for orig, dest in combinations(all_cities, 2):
    terr_o, terr_d = TERRITORY_OF.get(orig), TERRITORY_OF.get(dest)
    same_terr = terr_o == terr_d

    coord_o, coord_d = city_coords[orig], city_coords[dest]

    row_fwd = {
    "ciudad_proc": orig,
    "ciudad_dest": dest,
    "dist_carretera": float("nan"),   #  <-- new
    "dist_vía": float("nan"),
    "dist_aire": float("nan"),
}
    row_rev = row_fwd.copy()
    row_rev["ciudad_proc"], row_rev["ciudad_dest"] = dest, orig
    

    if terr_o == terr_d == "SPAIN":
        km = car_distance_km(orig, dest)
        if km is not None:
            row_fwd["dist_carretera"] = row_rev["dist_carretera"] = km

    if same_terr and terr_o in {"CONTINENT", "IRELAND"}:
        if (orig, dest) in rail_db.index:
            try:
                node_o = ox.distance.nearest_nodes(G_rail, coord_o[1], coord_o[0])
                node_d = ox.distance.nearest_nodes(G_rail, coord_d[1], coord_d[0])
                km = nx.shortest_path_length(G_rail, node_o, node_d, weight="length") / 1000
                row_fwd["dist_vía"] = row_rev["dist_vía"] = round(km, 1)
            except nx.NetworkXNoPath:
                pass

    if (not same_terr) or (terr_o == terr_d == "CONTINENT"):
        if (orig, dest) in rail_db.index:
            km = round(geodesic(coord_o, coord_d).kilometers, 1)
            row_fwd["dist_aire"] = row_rev["dist_aire"] = km

    rows.extend([row_fwd, row_rev])

# ─────── 7. EXPORTACIÓN A EXCEL ───────────────────────────────────────
df = pd.DataFrame(rows, columns=["ciudad_proc", "ciudad_dest",
        "dist_carretera", "dist_vía", "dist_aire"])
df2 = df.copy()
# Guardamos con el nombre coherente usado por los otros scripts
df2.to_excel("dataset_distancias_europa.xlsx", index=False)
log("✓ Archivo Excel generado con todas las distancias calculadas – filas:", len(df))

"""
SCRIPT 2: SIMULACIÓN DE EVENTOS
"""

import math
import os
import warnings
from functools import lru_cache
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import osmnx as ox

# ---------- PARÁMETROS ----------------------------------------------
DATASET_XLSX = Path("dataset_distancias_europa.xlsx")
if not DATASET_XLSX.exists():
    raise SystemExit("No se encuentra dataset_distancias_europa.xlsx – ejecútalo primero.")

TOTAL_OBS = 300                     # muestras a generar
DESTINO_FINAL = "Madrid, Spain"     # sede del congreso
KM_LOCAL_SEDE = (2, 60)             # reparto local en Madrid (uniforme)

# Factores de emisión (kg CO₂ por km)
EF_CO2 = {
    "coche"    : 0.164,
    "tren"     : 0.035,
    "avion"    : 0.246,
    "camion"   : 0.307,
    "furgoneta": 0.161,
    "bus"      : 0.035,
}

# ---------- CARGA DE DISTANCIAS --------------------------------------
# ---------- CARGA DE DISTANCIAS --------------------------------------
log("• Cargando matriz de distancias…")
xdist = (
    pd.read_excel(DATASET_XLSX, dtype=float)      # 1 sola lectura
      .drop_duplicates(subset=["ciudad_proc", "ciudad_dest"])
      .set_index(["ciudad_proc", "ciudad_dest"]) # acceso O(1)
)

lookup = xdist.drop_duplicates(subset=["ciudad_proc", "ciudad_dest"]).set_index(["ciudad_proc", "ciudad_dest"])

CIUDADES     = list({*xdist.index.get_level_values(0),
                     *xdist.index.get_level_values(1)})
CIUDADES_ES  = [c for c in CIUDADES if ", Spain" in c]
# Acceso rápido por pares (origen, destino) en MultiIndex

# ---------- UTILIDADES GEOGRÁFICAS -----------------------------------
from math import radians, sin, cos, atan2, sqrt

with open("city_coords.json") as fh:
    _CITY_COORDS = {k: tuple(v) for k, v in json.load(fh).items()}

@lru_cache(maxsize=None)
def _coords(city: str) -> Tuple[float, float]:
    """Devuelve (lat, lon) usando el JSON ya guardado; si falta, geocodea 1 vez."""
    return _CITY_COORDS.get(city) or ox.geocode(city)

# Solo para distancias de control cuando no hay valor en el Excel
EARTH_R = 6371.0

def _haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    lat1, lon1 = a; lat2, lon2 = b
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    h = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return 2 * EARTH_R * atan2(sqrt(h), sqrt(1 - h))

# ---------- FUNCIÓN CENTRAL DE DISTANCIA -----------------------------

def distancia_ciudades(ciudad1: str, ciudad2: str, modo: str) -> float:
    # Trayecto urbano en la sede del congreso
    if ciudad1 == ciudad2 == DESTINO_FINAL:
        return float(np.random.uniform(*KM_LOCAL_SEDE))

    col = {
        "camion": "dist_carretera", "furgoneta": "dist_carretera",
        "coche" : "dist_carretera", "bus"      : "dist_carretera",
        "tren"  : "dist_vía",       "avion"    : "dist_aire",
    }[modo]

    # Acceso rápido ida/vuelta en el DataFrame indexado
    try:
        dist = float(xdist.at[(ciudad1, ciudad2), col])
    except KeyError:
        dist = float(xdist.at[(ciudad2, ciudad1), col]) if (ciudad2, ciudad1) in xdist.index else math.nan

    if not math.isnan(dist):
        return dist

    # Fallback geodésico (factor 1.25 de rodeo)
    return 1.25 * _haversine_km(_coords(ciudad1), _coords(ciudad2))


# ---------- CREACIÓN DEL DATASET -------------------------------------
rows = []
log("• Generando muestras aleatorias…")
for obs in range(1, TOTAL_OBS + 1):
    es_catering = np.random.rand() < 0.10
    origen = np.random.choice(CIUDADES_ES if es_catering else CIUDADES)
    es_espanol = ", Spain" in origen

    # Posible escala (≤ 1000 km en línea recta) --------------------------------
    escala = None
    if np.random.rand() < 0.15:
        candidatas = [c for c in CIUDADES if c != origen and _haversine_km(_coords(origen), _coords(c)) < 1000]
        if candidatas:
            escala = np.random.choice(candidatas)

    # Inicializar kilómetros por modo
    km: Dict[str, float] = {k: 0.0 for k in EF_CO2}

    if es_catering:
        modo = np.random.choice(["camion", "furgoneta"])
        km[modo] += distancia_ciudades(origen, DESTINO_FINAL, modo)
    else:
        solo_avion = not es_espanol
        modo1 = np.random.choice(["avion"] if solo_avion else ["coche", "tren", "bus", "avion"])
        km[modo1] += distancia_ciudades(origen, escala or DESTINO_FINAL, modo1)
        if escala:
            modo2 = np.random.choice(["avion"] if solo_avion else ["coche", "tren", "bus", "avion"])
            km[modo2] += distancia_ciudades(escala, DESTINO_FINAL, modo2)

    # Ida y vuelta ------------------------------------------------------
    for m in km:
        km[m] *= 2

    huella = sum(km[m] * EF_CO2[m] for m in km)
    rows.append({
        "obs": obs,
        "sede_origen": origen,
        "es_catering": es_catering,
        **{f"km_{m}": round(km[m], 2) for m in km},
        "huella_CO2_kg": round(huella, 2),
    })

# ---------- GUARDADO A DISCO -----------------------------------------
log("• Guardando CSVs…")
df = pd.DataFrame(rows)
df.to_csv("caso2.csv", index=False)
pd.get_dummies(df, columns=["sede_origen"], drop_first=True).to_csv("caso2_dummy.csv", index=False)
log("✓ Listo – caso2.csv y caso2_dummy.csv creados.")

"""
SCRIPT 3: MODELO
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
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

# ── 1) CARGAR EL DATASET ────────────────────────────────────────────────
CSV_PATH = "caso2_dummy.csv"

df = pd.read_csv(CSV_PATH)
X = df.drop(columns=["huella_CO2_kg", "obs"])
y = df["huella_CO2_kg"] 

# ── 2) TRAIN / TEST SPLIT ───────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42
)

# ── 3) DEFINICIÓN DE CINCO MODELOS ─────────────────────────────────────
models = [
    RandomForestRegressor(max_depth=3, n_estimators=50 , min_samples_leaf=5, max_features="sqrt", random_state=42),
    RandomForestRegressor(max_depth=3, n_estimators=100, min_samples_leaf=5, max_features="sqrt", random_state=42),
    RandomForestRegressor(max_depth=3, n_estimators=100, min_samples_leaf=5, max_features="sqrt", criterion="absolute_error", random_state=42),
    RandomForestRegressor(max_depth=3, n_estimators=150, min_samples_leaf=5, max_features="sqrt", random_state=42),
    RandomForestRegressor(max_depth=3, n_estimators=150, min_samples_leaf=5, max_features="sqrt", criterion="absolute_error", random_state=42),
]

# ── 4) FUNCIÓN AUXILIAR PARA CALCULAR MAE ─────────────────────────────

def score_model(model):
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    return mean_absolute_error(y_test, pred)

# ── 5) TRACKER CODECARBON ──────────────────────────────────────────────
tracker.start()

for idx, mdl in enumerate(models, start=1):
    mae = score_model(mdl)
    log(f"MAE del modelo {idx}: {mae:.2f} kg CO₂")

tracker.stop()
log("Proceso finalizado. Consulta 'emissions.csv' para ver la energía consumida.")

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
    # 1. Inicializar calculadora
    calculator = CarbonCalculator()
    
    # 2. Definir la huella de carbono (kg CO2)
    huella_co2 = 7500  # Este es el valor que debes cambiar por tu huella real
    
    # 3. Calcular todas las opciones
    log("\nCalculando opciones de compensación...\n")
    opciones = calculator.compare_reforestation_options(
        total_co2=huella_co2,
        tree_age_pinus=15,
        tree_size_quercus='medium'
    )
    
    # 4. Selección programática directa (elige una de estas tres líneas)
    opcion_elegida = opciones['100_quercus']  # Opción 1: 100% Quercus
    # opcion_elegida = opciones['50_50_mix']   # Opción 2: 50% Quercus - 50% Pinus
    # opcion_elegida = opciones['100_pinus']   # Opción 3: 100% Pinus
    
    # 5. Mostrar resultados de la opción seleccionada
    log("\n=== OPCIÓN SELECCIONADA ===")
    log(f"{opcion_elegida['name']}")
    log(f"Descripción: {opcion_elegida['description']}")
    log(f"\nPara compensar {huella_co2} kg de CO2:")
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
