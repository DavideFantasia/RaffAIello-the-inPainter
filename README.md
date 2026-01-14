[🏠 Home](./README.md) | [🛠️ Pipeline](./docs/pipeline-details) | [🗂️ Dataset](./docs/dataset-details.md)

# 🖌️ RaffAIello the Inpainter

**RaffAIello** è una pipeline end-to-end per l'inpainting artistico basata sullo stile di Raffaello Sanzio. Il progetto automatizza la creazione di dataset da Wikimedia, elabora patch intelligenti utilizzando computer vision (YOLO + FaceAnalysis) e addestra un modello LoRA per replicare lo stile pittorico rinascimentale per svolgere poi l'inpaiting con flussi di lavoro ComfyUI su quadri danneggiati di Raffaello.

## 🏗️ Caratteristiche Principali

* **Dataset Fetching Automatizzato**: Raccolta immagini ad alta risoluzione da Wikimedia Commons tramite query SPARQL, filtrate per medium (Olio su tela).
* **Smart Patching & Anatomical Priority**: Creazione di dataset di training tramite segmentazione semantica, Face Analysis e Pose Detection per isolare con priorità volti, mani e piedi.
* **Style Training**: Addestramento LoRA su base SD 1.5 (tramite Kohya_ss) specifico per catturare lo stile pittorico di Raffaello.
* **Advanced ComfyUI Workflow**: Pipeline di inferenza ibrida che combina Inpainting tradizionale, ControlNets e IP-Adapter per risultati coerenti.

---
![Comparazione fra patch originale e patch con alcune crepe riempite](docs/img/comparing.png)

