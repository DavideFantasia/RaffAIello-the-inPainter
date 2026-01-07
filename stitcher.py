import os
from PIL import Image


# ================= CONFIGURAZIONE =================
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_IMAGE_PATH = f"{WORK_DIR}/stendardo/img/trinita_25perc.png"
INPAINTED_DIR = f"{WORK_DIR}/stendardo/patch_dst"
OUTPUT_FULL_PATH = f"{WORK_DIR}/stendardo/restauro.png"

TILE_PREFIX = "inpainted_tile_"

def stitch_images():
    print("Caricamento base originale...")
    # Apriamo l'originale per incollaci sopra solo le patch modificate
    # Così le parti sane restano alla qualità originale perfetta
    Image.MAX_IMAGE_PIXELS = None
    canvas = Image.open(SRC_IMAGE_PATH).convert("RGB")
    
    # Trova tutti i file immagine, ignora maschere
    all_files = os.listdir(INPAINTED_DIR)
    files = [
        f for f in all_files 
        if f.lower().endswith(('.png', '.jpg', '.jpeg')) 
        and not f.lower().endswith('_mask.png')
    ]
    print(f"Trovate {len(files)} patch restaurate da incollare.")
    
    for f in files:
        # Il nome file è tipo: tile_y00512_x01024.png
        # Dobbiamo estrarre y e x
        parts = f.replace(TILE_PREFIX, "").replace(".png", "").split("_")
        # parts[0] è y00512 -> togliamo la 'y'
        y = int(parts[0].replace("y", ""))
        # parts[1] è x01024 -> togliamo la 'x'
        x = int(parts[1].replace("x", ""))
        
        # Carica patch
        patch_path = os.path.join(INPAINTED_DIR, f)
        patch = Image.open(patch_path).convert("RGB")
        
        # Incolla sulla canvas alle coordinate giuste
        canvas.paste(patch, (x, y))
        
        print(f"Incollato blocco a X={x}, Y={y}")

    print("Salvataggio immagine finale... (potrebbe richiedere tempo)")
    canvas.save(OUTPUT_FULL_PATH)
    print("Finito!")

if __name__ == "__main__":
    stitch_images()