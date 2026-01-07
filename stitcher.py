import os
from PIL import Image
import config

def stitch_images():
    # 1. Verifica Cartelle
    if not os.path.exists(config.INPAINTED_DIR):
        print(f"ERRORE: La cartella {config.INPAINTED_DIR} non esiste.")
        return

    print("--- IMPOSTAZIONI STITCHING ---")
    print(f"Base Originale: {config.SRC_IMAGE_PATH}")
    print(f"Cartella Patch: {config.INPAINTED_DIR}")
    print(f"Output Finale: {config.FULL_OUTPUT_PATH}")
    print(f"Core Size: {config.PATCH_CORE_SIZE}px (Parte che verrà incollata)")
    print(f"Padding da rimuovere: {config.PADDING}px")
    print("------------------------------")

    # 2. Caricamento Base
    # Apriamo l'originale per incollarci sopra solo le patch modificate.
    # Le parti che non avevano danni rimarranno quelle originali ad altissima qualità.
    Image.MAX_IMAGE_PIXELS = None
    try:
        canvas = Image.open(config.SRC_IMAGE_PATH).convert("RGB")
    except FileNotFoundError:
        print("Errore: Immagine originale non trovata.")
        return

    # 3. Filtro File
    # Cerchiamo solo i file che iniziano con il prefisso definito nel config (es. "inpainted_tile_")
    # e che sono immagini.
    all_files = os.listdir(config.INPAINTED_DIR)
    files = [
        f for f in all_files 
        if f.startswith(config.TILE_PREFIX) 
        and f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]
    
    print(f"Trovate {len(files)} patch restaurate da processare.")
    
    # Parametri dimensionali dal config
    CORE_SIZE = config.PATCH_CORE_SIZE
    PADDING = config.PADDING

    for i, f in enumerate(files):
        # 4. Parsing del Nome File
        # Il file è tipo: inpainted_tile_y00512_x01024.png
        # Rimuoviamo prefisso ed estensione per leggere le coordinate
        try:
            name_clean = f.replace(config.TILE_PREFIX, "").replace(".png", "")
            parts = name_clean.split("_")
            
            # Formato atteso: "y00000", "x00000"
            y_part = [p for p in parts if p.startswith('y')][0]
            x_part = [p for p in parts if p.startswith('x')][0]

            y = int(y_part.replace("y", ""))
            x = int(x_part.replace("x", ""))
        except Exception as e:
            print(f"Saltato file {f}: formato nome non riconosciuto ({e})")
            continue
        
        # 5. Caricamento e Ritaglio (CROP)
        patch_path = os.path.join(config.INPAINTED_DIR, f)
        patch = Image.open(patch_path).convert("RGB")
        
        # La patch caricata include il PADDING (es. è 640x640).
        # Dobbiamo buttare via il padding esterno e tenere solo il centro (512x512).
        
        # Coordinate di ritaglio: (Left, Upper, Right, Lower)
        # Partiamo da PADDING e finiamo a PADDING + CORE
        crop_box = (PADDING, PADDING, PADDING + CORE_SIZE, PADDING + CORE_SIZE)
        
        # Eseguiamo il ritaglio
        clean_patch = patch.crop(crop_box)
        
        # 6. Incolla sulla Canvas
        # Usiamo le coordinate x,y estratte dal nome file.
        # Poiché nello slicer il nome file salvava l'angolo del CORE, qui incolliamo
        # esattamente a x,y senza dover fare calcoli strani.
        canvas.paste(clean_patch, (x, y))
        
        if i % 10 == 0:
            print(f"Incollato blocco {i+1}/{len(files)} a X={x}, Y={y}")

    print("Salvataggio immagine finale... (Attendere, file di grandi dimensioni)")
    # Crea la cartella di output se il path completo include sottocartelle non esistenti
    output_dir = os.path.dirname(config.FULL_OUTPUT_PATH)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    canvas.save(config.FULL_OUTPUT_PATH)
    print(f"Finito! Immagine salvata in: {config.FULL_OUTPUT_PATH}")

if __name__ == "__main__":
    stitch_images()