[🏠 Home](./README.md) | [🛠️ Pipeline SDXL](./docs/pipelineXL-details.md)| [🛠️ Pipeline SD 1.5](./docs/pipelineSD15-details.md) | [🗂️ Dataset](./docs/dataset-details.md) | [🖼️ Galleria](./docs/gallery.md)

# 🖌️ RaffAIello the Inpainter

**RaffAIello** è una pipeline end-to-end per l'inpainting artistico basata sullo stile di Raffaello Sanzio. Il progetto automatizza la creazione di dataset da Wikimedia, elabora patch intelligenti utilizzando computer vision (YOLO + FaceAnalysis) e addestra un modello LoRA per replicare lo stile pittorico rinascimentale per svolgere poi l'inpaiting con flussi di lavoro ComfyUI su quadri danneggiati di Raffaello.

![Comparazione fra patch originale e patch con alcune crepe riempite](docs/img/comparing.png "comparazione del risultato")
vedi la [Galleria](./docs/gallery.md) per più esempi e prompt usati.

## 🏗️ Caratteristiche Principali

* **Dataset Fetching Automatizzato**: Raccolta immagini ad alta risoluzione da Wikimedia Commons tramite query SPARQL, filtrate per medium (Olio su tela).
* **Smart Patching & Anatomical Priority**: Creazione di dataset di training tramite segmentazione semantica, Face Analysis e Pose Detection per isolare con priorità volti, mani e piedi.
* **Style Training**: Addestramento LoRA con architettura SD 1.5 e SDXL (Basato su `Juggernaut XL v8`) tramite `Kohya_ss`, con lo scopo di catturare lo stile pittorico di Raffaello.
---
# 📦 Installazione
Il progetto si compone di due parti: gli script Python per la gestione del dataset/processing e l'ambiente ComfyUI per la generazione.
## 1. Requisiti Python (Scripting)
Per eseguire gli strumenti di fetch, slicing e stitching (`dataset_fetcher.py`, `slicer.py`, `stitcher.py`), è necessario configurare l'ambiente Python locale:
```
git clone https://github.com/DavideFantasia/RaffAIello-the-inPainter.git
cd RaffAIello-the-inPainter
```
E installare le dipendenze del progetto
```
pip install -U -r requirements.txt
```
**Nota**: Il pacchetto insightface richiede Visual Studio C++ Build Tools installati su Windows per la compilazione corretta.
## 2. Configurazione ComfyUI
Per far funzionare la pipeline di inpainting e l'autocaptioner, è necessaria un'installazione funzionante di [ComfyUI](https://github.com/Comfy-Org/ComfyUI)
### Custom Nodes Richiesti
Installa i seguenti nodi personalizzati tramite ComfyUI Manager (*install missing custom nodes*) o clonandoli nella cartella `ComfyUI/custom_nodes`:

#### SD 1.5
<table>
<tr>
<th> ComfyUI </th>
<th> Modelli </th>
</tr>
<tr>
<td>

| Nodi Custom            |
|------------------------|
| ComfyUI-Manager        |
| comfyui_ipadapter_plus |
| comfyui-custom-scripts |
| comfyui-florence2      |
| comfyui-inpaint-nodes  |
| ComfyUI-KJNodes        |
| comfyui_controlnet_aux |
| was-node-suite-comfyui |

</td>
<td>

| Nome Modello               | Percorso                    | Link                                                                                                                                |
|----------------------------|-----------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| dreamshaper_8Inpainting    | `ComfyUI/models/checkpoint` | [🔗](https://huggingface.co/ahtoshkaa/Dreamshaper/blob/d4415d1a2644f08ab34bd7adabfbbb70571a782a/dreamshaper_8Inpainting.safetensors)|
| control_v11f1e_sd15_tile   | `ComfyUI/models/controlnet` | [🔗](https://huggingface.co/lllyasviel/ControlNet-v1-1/blob/main/control_v11f1e_sd15_tile.pth)                                      |
| control_v11p_sd15_softedge | `ComfyUI/models/controlnet` | [🔗](https://huggingface.co/lllyasviel/ControlNet-v1-1/blob/main/control_v11p_sd15_softedge.pth)                                    |
| big-lama                   | `ComfyUI/models/inpaint`    | [🔗](https://github.com/advimman/lama/tree/main)                                                                                    |
| ip-adapter-plus_sd15       | `ComfyUI/models/ipadapter`  | [🔗](https://huggingface.co/h94/IP-Adapter/blob/main/models/ip-adapter-plus_sd15.safetensors)                                       |
| Florence-2-base            | `ComfyUI/models/LLM`        | [🔗](https://huggingface.co/microsoft/Florence-2-base-ft/tree/main)                                                                 |
| CLIP-ViT-H-14-laion2B-s32B-b79K| `ComfyUI\models\clip_vision`| [🔗](https://huggingface.co/laion/CLIP-ViT-H-14-laion2B-s32B-b79K)                                                              |
| RaffaelloStyle             | `ComfyUI/models/loras`      | [🔗](https://huggingface.co/DavideFantasia/RaffaelloStyle) o da trainare                                                            |

</td>
</tr>
</table>

#### SDXL

<table>
<tr>
<th> ComfyUI </th>
<th> Modelli </th>
</tr>
<tr>
<td>

| Nodi Custom            |
|------------------------|
| ComfyUI-Manager        |
| ComfyUI-KJNodes        |
| ComfyUI-Logic          |

</td>
<td>

| Nome Modello               | Percorso                    | Link                                                                                       |
|----------------------------|-----------------------------|--------------------------------------------------------------------------------------------|
| Juggernaut XL    | `ComfyUI/models/checkpoint` | [🔗](https://civitai.com/api/download/models/1759168?type=Model&format=SafeTensor&size=full&fp=fp16)|
| RaffaelloStyleXL | `ComfyUI/models/loras`      | [🔗](https://huggingface.co/DavideFantasia/RaffaelloStyleXL) o da trainare                          |

</td>
</tr>
</table>

⚠️ La lista dei modelli è soggetta a variazioni⚠️

Assicurati che ComfyUI sia in esecuzione all'indirizzo specificato in `config.py` (default: `http://127.0.0.1:8000`) prima di lanciare gli script di inpainting.

## 3. Kohya_ss (Opzionale)

Se si intende ri-addestrare il LoRA sullo stile di Raffaello partendo da zero, è consigliato installare [Kohya_ss GUI](https://github.com/bmaltais/kohya_ss). Il dataset creato con gli script presenti in `dataset/` è già formattato per essere digerito direttamente dagli script di training di Kohya, su cui va seguito il captioning, si consiglia `WD14`, già presente nelle utilities di Kohya, o un qualunque LLM per il captioning (come `Florence-2`) nel caso del LoRA XL.

---

# Esecuzione della pipeline SD 1.5
## Creazione Dataset
Per scaricare le immagini da Wikimedia
```
python ./dataset/dataset_fetcher.py
```
Per la creazione delle patch
```
python ./dataset/patcher_creator.py
```
## Avvio inpainting
**Nota bene**: Per avviare l'inpainting è necessario creare una cartella di lavoro per le immagini, nel caso dello scope di questo progetto, la cartella è `stendardo`. Eventualmente sarà necessario cambiare i percorsi presenti nel file `config.py`
```bat
mkdir stendardo stendardo\img stendardo\mask stendardo\patch_src stendardo\patch_dst
```
Possiamo mettere nella cartella `stendardo/img` e `stendardo/mask` l'immagini di cui vogliamo fare l'inpaint, andando a cambiare il path del file obbiettivo in `config.py`.

### Slicer
Una volta fatto setuppato la cartella di lavoro possiamo avviare lo slicer come:
```bat
python slicer.py 
```
Per segmentare in tiles di dimensione 512+64x512+64px l'immagine target, la dimensione core, il padding e l'eventuale overlapping sono modificabili sempre in `config.py`.
**Nota Bene**: nel caso dello 'stendardo di santissima trinità' su cui il progetto si focalizza, sono presenti molti buchi particolarmente invadenti; è consigliato prima di applicare lo slicing, di 'tappare' anche grossolanamente i buchi, gli esperimenti svolti l'inpainter big-lama usata come pre-processing ha portato a risultati soddisfacenti. Il workflow usato a quello scopo è presente nella cartella `workflows/coarse_fix.json` insieme a tutti gli altri workflow usati.

### Captioning (opzionale)
Il captioning è una parte cruciale della pipeline, essendo che il numero di tiles può crescere molto rapidamente, si mette a disposizione un tool di autocaptioning, che aiuta particolarmente ma necessita di controlli su tiles difficili da descrivere. **Assicurandoci di avere ComfyUI avviato** e con l'indirizzo del server uguale all'indirizzo salvato in `config.py`, possiamo avviare l'autocaptioning:
```bat
python autocaptioner.py
```

### Inpainting
Il core della pipeline è il file `multi-patch_applier.py` che usa il workflow ComfyUI tramite la sua API per applicaare l'inpainting su tutte le patch presenti nella cartella `stendardo/patch_src` concatenando ad un prompt più generico quello più specifico di ogni tile, sempre presente nella cartella delle patch.
```
python multi-patch_applier.py
```
Che riempirà la cartella `stendardo/patch_dst` con i tiles a cui è stato applicato l'inpaint. Successivamente con lo script `stitcher.py` si possonon ricomporre le patch per ottenere l'immagine originale.

---
# Esecuzione della Pipeline XL
⚠️ Sezione soggetta a frequenti Variazioni ⚠️
## Presequisiti
Avendo installato i modelli nei path descritti nella sezione di [Installazione](#-installazione), importate il [workflow XL](./docs/workflow/SDXL) dentro ComfyUI, al momento non sono presenti tool di autosegmentazione per un'inpainting dell'intero quadro, ma è consigliato lavorare a zone di interesse ritaglate a mano.

---

# Future Improvements

- Si vuole procedere con lo sviluppare un tool per permettere di visualizzare, navigare e selezionare le zone di interesse di cui si vuole fare l'inpainting direttamente con un solo esecutivo
