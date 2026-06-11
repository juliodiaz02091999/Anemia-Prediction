"""
predict_hb.py — Inferencia de hemoglobina desde una imagen de ojo
==================================================================
Uso: python predict_hb.py
Edita la sección CONFIG antes de correr.
"""

import os
import sys
import zipfile
import tempfile

import numpy as np
import matplotlib.pyplot as plt
import cv2
import tensorflow as tf
from PIL import Image, UnidentifiedImageError
from tensorflow.keras.models import load_model, Model
from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D
from tensorflow.keras.applications import Xception
from tensorflow.keras.optimizers import Adam

# ──────────────────────────────────────────────
# Umbrales clínicos de anemia (OMS)
# ──────────────────────────────────────────────
ANEMIA_THRESHOLD_FEMALE  = 12.0   # g/dL
ANEMIA_THRESHOLD_MALE    = 13.0   # g/dL
ANEMIA_THRESHOLD_UNKNOWN = 12.0   # g/dL (conservador)

# ──────────────────────────────────────────────
# CONFIG — edita estos valores antes de correr
# ──────────────────────────────────────────────
IMAGE_PATH  = r"20200118_164733.jpg"   # ruta a la imagen
MODEL_PATH  = r"best_xception_model.h5"                       # ruta al modelo (.h5 o .keras)
GENDER      = "unknown"    # "male", "female" o "unknown"
GEN_GRADCAM = True         # True para generar el mapa Grad-CAM
GEN_LIME    = False        # True para generar explicacion LIME (~1 min)
OUTPUT_DIR  = "resultados" # carpeta donde se guardan los resultados
# ──────────────────────────────────────────────

GRADCAM_LAYER = 'block14_sepconv2_act'


# ──────────────────────────────────────────────
# Carga robusta del modelo (fallback: reconstruir + pesos)
# ──────────────────────────────────────────────
def _load_model_rebuild(model_path: str):
    """
    Carga el modelo reconstruyendo la arquitectura exacta desde el config.json
    guardado dentro del .keras, luego carga los pesos por posición.
    Resuelve el mismatch de nombres de capas entre Kaggle y local.
    """
    import json

    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(model_path, 'r') as z:
            z.extract('config.json', tmp)
            z.extract('model.weights.h5', tmp)

        config_path  = os.path.join(tmp, 'config.json')
        weights_path = os.path.join(tmp, 'model.weights.h5')

        with open(config_path, 'r') as f:
            config = json.load(f)

        # Reconstruir la arquitectura idéntica a la guardada en Kaggle
        model = tf.keras.models.model_from_json(json.dumps(config))
        model.compile(optimizer=Adam(1e-4), loss='mse', metrics=['mae'])

        # Cargar pesos por posición (by_name=False) para evitar mismatch de nombres
        model.load_weights(weights_path)

    return model


