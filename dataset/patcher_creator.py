#dipendenze:
#python -m pip install ultralytics insightface opencv-python pillow numpy tqdm
import os
import cv2
import numpy as np
from ultralytics import YOLO
from insightface.app import FaceAnalysis
from tqdm import tqdm
from PIL import Image
import random

# ======================
# CONFIG
# ======================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(CURRENT_DIR, "raw/images")
OUTPUT_DIR = os.path.join(CURRENT_DIR, "img")
MODEL_DIR = os.path.join(CURRENT_DIR, "../models")

PATCH_SIZE = 512
MAX_PATCHES_PER_IMAGE = 16

BACKGROUND_RATIO = 0.35   # ~35% patch solo sfondo
MIN_VARIANCE = 15         # filtro patch piatte

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
    box = max(x2-x1, y2-y1)
    size = int(box * (1 + context))
    size = max(size, PATCH_SIZE)

    x1 = max(0, cx - size//2)
    y1 = max(0, cy - size//2)
    x2 = min(w, x1 + size)
    y2 = min(h, y1 + size)

    crop = img[y1:y2, x1:x2]
    crop = cv2.resize(crop, (PATCH_SIZE, PATCH_SIZE))
    return crop

def random_background_crop(img, forbidden_mask):
    h, w = img.shape[:2]
    for _ in range(20):
        x = random.randint(0, w - PATCH_SIZE)
        y = random.randint(0, h - PATCH_SIZE)
        mask_crop = forbidden_mask[y:y+PATCH_SIZE, x:x+PATCH_SIZE]
        if np.mean(mask_crop) < 0.05:
            crop = img[y:y+PATCH_SIZE, x:x+PATCH_SIZE]
            return crop
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
# ======================
# MAIN
# ======================
counter = 0

for fname in tqdm(os.listdir(INPUT_DIR)):
    if not fname.lower().endswith((".png",".jpg",".jpeg",".tif")):
        continue

    img = cv2.imread(os.path.join(INPUT_DIR, fname))
    if img is None:
        continue

    h, w = img.shape[:2]
    if h < 1024 or w < 1024:
        continue

    # -------- YOLO SEG --------
    results = yolo(img, conf=0.25)[0]

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
    
    random.shuffle(bboxes)
    bboxes = bboxes[:MAX_PATCHES_PER_IMAGE]

    # -------- PATCH SOGGETTO --------
    for bbox in bboxes:
        patch = square_crop(img, bbox)
        if not good_patch(patch):
            continue

        save_sample(counter, patch)
        counter += 1

    # -------- PATCH BACKGROUND --------
    n_bg = int(len(bboxes) * BACKGROUND_RATIO) + 1
    for _ in range(n_bg):
        bg = random_background_crop(img, subject_mask)
        if bg is None or not good_patch(bg):
            continue

        save_sample(counter, bg)
        counter += 1

print(f"\nDataset creato: {counter} patch")
