FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 curl git git-lfs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py predictor.py ./

# Descarga el modelo desde GitHub LFS en tiempo de build
RUN curl -L "https://github.com/juliodiaz02091999/Anemia-Prediction/raw/main/best_xception_model.h5" \
    -o best_xception_model.h5 \
    && echo "Modelo descargado: $(du -sh best_xception_model.h5)"

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
