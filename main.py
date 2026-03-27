"""Multimodal Streaming AI Pipeline – FastAPI Application Entry Point."""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.multimodal import router as mm_router
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s – %(message)s")

app = FastAPI(
    title="Multimodal Streaming AI Pipeline",
    description="Real-time event-driven AI pipeline processing images (GPT-4 Vision), audio (OpenAI Whisper), and text through Apache Kafka. Supports multimodal fusion for unified cross-modal insights.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mm_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "service": "Multimodal Streaming AI Pipeline",
        "version": "1.0.0",
        "docs": "/docs",
        "modalities": {
            "image": "GPT-4 Vision (high detail) – scene analysis, OCR, chart reading",
            "audio": "OpenAI Whisper – transcription in 50+ languages",
            "text": "GPT-4o – summarisation, classification, entity extraction",
            "fusion": "GPT-4o – unified cross-modal insights",
        },
        "streaming": {
            "backend": "Apache Kafka",
            "input_topic": settings.KAFKA_INPUT_TOPIC,
            "output_topic": settings.KAFKA_OUTPUT_TOPIC,
        },
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
