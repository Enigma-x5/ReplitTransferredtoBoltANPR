# src/detectors/yolo_easyocr_adapter.py
import os
import re
import cv2
import time
import torch
import shutil
import numpy as np
from pathlib import Path
from typing import Dict, List, Generator, Any
from ultralytics import YOLO
import easyocr

# Configuration via env (override in .env or docker-compose)
YOLO_MODEL = os.getenv("YOLO_MODEL", "keremberke/yolov8n-license-plate")
CONFIDENCE_THRESHOLD = float(os.getenv("DETECT_CONFIDENCE", "0.30"))
FRAME_SKIP = int(os.getenv("FRAME_SKIP", "10"))
RESIZE_WIDTH = int(os.getenv("RESIZE_WIDTH", "640"))
DEVICE = os.getenv("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
CROP_DIR = Path(os.getenv("DETECTOR_CROP_DIR", "/tmp/anpr_crops"))
MIN_BOX_WIDTH = int(os.getenv("MIN_BOX_WIDTH", "20"))
MIN_BOX_HEIGHT = int(os.getenv("MIN_BOX_HEIGHT", "10"))

os.makedirs(CROP_DIR, exist_ok=True)

# Initialize models lazily so worker import stays fast
_yolo_model = None
_ocr_reader = None

def _init_models():
    global _yolo_model, _ocr_reader
    if _yolo_model is None:
        _yolo_model = YOLO(YOLO_MODEL)
        # ultralytics model will accept device argument on call; keep model ready
    if _ocr_reader is None:
        _ocr_reader = easyocr.Reader(['en'], gpu=(DEVICE == 'cuda'))

def _clean_plate_text(text: str) -> str:
    # Normalize plate text: uppercase, remove non-alphanum
    return re.sub(r'[^A-Z0-9]', '', text.upper())

def _pad_bbox(x1, y1, x2, y2, pad_px, w, h):
    x1p = max(0, x1 - pad_px)
    y1p = max(0, y1 - pad_px)
    x2p = min(w - 1, x2 + pad_px)
    y2p = min(h - 1, y2 + pad_px)
    return x1p, y1p, x2p, y2p

def process_video(video_path: str, camera_id: str = None) -> Generator[Dict[str, Any], None, None]:
    """
    Process a video file and yield detection dicts.
    Each yielded dict should include keys:
      - plate (str)
      - normalized_plate (str)
      - confidence (float)
      - bbox (dict x1,y1,x2,y2)
      - frame_no (int)
      - captured_at (float) # seconds since start of file
      - crop_path (str) local path saved to disk (worker will upload)
    """
    _init_models()
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_no = 0
    saved = 0
    start_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_no += 1
            if frame_no % FRAME_SKIP != 0:
                continue

            # Resize preserving aspect ratio
            h, w = frame.shape[:2]
            new_h = int(h * (RESIZE_WIDTH / w))
            resized = cv2.resize(frame, (RESIZE_WIDTH, new_h))

            # Run detection (pass device and conf)
            results = _yolo_model(resized, conf=CONFIDENCE_THRESHOLD, device=DEVICE)

            for r in results:
                # r.boxes may be ultralytics objects. Normalize access:
                for box in getattr(r, "boxes", []):
                    xy = box.xyxy.cpu().numpy().flatten() if hasattr(box.xyxy, "cpu") else np.array(box.xyxy).flatten()
                    x1, y1, x2, y2 = map(int, xy.tolist())
                    bw = x2 - x1
                    bh = y2 - y1
                    if bw < MIN_BOX_WIDTH or bh < MIN_BOX_HEIGHT:
                        continue

                    # pad crop
                    x1p, y1p, x2p, y2p = _pad_bbox(x1, y1, x2, y2, pad_px=6, w=resized.shape[1], h=resized.shape[0])
                    crop = resized[y1p:y2p, x1p:x2p]
                    if crop.size == 0:
                        continue

                    # Preprocess for OCR
                    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                    # Optional: CLAHE
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                    gray_eq = clahe.apply(gray)

                    # OCR (easyocr returns list of tuples)
                    ocr_results = _ocr_reader.readtext(gray_eq)
                    if not ocr_results:
                        continue

                    # take best result (highest prob)
                    best = max(ocr_results, key=lambda r: r[2])
                    text = best[1]
                    prob = float(best[2])

                    cleaned = _clean_plate_text(text)
                    timestamp_sec = frame_no / fps

                    # Save crop for audit / labeling
                    crop_name = f"{Path(video_path).stem}_f{frame_no}_c{saved}.jpg"
                    crop_path = str(CROP_DIR / crop_name)
                    cv2.imwrite(crop_path, crop)
                    saved += 1

                    yield {
                        "plate": text,
                        "normalized_plate": cleaned,
                        "confidence": prob,
                        "bbox": {"x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2)},
                        "frame_no": int(frame_no),
                        "captured_at": float(timestamp_sec),
                        "crop_path": crop_path,
                        "camera_id": camera_id,
                    }
    finally:
        cap.release()
