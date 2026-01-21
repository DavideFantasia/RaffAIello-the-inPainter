#dipendenze:
#python -m pip install ultralytics insightface opencv-python pillow numpy tqdm
import os
import cv2
import numpy as np
from ultralytics import YOLO
from insightface.app import FaceAnalysis
from tqdm.auto import tqdm
from PIL import Image
import random

# ======================
# CONFIG
# ======================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(CURRENT_DIR, "raw/images")
OUTPUT_DIR = os.path.join(CURRENT_DIR, "img")
MODEL_DIR = os.path.join(CURRENT_DIR, "../models")

PATCH_SIZE = 1024
MAX_PATCHES_PER_IMAGE = 16

BACKGROUND_RATIO = 0.35   # ~35% patch solo sfondo
MIN_VARIANCE = 15         # filtro patch piatte

IOU_THRESHOLD = 0.2      #soglia di sovrapposizione per il filtro duplicati

# ======================
# MODELLI
# ======================
yolo = YOLO(f"{MODEL_DIR}/yolov8n-seg.pt") #modello per la segmentazione generale delle figure

yolo_pose = YOLO(f"{MODEL_DIR}/yolov8n-pose.pt") #modello per il rilevamento degli arti umani

face_app = FaceAnalysis(providers=["CPUExecutionProvider"])
face_app.prepare(ctx_id=0)

# ======================
# UTILS
# ======================

def square_crop(img, bbox, context=0.3):
    h, w = img.shape[:2]
    x1, y1, x2, y2 = bbox
    cx, cy = (x1+x2)//2, (y1+y2)//2
    
    # Calcoliamo la dimensione del lato del quadrato
    box_dim = max(x2-x1, y2-y1)
    size = int(box_dim * (1 + context))
    size = max(size, PATCH_SIZE)

    # Safety check: se per assurdo il crop è più grande dell'immagine intera
    if size > w: size = w
    if size > h: size = h

    # Calcolo coordinate iniziali centrate
    x1 = cx - size // 2
    y1 = cy - size // 2

    # --- LOGICA DI SHIFTING ---
    
    # 1. Se esce a sinistra/alto, allineamento a 0
    if x1 < 0: 
        x1 = 0
    if y1 < 0: 
        y1 = 0
        
    # 2. Se esce a destra/basso, si sposta indietro
    if x1 + size > w:
        x1 = w - size
    if y1 + size > h:
        y1 = h - size
        
    #x2 e y2 basati su x1/y1 corretti e size fisso
    x2 = x1 + size
    y2 = y1 + size
    
    # --- FINE LOGICA ---

    crop = img[y1:y2, x1:x2]
    
    if crop.shape[0] != crop.shape[1]:
        # Fallback estremo: padding nero se proprio non si riesce a fare quadrato
        top = 0
        bottom = PATCH_SIZE - crop.shape[0]
        left = 0
        right = PATCH_SIZE - crop.shape[1]
        crop = cv2.copyMakeBorder(crop, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0,0,0])
    else:
        interpolation = cv2.INTER_AREA if crop.shape[0] > PATCH_SIZE else cv2.INTER_CUBIC
        crop = cv2.resize(crop, (PATCH_SIZE, PATCH_SIZE), interpolation=interpolation)
        
    return crop

def random_background_crop(img, forbidden_mask):
    h, w = img.shape[:2]
    
    # Tentiamo 20 volte di trovare uno spazio vuoto
    for _ in range(20):
        x1 = random.randint(0, w - PATCH_SIZE)
        y1 = random.randint(0, h - PATCH_SIZE)
        
        x2 = x1 + PATCH_SIZE
        y2 = y1 + PATCH_SIZE

        # Controlliamo se in questa zona c'è il soggetto
        mask_crop = forbidden_mask[y1:y2, x1:x2]
        
        # Se l'area occupata dal soggetto è inferiore al 5%
        if np.mean(mask_crop) < 0.05:
            bbox = (x1, y1, x2, y2) # Definiamo la bbox
            
            return bbox # Ritorna le coordinate

    # Se dopo 20 tentativi non trova uno spazio vuoto
    return None

def good_patch(patch):
    return np.var(patch) >= MIN_VARIANCE

def save_sample(idx, img):
    Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).save(
        f"{OUTPUT_DIR}/img_{idx:05d}.png"
    )

