import os
from PIL import Image
import numpy as np

# ================= CONFIGURAZIONE =================
WORK_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/stendardo"
# Percorsi file originali
SRC_IMAGE_PATH = f"{WORK_DIR}/img/trinita.png"
SRC_MASK_PATH = f"{WORK_DIR}/mask/trinita.png"

OUTPUT_DIR = f"{WORK_DIR}/patch_src"  # Dove salvare le patch
PATCH_SIZE = 512
OVERLAP = 0 # 0 per semplicità, per evitare cuciture visibili: ~64

# ==================================================

def slice_image_and_mask():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Carica le immagini originali
    # Nota: PIL carica "lazy",
    # Se si hanno errori di memoria, si può usare la libreria 'vips'
    Image.MAX_IMAGE_PIXELS = None # Disabilita protezione bomba decompressione
    
    print("Caricamento immagine originale...")
    img = Image.open(SRC_IMAGE_PATH).convert("RGB")
    print("Caricamento maschera originale...")
    mask = Image.open(SRC_MASK_PATH).convert("L") # Scala di grigi

    w, h = img.size
    print(f"Dimensioni originali: {w}x{h}")

    # Calcolo righe e colonne
    # Usiamo uno step minore del patch_size se c'è overlap
    step = PATCH_SIZE - OVERLAP
    
    rows = (h // step) + 1
    cols = (w // step) + 1

    count = 0
    
    for row in range(rows):
        for col in range(cols):
            # Calcola coordinate
            x = col * step
            y = row * step
            
            print(f"Creazione patch riga {row+1}/{rows}, colonna {col+1}/{cols} a X={x}, Y={y}...") 

            # Se siamo oltre il bordo, saltiamo o aggiustiamo
            if x + PATCH_SIZE > w: x = w - PATCH_SIZE
            if y + PATCH_SIZE > h: y = h - PATCH_SIZE
            if x < 0: x = 0
            if y < 0: y = 0

            # Ritaglia
            box = (x, y, x + PATCH_SIZE, y + PATCH_SIZE)
            patch_img = img.crop(box)
            patch_mask = mask.crop(box)
            mask_arr = np.array(patch_mask)
            has_damage = np.any(mask_arr > 20) # Soglia minima rumore
            # Nome base con coordinate per il stitching futuro
            # Formato: tile_yY_xX (Y è riga, X è colonna in pixel)
            base_name = f"tile_y{y:05d}_x{x:05d}"

            # Salva sempre l'immagine (ci serve per il contesto o ricostruzione)
            # O save solo se has_damage? Per ricostruire tutto serve tutto.
            # Ma per l'inpainting, processiamo solo quelle rotte.
            
            if has_damage:
                # Salva Immagine
                patch_img.save(os.path.join(OUTPUT_DIR, f"{base_name}.png"))
                # Salva Maschera
                patch_mask.save(os.path.join(OUTPUT_DIR, f"{base_name}_mask.png"))
                # Creiamo un file txt vuoto per ora (lo riempiremo dopo)
                with open(os.path.join(OUTPUT_DIR, f"{base_name}.txt"), "w") as f:
                    f.write("") # Placeholder
                count += 1
            
            # Se NON ha danni, per ora non la salviamo nella cartella di inpainting
            # perché non vogliamo processarla. 
            # MA ATTENZIONE: per ricomporre l'immagine finale, ti serviranno anche i pezzi sani.
            # Consiglio: Salva i pezzi sani in una cartella "sani" separata o copiali dopo.
            
    print(f"Finito! Create {count} patch con danni da processare.")

if __name__ == "__main__":
    slice_image_and_mask()