import os
from PIL import Image
import numpy as np
import config  # Importa il tuo file di configurazione

def slice_image_and_mask():
    # 1. Creazione cartella output se non esiste
    if not os.path.exists(config.TILES_DIR):
        os.makedirs(config.TILES_DIR)
        print(f"Creata cartella: {config.TILES_DIR}")

    # 2. Lettura Parametri dal Config
    CORE_SIZE = config.PATCH_CORE_SIZE
    PADDING = config.PADDING
    OVERLAP = config.OVERLAP
    
    # La dimensione totale che andrà a ComfyUI (es. 512 + 64 + 64 = 640)
    TILE_SIZE = CORE_SIZE + (PADDING * 2)

    print(f"--- IMPOSTAZIONI SLICING ---")
    print(f"Input Immagine: {config.SRC_IMAGE_PATH}")
    print(f"Core Size (Area Utile): {CORE_SIZE}px")
    print(f"Padding (Contesto): {PADDING}px")
    print(f"Overlap: {OVERLAP}px")
    print(f"Dimensione Patch Finale: {TILE_SIZE}x{TILE_SIZE}px")
    print(f"----------------------------")

    # Disabilita il limite pixel per immagini grandi
    Image.MAX_IMAGE_PIXELS = None 
    
    # 3. Caricamento Immagini
    try:
        print("Caricamento immagine originale...")
        img = Image.open(config.SRC_IMAGE_PATH).convert("RGB")
        print("Caricamento maschera originale...")
        mask = Image.open(config.SRC_MASK_PATH).convert("L") 
    except FileNotFoundError as e:
        print(f"ERRORE: Impossibile trovare i file di input definiti nel config.\n{e}")
        return

    w, h = img.size
    print(f"Dimensioni Originali: {w}x{h}")

    # 4. Calcolo Griglia
    # Lo step di avanzamento dipende solo dal CORE e dall'OVERLAP
    step = CORE_SIZE - OVERLAP
    
    rows = (h // step) + 1
    cols = (w // step) + 1

    count = 0
    
    for row in range(rows):
        for col in range(cols):
            # Coordinate X, Y dell'angolo in alto a sinistra del CORE
            core_x = col * step
            core_y = row * step
            
            # --- AGGIUSTAMENTO BORDI ---
            # Se il core esce fuori dai bordi (a destra o in basso),
            # lo spostiamo indietro per allinearlo esattamente alla fine dell'immagine.
            if core_x + CORE_SIZE > w: core_x = w - CORE_SIZE
            if core_y + CORE_SIZE > h: core_y = h - CORE_SIZE
            
            # Sicurezze per evitare coordinate negative
            if core_x < 0: core_x = 0
            if core_y < 0: core_y = 0

            # --- PREPARAZIONE CANVAS ---
            # Creiamo la base nera della dimensione finale (Core + Padding)
            final_tile_img = Image.new("RGB", (TILE_SIZE, TILE_SIZE), (0, 0, 0))
            # La maschera di base è NERA (0) = "Non toccare questa zona"
            final_tile_mask = Image.new("L", (TILE_SIZE, TILE_SIZE), (0)) 

            # --- RITAGLIO IMMAGINE (INCLUDE IL PADDING) ---
            # Calcoliamo l'area da ritagliare dall'originale (cercando di prendere il contesto)
            crop_x1 = max(0, core_x - PADDING)
            crop_y1 = max(0, core_y - PADDING)
            crop_x2 = min(w, core_x + CORE_SIZE + PADDING)
            crop_y2 = min(h, core_y + CORE_SIZE + PADDING)

            patch_img = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))

            # Calcoliamo dove incollare sulla canvas nera per centrare correttamente
            paste_x = crop_x1 - (core_x - PADDING)
            paste_y = crop_y1 - (core_y - PADDING)
            
            final_tile_img.paste(patch_img, (paste_x, paste_y))

            # --- RITAGLIO MASCHERA (SOLO CORE) ---
            # Ritagliamo SOLO la parte centrale della maschera.
            # Il padding deve rimanere nero per dire all'IA: "Usa il bordo solo per guardare, non modificarlo"
            mask_crop_x1 = max(0, core_x)
            mask_crop_y1 = max(0, core_y)
            mask_crop_x2 = min(w, core_x + CORE_SIZE)
            mask_crop_y2 = min(h, core_y + CORE_SIZE)

            patch_mask = mask.crop((mask_crop_x1, mask_crop_y1, mask_crop_x2, mask_crop_y2))

            # Incolliamo la maschera esattamente nella zona del CORE (dopo il padding)
            # Nota: Se siamo sul bordo immagine, PIL gestisce l'offset, ma idealmente è a (PADDING, PADDING)
            mask_paste_x = max(0, mask_crop_x1 - (core_x - PADDING)) - (crop_x1 - (core_x - PADDING)) + paste_x # Logica complessa per bordi
            
            # Semplificazione robusta per la maschera:
            # Sappiamo che il core inizia a PADDING nella canvas, a meno che non siamo sul bordo.
            # Ricalcoliamo relativo alla canvas:
            m_paste_x = (mask_crop_x1 - crop_x1) + paste_x
            m_paste_y = (mask_crop_y1 - crop_y1) + paste_y
            
            final_tile_mask.paste(patch_mask, (m_paste_x, m_paste_y))

            # --- FILTRO DANNI ---
            # Salviamo solo se c'è del bianco nella maschera (danni da riparare)
            mask_arr = np.array(final_tile_mask)
            has_damage = np.any(mask_arr > 20)

            # Nome file: usiamo "tile_" per i file sorgente, mantenendo le coordinate del CORE
            base_name = f"{config.TILE_PREFIX}y{core_y:05d}_x{core_x:05d}"

            if has_damage:
                # Salva Immagine
                final_tile_img.save(os.path.join(config.TILES_DIR, f"{base_name}.png"))
                # Salva Maschera
                final_tile_mask.save(os.path.join(config.TILES_DIR, f"{base_name}_mask.png"))
                
                # Crea file txt vuoto per il prompt
                with open(os.path.join(config.TILES_DIR, f"{base_name}.txt"), "w") as f:
                    f.write("") 
                
                count += 1
                if count % 10 == 0:
                    print(f"Generata patch {count}...")
            
    print(f"Create {count} patch nella cartella '{config.TILES_DIR}'.")

if __name__ == "__main__":
    slice_image_and_mask()