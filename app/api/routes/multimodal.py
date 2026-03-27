"""Multimodal Streaming AI Pipeline – API routes."""
import shutil, tempfile
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.services.multimodal_service import MultimodalService, get_multimodal_service

router = APIRouter(prefix="/multimodal", tags=["Multimodal AI"])

class TextAnalysisRequest(BaseModel):
    text: str
    task: str = "summarise"

class FusionRequest(BaseModel):
    image_event_id: Optional[str] = None
    audio_event_id: Optional[str] = None
    text: Optional[str] = ""

@router.post("/image")
async def analyse_image(
    file: UploadFile = File(...),
    context: str = Form(default=""),
    svc: MultimodalService = Depends(get_multimodal_service),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(400, "Image too large (max 10MB)")
    return svc.analyse_image(data, file.filename, context)

@router.post("/audio")
async def transcribe_audio(
    file: UploadFile = File(...),
    svc: MultimodalService = Depends(get_multimodal_service),
):
    allowed = ("audio/mpeg", "audio/mp4", "audio/wav", "audio/ogg", "audio/webm")
    if file.content_type not in allowed:
        raise HTTPException(400, f"Unsupported audio format: {file.content_type}")
    data = await file.read()
    return svc.transcribe_audio(data, file.filename)

@router.post("/text")
async def analyse_text(req: TextAnalysisRequest, svc: MultimodalService = Depends(get_multimodal_service)):
    if not req.text.strip():
        raise HTTPException(400, "text cannot be empty")
    valid_tasks = ("summarise", "classify", "extract", "translate")
    if req.task not in valid_tasks:
        raise HTTPException(400, f"task must be one of {valid_tasks}")
    return svc.analyse_text(req.text, req.task)

@router.post("/fuse")
async def fuse_multimodal(req: FusionRequest, svc: MultimodalService = Depends(get_multimodal_service)):
    if not req.image_event_id and not req.audio_event_id and not req.text:
        raise HTTPException(400, "Provide at least one input: image_event_id, audio_event_id, or text")
    return svc.fuse_multimodal(req.image_event_id, req.audio_event_id, req.text)

@router.get("/stats")
async def stats(svc: MultimodalService = Depends(get_multimodal_service)):
    return svc.get_pipeline_stats()

@router.get("/health")
async def health():
    return {"status": "ok", "service": "Multimodal Streaming AI Pipeline – Vision + Audio + Kafka"}