# ──────────────────────────────────────────────
# Preprocesamiento
# ──────────────────────────────────────────────
def load_image(image_path: str) -> np.ndarray:
    """Carga y normaliza la imagen a (1, 224, 224, 3) float32."""
    try:
        img = Image.open(image_path).convert("RGB")
        img = img.resize((224, 224), Image.BILINEAR)
        arr = np.array(img, dtype=np.float32) / 255.0
    except (UnidentifiedImageError, OSError):
        img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if img is None:
            sys.exit(f"[ERROR] No se pudo abrir la imagen: {image_path}")
        img = cv2.resize(img, (224, 224))
        arr = img.astype(np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


# ──────────────────────────────────────────────
# Predicción
# ──────────────────────────────────────────────
def predict(model, image: np.ndarray, gender: str = "unknown") -> dict:
    """Predice Hb y determina si hay anemia según el género."""
    hb = float(model.predict(image, verbose=0)[0][0])
    threshold = {
        "female": ANEMIA_THRESHOLD_FEMALE,
        "male":   ANEMIA_THRESHOLD_MALE,
    }.get(gender.lower(), ANEMIA_THRESHOLD_UNKNOWN)

    anemia = hb < threshold
    return {
        "hb_pred_gdl":  round(hb, 3),
        "threshold":    threshold,
        "gender":       gender,
        "anemia":       anemia,
        "diagnosis":    "ANEMIA" if anemia else "NORMAL",
    }


# ──────────────────────────────────────────────
# Grad-CAM
# ──────────────────────────────────────────────
def gradcam(model, image: np.ndarray, layer_name: str = GRADCAM_LAYER) -> np.ndarray:
    grad_model = Model(
        inputs=model.inputs,
        outputs=[model.get_layer(layer_name).output, model.output]
    )
    with tf.GradientTape() as tape:
        conv_out, preds = grad_model(image)
        loss = preds[:, 0]
    grads = tape.gradient(loss, conv_out)
    pooled = tf.reduce_mean(grads, axis=(0, 1, 2))
    heatmap = conv_out[0] @ pooled[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    heatmap = tf.maximum(heatmap, 0) / (tf.math.reduce_max(heatmap) + 1e-8)
    return heatmap.numpy()


def save_gradcam(image: np.ndarray, heatmap: np.ndarray,
                 result: dict, output_path: str) -> None:
    img_u8 = np.uint8(255 * image[0])
    h = cv2.resize(heatmap, (img_u8.shape[1], img_u8.shape[0]))
    h_color = cv2.applyColorMap(np.uint8(255 * h), cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(img_u8, 0.6, h_color, 0.4, 0)

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle(
        f"Hb predicha: {result['hb_pred_gdl']:.2f} g/dL  |  "
        f"Umbral: {result['threshold']} g/dL  |  {result['diagnosis']}",
        fontsize=13, fontweight='bold',
        color='red' if result['anemia'] else 'green'
    )
    axes[0].imshow(img_u8);   axes[0].set_title("Imagen original"); axes[0].axis('off')
    axes[1].imshow(overlay);  axes[1].set_title("Grad-CAM");         axes[1].axis('off')
    plt.tight_layout()
    plt.savefig(output_path, dpi=130, bbox_inches='tight')
    plt.close()
    print(f"  Grad-CAM guardado en: {output_path}")


# ──────────────────────────────────────────────
# LIME
# ──────────────────────────────────────────────
def save_lime(model, image: np.ndarray, result: dict, output_path: str) -> None:
    try:
        from lime import lime_image
        from skimage.segmentation import mark_boundaries
    except ImportError:
        print("  [AVISO] LIME no instalado. Ejecuta: pip install lime")
        return

    explainer = lime_image.LimeImageExplainer()
    explanation = explainer.explain_instance(
        image=image[0],
        classifier_fn=lambda x: model.predict(x, verbose=0),
        top_labels=1,
        hide_color=0,
        num_samples=1000
    )
    temp, mask = explanation.get_image_and_mask(
        label=0, positive_only=True, hide_rest=False, num_features=5, min_weight=0.0
    )
    plt.figure(figsize=(6, 5))
    plt.imshow(mark_boundaries(temp, mask))
    plt.title(
        f"LIME  |  Hb={result['hb_pred_gdl']:.2f} g/dL  |  {result['diagnosis']}",
        fontsize=12, fontweight='bold',
        color='red' if result['anemia'] else 'green'
    )
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_path, dpi=130, bbox_inches='tight')
    plt.close()
    print(f"  LIME guardado en:    {output_path}")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
if __name__ == '__main__':

    # Validaciones
    if not os.path.isfile(IMAGE_PATH):
        sys.exit(f"[ERROR] Imagen no encontrada: {IMAGE_PATH}")
    if not os.path.isfile(MODEL_PATH):
        sys.exit(f"[ERROR] Modelo no encontrado: {MODEL_PATH}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Cargar modelo
    print(f"\nCargando modelo: {MODEL_PATH}")
    model = None
    strategies = [
        lambda p: load_model(p, compile=False),
        lambda p: load_model(p, compile=False, safe_mode=False),
        lambda p: tf.keras.models.load_model(p, compile=False),
        lambda p: _load_model_rebuild(p),
    ]
    for i, strategy in enumerate(strategies):
        try:
            model = strategy(MODEL_PATH)
            break
        except Exception as e:
            print(f"  [intento {i+1}] {type(e).__name__}: {e}")
    if model is None:
        sys.exit("[ERROR] No se pudo cargar el modelo con ninguna estrategia.")

    # Cargar imagen
    print(f"Procesando imagen: {IMAGE_PATH}")
    image = load_image(IMAGE_PATH)

    # Prediccion
    result = predict(model, image, gender=GENDER)

    # Resultado en consola
    print("\n" + "=" * 45)
    print("           RESULTADO DE PREDICCION")
    print("=" * 45)
    print(f"  Hb predicha  : {result['hb_pred_gdl']:.3f} g/dL")
    print(f"  Umbral usado : {result['threshold']} g/dL  (genero: {result['gender']})")
    print(f"  Diagnostico  : {result['diagnosis']}")
    print("=" * 45)
    if result['anemia']:
        print("  [!] POSIBLE ANEMIA - consultar con un medico.")
    else:
        print("  [OK] Valores dentro del rango normal.")
    print("=" * 45 + "\n")

    img_stem = os.path.splitext(os.path.basename(IMAGE_PATH))[0]

    # Grad-CAM
    if GEN_GRADCAM:
        print("Generando Grad-CAM...")
        heatmap = gradcam(model, image)
        out_gc = os.path.join(OUTPUT_DIR, f"{img_stem}_gradcam.png")
        save_gradcam(image, heatmap, result, out_gc)

    # LIME
    if GEN_LIME:
        print("Generando LIME (puede tardar ~1 min)...")
        out_lime = os.path.join(OUTPUT_DIR, f"{img_stem}_lime.png")
        save_lime(model, image, result, out_lime)

    print("Listo.\n")
