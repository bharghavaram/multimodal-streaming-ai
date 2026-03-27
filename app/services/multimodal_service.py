"""
Multimodal Streaming AI Pipeline.
Kafka-based event streaming + GPT-4 Vision + Whisper audio + real-time WebSocket output.
"""
import logging
import base64
import json
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import httpx
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

VISION_ANALYSIS_PROMPT = """Analyse this image comprehensively. Provide:
1. **Scene Description**: What is shown in detail
2. **Key Objects**: List all significant objects with confidence
3. **Text/Data Extracted**: Any text, numbers, charts, or data visible
4. **Insights**: Business/technical/medical insights depending on context
5. **Action Items**: Recommended actions based on the image content
6. **Confidence**: Overall confidence in analysis (0-100%)"""

MULTIMODAL_FUSION_PROMPT = """You are a multimodal AI analyst. Synthesise insights from multiple data sources.

IMAGE ANALYSIS:
{image_analysis}

AUDIO TRANSCRIPT:
{audio_transcript}

TEXT CONTEXT:
{text_context}

Provide a unified, comprehensive analysis that:
1. Identifies connections between visual, audio, and text information
2. Resolves any contradictions between sources
3. Extracts the most important actionable insights
4. Rates confidence in the overall analysis"""


class KafkaProducer:
    def __init__(self):
        self.available = False
        try:
            from kafka import KafkaProducer as _KafkaProducer
            self.producer = _KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS.split(","),
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            self.available = True
            logger.info("Kafka producer connected")
        except Exception as exc:
            logger.warning("Kafka unavailable (%s) – events stored in memory", exc)
            self._queue: List[dict] = []

    def send(self, topic: str, message: dict):
        if self.available:
            self.producer.send(topic, value=message)
            self.producer.flush()
        else:
            self._queue.append({"topic": topic, "message": message})

    def get_queued(self) -> list:
        return self._queue if not self.available else []


class MultimodalService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.kafka = KafkaProducer()
        self._events: List[dict] = []
        self._results: dict = {}

    def analyse_image(self, image_data: bytes, filename: str = "image.jpg", context: str = "") -> dict:
        event_id = str(uuid.uuid4())
        b64_image = base64.b64encode(image_data).decode("utf-8")
        ext = filename.rsplit(".", 1)[-1].lower()
        media_type = f"image/{ext}" if ext in ("png", "jpg", "jpeg", "gif", "webp") else "image/jpeg"

        # Emit to Kafka
        self.kafka.send(settings.KAFKA_INPUT_TOPIC, {
            "event_id": event_id,
            "event_type": "image_analysis",
            "filename": filename,
            "timestamp": datetime.utcnow().isoformat(),
        })

        try:
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{VISION_ANALYSIS_PROMPT}\n\nContext: {context}" if context else VISION_ANALYSIS_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{b64_image}", "detail": "high"}},
                ]
            }]
            resp = self.openai_client.chat.completions.create(
                model=settings.GPT4V_MODEL,
                messages=messages,
                max_tokens=settings.MAX_TOKENS,
            )
            analysis = resp.choices[0].message.content
            tokens = resp.usage.total_tokens
        except Exception as exc:
            logger.error("Vision analysis failed: %s", exc)
            analysis = f"Vision analysis failed: {exc}"
            tokens = 0

        result = {
            "event_id": event_id,
            "event_type": "image_analysis",
            "filename": filename,
            "analysis": analysis,
            "tokens_used": tokens,
            "model": settings.GPT4V_MODEL,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._results[event_id] = result
        self.kafka.send(settings.KAFKA_OUTPUT_TOPIC, result)
        return result

    def transcribe_audio(self, audio_data: bytes, filename: str = "audio.mp3") -> dict:
        event_id = str(uuid.uuid4())
        self.kafka.send(settings.KAFKA_INPUT_TOPIC, {
            "event_id": event_id,
            "event_type": "audio_transcription",
            "filename": filename,
            "timestamp": datetime.utcnow().isoformat(),
        })

        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=f".{filename.rsplit('.', 1)[-1]}", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            with open(tmp_path, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model=settings.WHISPER_MODEL,
                    file=audio_file,
                    response_format="verbose_json",
                )
            Path(tmp_path).unlink(missing_ok=True)

            result = {
                "event_id": event_id,
                "event_type": "audio_transcription",
                "filename": filename,
                "transcript": transcript.text,
                "language": getattr(transcript, "language", "en"),
                "duration_seconds": getattr(transcript, "duration", 0),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as exc:
            logger.error("Audio transcription failed: %s", exc)
            result = {
                "event_id": event_id,
                "event_type": "audio_transcription",
                "error": str(exc),
                "transcript": "",
                "timestamp": datetime.utcnow().isoformat(),
            }

        self._results[event_id] = result
        self.kafka.send(settings.KAFKA_OUTPUT_TOPIC, result)
        return result

    def analyse_text(self, text: str, task: str = "summarise") -> dict:
        event_id = str(uuid.uuid4())
        tasks = {
            "summarise": "Provide a concise summary with key points:",
            "classify": "Classify the topic, sentiment, and intent of this text:",
            "extract": "Extract all named entities, facts, and metrics from this text:",
            "translate": "Translate to English and summarise:",
        }
        prompt = f"{tasks.get(task, tasks['summarise'])}\n\n{text}"
        self.kafka.send(settings.KAFKA_INPUT_TOPIC, {"event_id": event_id, "event_type": "text_analysis", "task": task})

        resp = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        result = {
            "event_id": event_id,
            "event_type": "text_analysis",
            "task": task,
            "result": resp.choices[0].message.content,
            "tokens_used": resp.usage.total_tokens,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._results[event_id] = result
        self.kafka.send(settings.KAFKA_OUTPUT_TOPIC, result)
        return result

    def fuse_multimodal(self, image_event_id: str = None, audio_event_id: str = None, text: str = "") -> dict:
        image_analysis = self._results.get(image_event_id, {}).get("analysis", "No image analysis") if image_event_id else "No image provided"
        audio_transcript = self._results.get(audio_event_id, {}).get("transcript", "No audio transcript") if audio_event_id else "No audio provided"

        prompt = MULTIMODAL_FUSION_PROMPT.format(
            image_analysis=image_analysis,
            audio_transcript=audio_transcript,
            text_context=text or "No additional text context",
        )
        resp = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings.MAX_TOKENS,
        )
        event_id = str(uuid.uuid4())
        result = {
            "event_id": event_id,
            "event_type": "multimodal_fusion",
            "fused_analysis": resp.choices[0].message.content,
            "sources": {
                "image_event_id": image_event_id,
                "audio_event_id": audio_event_id,
                "has_text": bool(text),
            },
            "tokens_used": resp.usage.total_tokens,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._results[event_id] = result
        self.kafka.send(settings.KAFKA_OUTPUT_TOPIC, result)
        return result

    def get_pipeline_stats(self) -> dict:
        events_by_type = {}
        for r in self._results.values():
            t = r.get("event_type", "unknown")
            events_by_type[t] = events_by_type.get(t, 0) + 1
        return {
            "total_events_processed": len(self._results),
            "kafka_available": self.kafka.available,
            "events_by_type": events_by_type,
            "queued_events": len(self.kafka.get_queued()),
        }


_service: Optional[MultimodalService] = None
def get_multimodal_service() -> MultimodalService:
    global _service
    if _service is None:
        _service = MultimodalService()
    return _service
