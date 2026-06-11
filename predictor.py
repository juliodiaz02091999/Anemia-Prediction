"""
predictor.py — Carga el modelo y ejecuta inferencia de hemoglobina.
"""

import os
import io
import numpy as np
import cv2
from PIL import Image, UnidentifiedImageError
import tensorflow as tf
from tensorflow.keras.models import load_model

ANEMIA_THRESHOLD = {"female": 12.0, "male": 13.0, "unknown": 12.0}
MODEL_PATH = os.environ.get("MODEL_PATH", "best_xception_model.h5")

_model = None


def get_model():
    global _model
    if _model is None:
        print(f"[predictor] Cargando modelo: {MODEL_PATH}")
        _model = load_model(MODEL_PATH, compile=False)
        print("[predictor] Modelo listo.")
    return _model


def preprocess(image_bytes: bytes) -> np.ndarray:
    """Convierte bytes de imagen a tensor (1, 224, 224, 3) float32."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize((224, 224), Image.BILINEAR)
        arr = np.array(img, dtype=np.float32) / 255.0
    except (UnidentifiedImageError, OSError):
        buf = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("No se pudo decodificar la imagen.")
        img = cv2.resize(img, (224, 224))
        arr = img.astype(np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


def predict(image_bytes: bytes, gender: str = "unknown") -> dict:
    """
    Devuelve:
        hb_pred_gdl  float  — hemoglobina predicha en g/dL
        threshold    float  — umbral OMS usado
        gender       str
        diagnosis    str    — "ANEMIA" | "NORMAL"
        anemia       bool
    """
    model = get_model()
    image = preprocess(image_bytes)
    hb = float(model.predict(image, verbose=0)[0][0])
    threshold = ANEMIA_THRESHOLD.get(gender.lower(), 12.0)
    anemia = hb < threshold
    return {
        "hb_pred_gdl": round(hb, 3),
        "threshold":   threshold,
        "gender":      gender,
        "diagnosis":   "ANEMIA" if anemia else "NORMAL",
        "anemia":      anemia,
    }
