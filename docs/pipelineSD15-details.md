[🏠 Home](../README.md) | [🛠️ Pipeline SDXL](./pipelineXL-details.md)| [🛠️ Pipeline SD 1.5](./pipelineSD15-details.md) |  [🗂️ Dataset](./dataset-details.md) | [🖼️ Galleria](./gallery.md)
# 🔧 Pipeline
 Il progetto si sviluppa in fasi separate, tutti i vari parametri del progetto sono visionabili e modificabili sul bisogno in [`config.py`](../config.py)
 ## 1. 🗂️ Creazione del Dataset
 La creazione del Dataset per l'addestramento del **LoRA** è spiegato nella sezione [apposita](./dataset-details.md) essendo un processo abbastanza complesso

 ## 2. 🔪 Slicer
 Dato il file originale, si usa lo script [`slicer.py`](../slicer.py) per segmentare in tile più gestibili di dimensioni configurabili. 
 Le tile vengono create in maniera sequenziale aggiungendo ad una dimensione di core (512x512px per esempio) un padding (64px per lato) per dare del contesto extra all'inpainter durante la generazione.
Per evitare di fare lavoro in più rispetto al dovuto, vengono generate solo tiles aventi maschera non completamente nera, il nome del file è generato univocamente attraverso le coordinate della tile che rappresenta.

 ## 3. ✍ Autocaptioning
 Una volta generata la lista di tiles bisogna scrivere delle caption per ciascuna patch, questa caption verrà concatenata ad una descrizione più generica per l'inpainting,
 per quanto un captioning manuale sarebbe ottimale e produce risultati di gran lunga migliore, non è possibile descrivere a mano una così grossa serie di immagini, per cui
 lo script [`autocaptioner.py`](../autocaptioner.py) va a creare un file `.txt` con lo stesso nome dell'immagine che va a descrivere. Questo script usa un [workflow](workflows/autocaptioner.json)
 ComfyUI con modello di captioning [microsoft/florence-2-base](https://huggingface.co/microsoft/Florence-2-base), lo script usa l'API del workflow per eseguire il captioning.

 ## 4. 🎨 Inpainting
 Nello script [`multi-patch_applier.py`](../multi-patch_applier.py) si passa tramite API al [workflow](workflow/Raffaello_the_Inpainter.json) ComfyUI una per una tutta le immagini con relative maschere e caption al modello di Inpainting.
 
#### 4.1 🔎​ Analisi del Workflow ComfyUI
Il file JSON incluso utilizza una strategia a triplo controllo:

* **Base Model**: Utilizza `dreamshaper_8Inpainting.safetensors`, un modello checkpoint specificamente finetunato per l'inpainting, garantendo una coerenza di base superiore a SD standard.
* **Style Transfer (IP-Adapter)**:
    * Utilizza `IPAdapter Plus (high strength)` per iniettare lo stile dell'immagine originale direttamente nel processo di generazione, riducendo la dipendenza dal prompt testuale e così da diminuire le allucinazioni, rendendo l'inpainting più coerente col contesto.
    * Configurato su "Style Transfer".
* **Struttura (ControlNet)**:
    * Utilizza `control_v11p_sd15_softedge` (con preprocessore Soft Edge) per mantenere intatti i bordi e la composizione originale dell'area mascherata.
* **Tiling (ControlNet)**:
   * Utilizza `control-v11f1e_sd15_tile` (con preprocessore Tile) per indirizzare la generazione verso il tiling
* **LoRA Injection**: Il LoRA `RaffaelloStyle.safetensors` viene caricato per applicare lo stile specifico.

Il modello risultante dalla combinazione (non in ordine) di queste componenti, viene passato ad un doppio passaggio di KSampler, per cristallizzare i dettagli della prima generazione, l'immagine ottenuta viene applicata come maschera all'immagine originale e salvata nella folder con tutte le altre tiles generate.


 ## 5. 🪡 Patch Stitcher
 Inversamente allo slicer, le tiles generate vengono rimesse sull'immagine originale sulla base delle coordinate presenti nel nome del file, producendo l'immagine finale.
