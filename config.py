import os

# ==============================================================================
# PERCORSI BASE (PATHS)
# ==============================================================================

# Ottiene la cartella in cui si trova QUESTO file config.py
# Utile per evitare errori se lanci gli script da posizioni diverse
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STENDARDO_PATH = os.path.join(BASE_DIR,"stendardo")

# File di input originali (Giganti)
SRC_IMAGE_PATH = os.path.join(STENDARDO_PATH, "img/Trinita_25perc.png")
SRC_MASK_PATH = os.path.join(STENDARDO_PATH, "mask/Trinita_25perc.png")
FULL_OUTPUT_PATH = os.path.join(STENDARDO_PATH, "Stendardo_Restaurato.png")

# Cartelle di lavoro
# Qui verranno messe le patch ritagliate (Input per ComfyUI)
TILES_DIR = os.path.join(STENDARDO_PATH, "patch_src")
# Qui verranno salvati i risultati di ComfyUI
INPAINTED_DIR = os.path.join(STENDARDO_PATH, "patch_dst")

# File del Workflow API
WORKFLOW_FILE = os.path.join(BASE_DIR, "API-RaffAIello-the-inPainter.json")

# ==============================================================================
# IMPOSTAZIONI TAGLIO (SLICING)
# ==============================================================================
PATCH_CORE_SIZE = 512
OVERLAP = 0  # 64 o 128 per sovrapposizioni, per evitare cuciture visibili
PADDING = 64 # Padding per inpainting, per dare più contesto al modello del singolo tile

# ==============================================================================
# COMFYUI SERVER
# ==============================================================================
COMFY_URL = "http://127.0.0.1:8000"

# ==============================================================================
# ID DEI NODI (Workflow API)
# ==============================================================================
NODE_ID_LOAD_IMAGE = "4"          # Nodo che carica l'immagine principale
NODE_ID_LOAD_MASK = "9"           # Nodo LoadImageMask
NODE_ID_POSITIVE_PROMPT = "3"     # Nodo CLIP Text Encode
NODE_ID_KSAMPLER = "8"            # KSampler (per il seed)
NODE_ID_SAVE_IMAGE = "19"         # Nodo Save Image

# ==============================================================================
# PROMPT SETTINGS
# ==============================================================================
# Per lo script di pulizia prompt
TILE_PREFIX = "tile_"
BAD_TAGS = ["cracks", "damage", "paint loss", "scratches", "texture", "grunge", "ruins", "spots"]
PROMPT_PREFIX = "Raffaello style, restored, high quality, "