[🏠 Home](./README.md) | [🛠️ Pipeline](./docs/pipeline-details.md) | [🗂️ Dataset](./docs/dataset-details.md)

# 🖌️ RaffAIello the Inpainter

**RaffAIello** è una pipeline end-to-end per l'inpainting artistico basata sullo stile di Raffaello Sanzio. Il progetto automatizza la creazione di dataset da Wikimedia, elabora patch intelligenti utilizzando computer vision (YOLO + FaceAnalysis) e addestra un modello LoRA per replicare lo stile pittorico rinascimentale per svolgere poi l'inpaiting con flussi di lavoro ComfyUI su quadri danneggiati di Raffaello.

## 🏗️ Caratteristiche Principali

* **Dataset Fetching Automatizzato**: Raccolta immagini ad alta risoluzione da Wikimedia Commons tramite query SPARQL, filtrate per medium (Olio su tela).
* **Smart Patching & Anatomical Priority**: Creazione di dataset di training tramite segmentazione semantica, Face Analysis e Pose Detection per isolare con priorità volti, mani e piedi.
* **Style Training**: Addestramento LoRA su base SD 1.5 (tramite Kohya_ss) specifico per catturare lo stile pittorico di Raffaello.
* **Advanced ComfyUI Workflow**: Pipeline di inferenza ibrida che combina Inpainting tradizionale, ControlNets e IP-Adapter per risultati coerenti.
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
pip install -r dataset/requirements.txt
```
**Nota**: Il pacchetto insightface richiede Visual Studio C++ Build Tools installati su Windows per la compilazione corretta.
## 2. Configurazione ComfyUI
Per far funzionare la pipeline di inpainting e l'autocaptioner, è necessaria un'installazione funzionante di [ComfyUI](https://github.com/Comfy-Org/ComfyUI)
### Custom Nodes Richiesti
Installa i seguenti nodi personalizzati tramite ComfyUI Manager (*install missing custom nodes*) o clonandoli nella cartella `ComfyUI/custom_nodes`:
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
| RaffaelloStyle             | `ComfyUI/models/loras`      | [🔗](https://huggingface.co/DavideFantasia/RaffaelloStyle) o da trainare                                                            |

</td>
</tr>
</table>

Assicurati che ComfyUI sia in esecuzione all'indirizzo specificato in `config.py` (default: `http://127.0.0.1:8000`) prima di lanciare gli script di inpainting.

## 3. Kohya_ss (Opzionale)

Se si intende ri-addestrare il LoRA sullo stile di Raffaello partendo da zero, è consigliato installare [Kohya_ss GUI](https://github.com/bmaltais/kohya_ss). Il dataset creato con gli script presenti in `dataset/` è già formattato per essere digerito direttamente dagli script di training di Kohya, a cui va seguito il captioning tramite WD14 presente fra le sue utilities.

---
![Comparazione fra patch originale e patch con alcune crepe riempite](docs/img/comparing.png)