def get_extremities_bboxes(img):
    """
    Usa YOLO Pose per trovare polsi (mani) e caviglie (piedi)
    Keypoints COCO:
    9: Left Wrist, 10: Right Wrist
    15: Left Ankle, 16: Right Ankle
    """
    results = yolo_pose(img, conf=0.5, verbose=False)[0]
    extremity_boxes = []
    
    if results.keypoints is not None:
        # data format: (Batch, 17 points, 3 values [x, y, conf])
        keypoints_data = results.keypoints.data.cpu().numpy()
        
        for person in keypoints_data:
            # Indici per Polsi (Mani) e Caviglie (Piedi)
            target_indices = [9, 10, 15, 16] 
            
            for idx in target_indices:
                kp = person[idx]
                x, y, conf = kp
                
                if conf > 0.5: # Se il punto è visibile
                    # Creiamo un box fittizio attorno al punto (articolazione)
                    # Dimensione fissa iniziale: 120px raggio (240px width)
                    # square_crop poi adatterà il contesto
                    radius = 120 
                    x1 = int(x - radius)
                    y1 = int(y - radius)
                    x2 = int(x + radius)
                    y2 = int(y + radius)
                    
                    # Check bordi
                    h, w = img.shape[:2]
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(w, x2), min(h, y2)
                    
                    if (x2 - x1) > 50 and (y2 - y1) > 50:
                        extremity_boxes.append((x1, y1, x2, y2))
                        
    return extremity_boxes

def compute_iou(boxA, boxB):
    # Determina le coordinate del rettangolo di intersezione
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    # Calcola l'area dell'intersezione
    interArea = max(0, xB - xA) * max(0, yB - yA)

    # Calcola l'area dei due box
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    # Calcola intersezione fratto unione
    # Se i box non si toccano, interArea è 0, quindi iou è 0
    float_div = float(boxAArea + boxBArea - interArea)
    if float_div == 0: return 0.0
    
    iou = interArea / float_div
    return iou
# ======================
# MAIN
# ======================
counter = 0

for fname in tqdm(os.listdir(INPUT_DIR), desc=f"Processing Image", position=0, leave=False):
    if not fname.lower().endswith((".png",".jpg",".jpeg",".tif")):
        continue

    img = cv2.imread(os.path.join(INPUT_DIR, fname))
    if img is None:
        continue

    h, w = img.shape[:2]
    if h < 1024 or w < 1024:
        continue

    # -------- YOLO SEG --------
    results = yolo(img, conf=0.25, verbose=False)[0]

    subject_mask = np.zeros((h,w), dtype=np.uint8)
    bboxes = []

    if results.masks is not None:
        for m, box in zip(results.masks.data, results.boxes.xyxy):

            # maschera YOLO -> numpy
            mask_small = (m.cpu().numpy() * 255).astype(np.uint8)

            #resize alla risoluzione originale
            mask = cv2.resize(
                mask_small,
                (w, h),
                interpolation=cv2.INTER_NEAREST
            )

            subject_mask = cv2.bitwise_or(subject_mask, mask)

            x1, y1, x2, y2 = map(int, box)
            if (x2 - x1) > 256 and (y2 - y1) > 256:
                bboxes.append((x1, y1, x2, y2))

    # -------- MANI E PIEDI (Pose Estimation) --------
    # Inseriamo questi PRIMA dei box generici, per dare priorità ai dettagli anatomici
    hands_feet_bboxes = get_extremities_bboxes(img)
    # Li mettiamo in cima alla lista
    for hb in hands_feet_bboxes:
        bboxes.insert(0, hb)

    # -------- VOLTI --------
    faces = face_app.get(img)
    for f in faces:
        x1,y1,x2,y2 = map(int, f.bbox)
        if (x2-x1) > 128: #si da priorità ai volti ben definiti
            bboxes.insert(0, (x1,y1,x2,y2))  # priorità alta

    # -------- PATCH BACKGROUND --------
    n_bg = int(MAX_PATCHES_PER_IMAGE * BACKGROUND_RATIO) + 1
    for _ in range(n_bg):
        bg_bbox = random_background_crop(img, subject_mask)
        bboxes.append(bg_bbox) if bg_bbox is not None else None

    # --- FILTRO DUPLICATI (IoU) ---
    unique_bboxes = []
    # Soglia di sovrapposizione: significa che se due box 
    # condividono più di un tot dell'area, uno viene scartato.

    for box in bboxes:
        is_duplicate = False
        for kept_box in unique_bboxes:
            if compute_iou(box, kept_box) > IOU_THRESHOLD:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_bboxes.append(box)
    #print(f"Detected {len(bboxes) - len(unique_bboxes)} duplicates for {fname}.")  
    bboxes = unique_bboxes
    # -------------------------------
    
    random.shuffle(bboxes)
    bboxes = bboxes[:MAX_PATCHES_PER_IMAGE]

    # -------- CONTROLLO E SALVATAGGIO PATCH --------
    for bbox in bboxes:
        patch = square_crop(img, bbox)
        if not good_patch(patch):
            continue

        save_sample(counter, patch)
        counter += 1

print(f"\nDataset creato: {counter} patch")
