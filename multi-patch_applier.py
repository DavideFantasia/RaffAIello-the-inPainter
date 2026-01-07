import os
import json
import random
import time
import requests
import shutil

import config


# ==============================================================================
# FUNZIONI UTILI
# ==============================================================================

def upload_image(filepath):
    """Carica un file (immagine o maschera) su ComfyUI"""
    with open(filepath, 'rb') as f:
        files = {'image': f}
        # Sovrascrive se esiste già un file con lo stesso nome
        response = requests.post(f"{config.COMFY_URL}/upload/image", files=files)
    return response.json()

def queue_prompt(workflow_json):
    p = {"prompt": workflow_json}
    data = json.dumps(p).encode('utf-8')
    response = requests.post(f"{config.COMFY_URL}/prompt", data=data)
    return response.json()

def get_history(prompt_id):
    response = requests.get(f"{config.COMFY_URL}/history/{prompt_id}")
    return response.json()

def get_image_content(filename, subfolder, folder_type):
    params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    response = requests.get(f"{config.COMFY_URL}/view", params=params)
    return response.content

def load_workflow():
    with open(config.WORKFLOW_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ==============================================================================
# MAIN LOOP
# ==============================================================================

def main():
    if not os.path.exists(config.WORKFLOW_FILE):
        print(f"ERRORE: Non trovo il file {config.WORKFLOW_FILE}. Esportalo da ComfyUI (Save API Format).")
        return

    os.makedirs(config.INPAINTED_DIR, exist_ok=True)
    base_workflow = load_workflow()
    
    # Trova tutti i file immagine, ignora maschere
    all_files = os.listdir(config.TILES_DIR)
    image_files = [
        f for f in all_files 
        if f.lower().endswith(('.png', '.jpg', '.jpeg')) 
        and not f.lower().endswith('_mask.png')
    ]
    
    print(f"Trovate {len(image_files)} immagini principali da processare.")
    counter = 0
    total = len(image_files)
    for filename in image_files:
        print(f"\n-------------------------------------------------------------")
        print(f">>> Inizio lavorazione: {filename}")
        
        # Percorsi file
        img_path = os.path.join(config.TILES_DIR, filename)
        base_name = os.path.splitext(filename)[0]
        
        txt_path = os.path.join(config.TILES_DIR, base_name + ".txt")
        mask_path = os.path.join(config.TILES_DIR, base_name + "_mask.png")

        # -----------------------------------------------------------
        # UPLOAD IMMAGINE PRINCIPALE
        # -----------------------------------------------------------
        print("    [1/4] Caricamento immagine principale...")
        resp_img = upload_image(img_path)
        comfy_img_name = resp_img.get("name", filename)

        # -----------------------------------------------------------
        # UPLOAD MASCHERA (Se esiste, se no default nel JSON [sconsigliato])
        # -----------------------------------------------------------
        comfy_mask_name = None
        if os.path.exists(mask_path):
            print(f"    [2/4] Caricamento maschera ({base_name}_mask.png)...")
            resp_mask = upload_image(mask_path)
            comfy_mask_name = resp_mask.get("name", os.path.basename(mask_path))
        else:
            print("    [!] ATTENZIONE: Maschera non trovata! Lo script userà quella di default nel JSON (se c'è).")

        # -----------------------------------------------------------
        # LETTURA PROMPT
        # -----------------------------------------------------------
        prompt_text = ""
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                prompt_text = f.read().strip()
            print("    [3/4] Prompt testuale letto.")
        else:
            print("    [Info] Nessun file .txt trovato, uso prompt predefinito.")

        # -----------------------------------------------------------
        # AGGIORNAMENTO WORKFLOW
        # -----------------------------------------------------------
        workflow = base_workflow.copy()

        # Aggiorna Immagine (Nodo 4)
        workflow[config.NODE_ID_LOAD_IMAGE]["inputs"]["image"] = comfy_img_name
        
        # Aggiorna Maschera (Nodo 9) - SE TROVATA
        if comfy_mask_name:
            # Di solito l'input si chiama "image" anche nel nodo LoadImageMask
            # il canale scelto è il red
            workflow[config.NODE_ID_LOAD_MASK]["inputs"]["image"] = comfy_mask_name
        
        # Aggiorna Prompt (Nodo 3)
        if prompt_text:
            if "text" in workflow[config.NODE_ID_POSITIVE_PROMPT]["inputs"]:
                 workflow[config.NODE_ID_POSITIVE_PROMPT]["inputs"]["text"] += ", "+prompt_text
            else:
                 workflow[config.NODE_ID_POSITIVE_PROMPT]["inputs"]["text_g"] += ", "+prompt_text

        # Random Seed (Nodo 8)
        if "seed" in workflow[config.NODE_ID_KSAMPLER]["inputs"]:
            workflow[config.NODE_ID_KSAMPLER]["inputs"]["seed"] = random.randint(1, 10**14)
        elif "noise_seed" in workflow[config.NODE_ID_KSAMPLER]["inputs"]:
            workflow[config.NODE_ID_KSAMPLER]["inputs"]["noise_seed"] = random.randint(1, 10**14)

        # -----------------------------------------------------------
        # ESECUZIONE
        # -----------------------------------------------------------
        try:
            print("    [4/4] Invio job a ComfyUI...")
            queue_resp = queue_prompt(workflow)
            prompt_id = queue_resp['prompt_id']
        except Exception as e:
            print(f"    [ERRORE] Impossibile connettersi a ComfyUI: {e}")
            continue

        # Attesa (Polling)
        while True:
            history = get_history(prompt_id)
            if prompt_id in history:
                break
            time.sleep(1)

        # -----------------------------------------------------------
        # SALVATAGGIO OUTPUT
        # -----------------------------------------------------------
        history_data = history[prompt_id]
        outputs = history_data.get('outputs', {})

        if config.NODE_ID_SAVE_IMAGE in outputs:
            for item in outputs[config.NODE_ID_SAVE_IMAGE].get('images', []):
                img_data = get_image_content(item['filename'], item['subfolder'], item['type'])
                
                # Nome file output: inpainted_nomefileoriginale.png
                out_name = f"{filename}"
                out_path = os.path.join(config.INPAINTED_DIR, out_name)
                
                with open(out_path, "wb") as f_out:
                    f_out.write(img_data)
                print(f"    >>> SUCCESSO: Immagine salvata in {out_path}")
        else:
            print("    [Errore] Output non trovato. Verifica in `config.py` che 'NODE_ID_SAVE_IMAGE' sia corretto.")
        counter += 1
        print(f"    >>> Eseguiti {counter}/{total} immagini.")
    print("\n--- Batch completato ---")

if __name__ == "__main__":
    main()