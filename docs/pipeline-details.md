# 🔧 Pipeline
 Il progetto si sviluppa in fasi separate, tutti i vari parametri del progetto sono visionabili e modificabili sul bisogno in [`config.py`](../config.py)
 ## 1. 🗂️ Creazione del Dataset
 La creazione del Dataset è spiegato nella sezione [apposita](./dataset-creation.md) essendo abbastanza complicata

 ## 2. 🔪 Slicer
 Dato il file originale, si usa lo script [`slicer.py`](../slicer.py) per segmentare in tile più gestibili di dimensioni configurabili. 
 Le tile vengono create in maniera sequenziale aggiungendo ad una dimensione di core (512x512px per esempio) un padding (64px per lato) per dare del contesto extra all'inpainter durante la generazione.

 ## 3. ✍ Autocaptioning
 Una volta generata la lista di tiles bisogna scrivere delle caption per ciascuna patch, questa caption verrà concatenata ad una descrizione più generica per l'inpainting,
 per quanto un captioning manuale sarebbe ottimale e produce risultati di gran lunga migliore, non è possibile descrivere a mano una così grossa serie di immagini, per cui
 lo script [`autocaptioner.py`](../autocaptioner.py) va a creare un file `.txt` con lo stesso nome dell'immagine che va a descrivere. Questo script usa un [workflow](workflows/autocaptioner.json)
 ComfyUI con modello di captioning [microsoft/florence-2-base](https://huggingface.co/microsoft/Florence-2-base), lo script usa l'API del workflow per eseguire il captioning.

 ## 4. 🎨 Inpainting
 Nello script [multi-patch_applier.py](../multi-patch_applier.py) si passa tramite API al [workflow](workflow/Raffaello_the_Inpainter.json) ComfyUI una per una tutta le immagini con relative maschere e caption al modello di Inpainting.
 
 Questo è strutturato 

 ## 5. 🪡 Patch Stitcher
