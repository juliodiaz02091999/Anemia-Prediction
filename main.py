"""
main.py — FastAPI backend para predicción de anemia desde imagen de ojo.

Endpoints:
    GET  /health       → { status: "ok", model_loaded: bool }
    POST /predict      → { hb_pred_gdl, diagnosis, threshold, gender, anemia }
"""

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal
import uvicorn

from predictor import predict, get_model

app = FastAPI(
    title="HemoScan API",
    description="Predice hemoglobina (Hb) a partir de una foto de la conjuntiva palpebral.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictionResponse(BaseModel):
    hb_pred_gdl: float
    threshold:   float
    gender:      str
    diagnosis:   Literal["ANEMIA", "NORMAL"]
    anemia:      bool


@app.get("/health")
def health():
    try:
        get_model()
        loaded = True
    except Exception:
        loaded = False
    return {"status": "ok", "model_loaded": loaded}


@app.post("/predict", response_model=PredictionResponse)
async def predict_endpoint(
    image:  UploadFile = File(..., description="Foto del ojo (jpg/png)"),
    gender: str        = Form("unknown", description="male | female | unknown"),
):
    if gender not in ("male", "female", "unknown"):
        raise HTTPException(status_code=422, detail="gender debe ser male, female o unknown.")

    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="El archivo debe ser una imagen.")

    image_bytes = await image.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="La imagen esta vacia.")

    try:
        result = predict(image_bytes, gender=gender)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la imagen: {e}")

    return result


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
