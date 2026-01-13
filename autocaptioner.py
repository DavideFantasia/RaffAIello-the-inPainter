import os
import json
import time
import requests
import config
import shutil
import sys

# ==============================================================================
# FUNZIONI API COMFYUI
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

def get_queue():
    """Controlla la coda (Job in attesa o in esecuzione)"""
    try:
        response = requests.get(f"{config.COMFY_URL}/queue", timeout=5)
        return response.json()
    except Exception:
        # Se il server è occupato a caricare il modello, potrebbe non rispondere.
        # Ritorniamo un dizionario vuoto sicuro.
        return {}

def get_file_content(filename, subfolder, folder_type):
    """Scarica il contenuto di un file"""
    params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    response = requests.get(f"{config.COMFY_URL}/view", params=params, timeout=30)
    return response.content.decode('utf-8')

def load_workflow():
    with open(config.AUTOCAPTIONER_WORKFLOW_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ==============================================================================
# LOGICA DI ATTESA (POLLING ROBUSTO)
# ==============================================================================

def wait_for_job(prompt_id):
    """
    Attende il completamento del job controllando sia la Coda che la Storia.
    """
    print(f"    -> In attesa del Job ID: {prompt_id}...")
    start_time = time.time()
    
    while True:
        # 1. Controlla se è finito (History)
        history = get_history(prompt_id)
        if prompt_id in history:
            return history[prompt_id] # Trovato! Usciamo dal loop.

        # 2. Controlla se è ancora in coda o in esecuzione (Queue)
        queue_data = get_queue()
        
        is_pending = False
        is_running = False
        
        # Check Pending (In attesa)
        for item in queue_data.get('queue_pending', []):
            if item[1] == prompt_id:
                is_pending = True
                break
        
        # Check Running (In esecuzione)
        for item in queue_data.get('queue_running', []):
            if item[1] == prompt_id:
                is_running = True
                break

        if is_running:
            sys.stdout.write(f"\r    -> [Esecuzione in corso... (Caricamento Modello/Inferenza)] {int(time.time()-start_time)}s")
            sys.stdout.flush()
        elif is_pending:
            sys.stdout.write(f"\r    -> [In Coda...] {int(time.time()-start_time)}s")
            sys.stdout.flush()
        else:
            # Se NON è in history, NON è in pending, NON è in running...
            # Potrebbe essere un momento di transizione o il job è fallito silenziosamente.
            # Aspettiamo ancora un po' prima di dichiararlo perso, a volte l'API lagga.
            sys.stdout.write(f"\r    -> [Check stato...] {int(time.time()-start_time)}s")
            sys.stdout.flush()

        time.sleep(1) # Attesa di 1 secondo tra i check

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print(">>> Avvio Auto-Captioner Batch (Modalità Robusta)...")
    
    try:
        base_workflow = load_workflow()
    except Exception as e:
        print(f"ERRORE CRITICO: {e}")
        return

    all_files = os.listdir(config.TILES_DIR)
    image_files = [
        f for f in all_files 
        if f.lower().endswith(('.png', '.jpg', '.jpeg')) 
        and not f.lower().endswith('_mask.png')
    ]
    
    total = len(image_files)
    print(f"Trovate {total} immagini da descrivere in: {config.TILES_DIR}")

    NODE_ID_LOAD_IMAGE = "3"
    NODE_ID_SAVE_TEXT = "8" 

    for i, filename in enumerate(image_files, 1):
        print(f"\n[{i}/{total}] Processo: {filename}")
        
        img_path = os.path.join(config.TILES_DIR, filename)
        txt_filename = os.path.splitext(filename)[0] + ".txt"
        txt_output_path = os.path.join(config.TILES_DIR, txt_filename)

        # A. UPLOAD
        resp_img = upload_image(img_path)
        if not resp_img:
            print("    [!] Skip per errore upload.")
            continue
        comfy_img_name = resp_img.get("name", filename)

        # B. SETUP WORKFLOW
        workflow = base_workflow.copy()

        if NODE_ID_LOAD_IMAGE in workflow:
            workflow[NODE_ID_LOAD_IMAGE]["inputs"]["image"] = comfy_img_name
        else:
            print(f"ERRORE: Nodo {NODE_ID_LOAD_IMAGE} non trovato.")
            continue

        if NODE_ID_SAVE_TEXT in workflow:
            workflow[NODE_ID_SAVE_TEXT]["inputs"]["file"] = txt_filename
        else:
            print(f"ERRORE: Nodo {NODE_ID_SAVE_TEXT} non trovato.")
            continue

        # C. INVIO
        queue_resp = queue_prompt(workflow)
        if not queue_resp:
            continue
        prompt_id = queue_resp['prompt_id']

        # D. ATTESA (Funzione Robusta)
        print("") # Newline per pulizia
        result_data = wait_for_job(prompt_id)
        print("\n    -> Job Completato!")

        # E. SALVATAGGIO
        source_file = os.path.join("C:/ComfyUI/output", txt_filename)
        
        if os.path.exists(source_file):
            # Sposta (sovrascrive se esiste)
            shutil.move(source_file, config.TILES_DIR)
            print(f"    >>> Caption salvata correttamente in: {config.TILES_DIR}")
        else:
            print(f"    [!] ERRORE: Non trovo il file generato in {source_file}")
            print("        Verifica che la caption venga creata nella cartella ComfyUI/output.")

    print("\n--- Captioning Completato ---")

if __name__ == "__main__":
    main()