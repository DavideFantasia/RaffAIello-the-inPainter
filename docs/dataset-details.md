[🏠 Home](../README.md) | [🛠️ Pipeline SDXL](./pipelineXL-details.md)| [🛠️ Pipeline SD 1.5](./pipelineSD15-details.md) |  [🗂️ Dataset](./dataset-details.md) | [🖼️ Galleria](./gallery.md)

## 🏗️ Caratteristiche Principali

* **Dataset Fetching Automatizzato**: Raccolta immagini ad alta risoluzione da Wikimedia Commons tramite query SPARQL, filtrate per medium (Olio su tela).
* **Smart Patching & Anatomical Priority**: Creazione di dataset di training tramite segmentazione semantica, Face Analysis e Pose Detection per isolare con priorità volti, mani e piedi.
* **Style Training**: Addestramento LoRA su base SD 1.5 (tramite Kohya_ss) specifico per catturare lo stile pittorico di Raffaello.

---

## 🛠️ Creazione del Dataset

Il processo di creazione è diviso in 3 macro-fasi:

### 1. Data Collection & Preprocessing
#### 1.1 Images Fetching
Utilizziamo una query **SPARQL** nel file `dataset_fetcher.py` per interrogare Wikidata/Wikimedia Commons e scaricare esclusivamente dipinti attribuiti a Raffaello Sanzio (Q5597).
-   **Filtri Rigorosi**: Solo opere "Olio su tela" o tavola, con risoluzione > 2000px.
-   **Output**: Salva metadati JSON e immagini raw in `dataset_raw`.
Si utilizza la seguente query:
```SPARQL
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
```
#### 1.2 Preprocessing
Le immagini grezze vengono processate dal `patcher_creator.py` per creare un dataset ottimizzato (patch 512x512px). La logica di ritaglio non è casuale ma gerarchica:
1.  **FaceAnalysis**: Priorità massima ai volti (dettaglio critico per lo stile rinascimentale).
2.  **YOLOv8 Pose**: Identificazione di keypoints anatomici per salvare mani e piedi, noto punto debole delle IA generative.
3.  **YOLOv8 Seg**: Segmentazione della figura umana completa.
4.  **Background**: Una percentuale (35%) di patch è riservata allo sfondo per apprendere la texture della tela e del muro, filtrando aree piatte o povere di dettagli.

### 2. LoRA Training (`RaffaelloStyle_LoRA`)
Utilizzando il dataset generato, viene addestrato un adattatore **LoRA (Low-Rank Adaptation)**.
-   **Base Model**: Dreambooth 1.5.
-   **Tools**: Script basati su `kohya_ss`.
-   **Labeling**: Generazione automatica di caption descrittive per ogni patch, tramite il modello `WD14 Tagger`.
-   **Obiettivo**: Fitting stilistico controllato per replicare texture, palette cromatica, chiaroscuro e sfumato.
Sono stati usati i seguenti parametri:

| parameter  | value |
| ------------- | ------------- |
| resolution | 512 |
| #images | ~800 |
| epoch  | 2  |
| repeats  | 10  |
| rank | 64 |
| alpha | 32 |
| learning rate | 1e-4 |
---
