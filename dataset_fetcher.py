import os
import json
import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm
# ==========================
# CONFIGURAZIONE
# ==========================

OUTPUT_DIR = "dataset_raw"
IMAGE_DIR = os.path.join(OUTPUT_DIR, "images")
METADATA_FILE = os.path.join(OUTPUT_DIR, "metadata.json")
USER_AGENT = "SD-Dataset-Bot/1.1 (research)"

# ==========================
# SESSIONE REQUESTS CON RETRY
# ==========================

# Configurazione Retry (Backoff Esponenziale)
retry_strategy = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

# Creazione della Sessione
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)
http.headers.update({"User-Agent": USER_AGENT})

# ==========================
# COSTANTI
# ==========================
MIN_WIDTH = 2000
MIN_HEIGHT = MIN_WIDTH

# Endpoint SPARQL di Wikidata
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

#query SPARQL
SPARQL_QUERY = """
SELECT ?item ?itemLabel ?image ?height_px ?width_px
        (SAMPLE(?samples_years) as ?year)
        (SAMPLE(?physHeight) as ?height)
        (SAMPLE(?physWidth) as ?width)
WHERE {
  ?item wdt:P31 wd:Q3305213 ;
        wdt:P170 wd:Q5597 ;
        wdt:P18 ?image ;
        wdt:P2048 ?physHeight ;
        wdt:P2049 ?physWidth .
  
  #Filtro sul tipo di materiale, quindi si filtra per cercare dipinti oli su tela 
  ?item wdt:P186 ?materiale .
  FILTER(?materiale = wd:Q296955 || ?materiale = wd:Q134627)
  
  #Anno di creazione (solo anno)
  ?item wdt:P571 ?inception . 
  BIND(YEAR(?inception) AS ?samples_years)
  
  # --- Ritiro informazioni sulla foto ----
  
  BIND(STRAFTER(wikibase:decodeUri(STR(?image)), "http://commons.wikimedia.org/wiki/Special:FilePath/") AS ?fileTitle)

  SERVICE wikibase:mwapi {
    bd:serviceParam wikibase:endpoint "commons.wikimedia.org";
                    wikibase:api "Generator";
                    wikibase:limit "once";
                    mwapi:generator "allpages";
                    mwapi:gapfrom ?fileTitle;
                    mwapi:gapnamespace 6; # NS_FILE
                    mwapi:gaplimit 1;
                    mwapi:prop "imageinfo";
                    mwapi:iiprop "dimensions".
    ?size wikibase:apiOutput "imageinfo/ii/@size".
    ?width_px wikibase:apiOutput "imageinfo/ii/@width".
    ?height_px wikibase:apiOutput "imageinfo/ii/@height".
  }
  
  #filtro sulla dimensione del file
  FILTER(xsd:integer(?width_px) > """+ str(MIN_WIDTH) +""" && xsd:integer(?height_px) > """+ str(MIN_HEIGHT) +""") 

  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
}
GROUP BY ?item ?itemLabel ?image ?height_px ?width_px
"""

# ==========================
# FUNZIONI
# ==========================

def ensure_dirs():
    os.makedirs(IMAGE_DIR, exist_ok=True)
"""
def fetch_sparql_results():

    print("Esecuzione della query SPARQL su Wikidata...")
    params = {
        'query': SPARQL_QUERY,
        'format': 'json'
    }
    headers = {'User-Agent': USER_AGENT}
    
    try:
        response = requests.get(SPARQL_ENDPOINT, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Errore durante la query SPARQL: {e}")
        return None

def download_image(url, filename):

    path = os.path.join(IMAGE_DIR, filename)
    
    # Se il file esiste già, lo saltiamo
    if os.path.exists(path):
        return True

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "image/*"
    }

    try:
        # stream=True è importante per file grandi
        with requests.get(url, headers=headers, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"Errore download {filename}: {e}")
        return False
"""

def fetch_sparql_results():
    print("Esecuzione della query SPARQL su Wikidata...")
    params = {'query': SPARQL_QUERY, 'format': 'json'}
    
    try:
        # Usa la sessione 'http' creata sopra
        response = http.get(SPARQL_ENDPOINT, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Errore query SPARQL: {e}")
        return None

def download_image(url, filename):
    path = os.path.join(IMAGE_DIR, filename)
    
    if os.path.exists(path):
        return True

    try:
        # stream=True scarica il file a pezzi senza riempire la RAM
        with http.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    
    except requests.exceptions.HTTPError as e:
        # Se dopo tutti i retry fallisce ancora (es. 404 Not Found reale)
        if e.response.status_code == 429:
            print(f"Skipping {filename}: Troppe richieste (429) persistente.")
        else:
            print(f"Errore HTTP {filename}: {e}")
        return False
        
    except Exception as e:
        print(f"Errore generico {filename}: {e}")
        return False

# ==========================
# MAIN
# ==========================

def main():
    ensure_dirs()
    
    # 1. Ottieni i dati dalla Query
    data = fetch_sparql_results()
    if not data:
        return

    results = data['results']['bindings']
    print(f"Trovate {len(results)} opere che soddisfano i criteri.")
    
    all_metadata = []

    # 2. Itera sui risultati e scarica
    for result in tqdm(results, desc="Download immagini"):
        
        # Estrazione dati dal JSON SPARQL
        item_url = result['item']['value']
        title = result['itemLabel']['value']
        image_url = result['image']['value']
        width_px = result['width_px']['value']
        height_px = result['height_px']['value']
        year = result['year']['value']
        width = result['width']['value']
        height = result['height']['value']
        
        # Pulizia nome file (prende l'ultima parte dell'URL e rimuove caratteri strani)
        # L'URL è tipo http://commons.../Special:FilePath/NomeFile.jpg
        file_name = image_url.split("Special:FilePath/")[-1]
        file_name = requests.utils.unquote(file_name) # Decodifica %20 in spazi
        # Rimuovi caratteri non validi per il filesystem
        safe_filename = "".join([c for c in file_name if c.isalpha() or c.isdigit() or c in (' ', '.', '_', '-')]).strip()
        
        # Metadata locale
        meta = {
            "title": title,
            "year": year,
            "wikidata_id": item_url.split("/")[-1],
            "filename": safe_filename,
            "width":  float(width),
            "height": float(height),
            "source_url": image_url,
            "height_px": int(height_px),
            "width_px": int(width_px)
        }
        
        # 3. Scarica
        success = download_image(image_url, safe_filename)
        
        if success:
            all_metadata.append(meta)
            # Pausa di cortesia per non sovraccaricare il server (opzionale ma consigliata)
            time.sleep(2.0) 

    # 4. Salva il file JSON riassuntivo
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, indent=2, ensure_ascii=False)

    print(f"\nOperazione completata. Dataset salvato in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()