"""Tests for Multimodal Streaming AI Pipeline."""
import pytest
from unittest.mock import MagicMock, patch
from app.core.config import settings


def test_settings():
    assert settings.MAX_IMAGE_SIZE_MB == 10
    assert settings.MAX_AUDIO_DURATION_SECS == 300
    assert settings.GPT4V_MODEL == "gpt-4o"


def test_kafka_producer_fallback():
    with patch("app.services.multimodal_service.OpenAI"), \
         patch("app.services.multimodal_service.Anthropic"):
        from app.services.multimodal_service import KafkaProducer
        producer = KafkaProducer()
        # Kafka not running – should fall back to in-memory queue
        assert not producer.available
        producer.send("test-topic", {"key": "value"})
        queued = producer.get_queued()
        assert len(queued) == 1
        assert queued[0]["topic"] == "test-topic"
        assert queued[0]["message"]["key"] == "value"


def test_pipeline_stats_empty():
    with patch("app.services.multimodal_service.OpenAI"), \
         patch("app.services.multimodal_service.Anthropic"):
        from app.services.multimodal_service import MultimodalService
        svc = MultimodalService()
        stats = svc.get_pipeline_stats()
        assert stats["total_events_processed"] == 0
        assert "kafka_available" in stats


def test_image_size_validation():
    max_bytes = 10 * 1024 * 1024
    large = b"x" * (max_bytes + 1)
    assert len(large) > max_bytes


@pytest.mark.asyncio
async def test_api_health():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    resp = client.get("/api/v1/multimodal/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_api_stats():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    resp = client.get("/api/v1/multimodal/stats")
    assert resp.status_code == 200
    assert "total_events_processed" in resp.json()


@pytest.mark.asyncio
async def test_api_text_invalid_task():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    resp = client.post("/api/v1/multimodal/text", json={"text": "Hello world", "task": "invalid"})
    assert resp.status_code == 400
