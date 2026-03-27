> **📅 Project Period:** Aug 2025 – Sep 2025 &nbsp;|&nbsp; **Status:** Completed &nbsp;|&nbsp; **Author:** [Bharghava Ram Vemuri](https://github.com/bharghavaram)

# Multimodal Streaming AI Pipeline

> Real-time event-driven AI processing pipeline for images (GPT-4 Vision), audio (Whisper), and text via Apache Kafka

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Kafka](https://img.shields.io/badge/Apache_Kafka-3.x-black)](https://kafka.apache.org)
[![GPT-4V](https://img.shields.io/badge/GPT--4o-Vision-purple)](https://openai.com)
[![Whisper](https://img.shields.io/badge/Whisper-v1-orange)](https://openai.com)

## Overview

A production-grade **multimodal AI pipeline** that processes images, audio, and text through Apache Kafka event streams. Each modality is processed by specialised AI models and results can be fused into unified cross-modal insights — enabling real-time AI analysis at scale.

## Architecture

```
HTTP Upload → FastAPI → Kafka Input Topic
                              ↓
              ┌───────────────────────────────┐
              │  Image → GPT-4o Vision        │
              │  Audio → OpenAI Whisper       │
              │  Text → GPT-4o Analysis       │
              └───────────────────────────────┘
                              ↓
                     Kafka Output Topic
                              ↓
              Multimodal Fusion (GPT-4o)
                              ↓
              Unified Cross-Modal Insights
```

## Key Features

- **GPT-4 Vision** – high-detail image analysis: scene description, OCR, chart reading, object detection
- **OpenAI Whisper** – transcription in 50+ languages with timestamps and duration
- **Apache Kafka** – event streaming with graceful in-memory fallback
- **Multimodal Fusion** – combines image, audio, and text analyses into unified insights
- **Real-time processing** – async FastAPI with WebSocket support
- **WebSocket streaming** – stream results to frontend in real time

## Quick Start

```bash
git clone https://github.com/bharghavaram/multimodal-streaming-ai
cd multimodal-streaming-ai
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/multimodal/image` | Analyse image (multipart) |
| POST | `/api/v1/multimodal/audio` | Transcribe audio file |
| POST | `/api/v1/multimodal/text` | Analyse text (summarise/classify/extract) |
| POST | `/api/v1/multimodal/fuse` | Fuse multiple modality results |
| GET | `/api/v1/multimodal/stats` | Pipeline statistics |

### Example: Image Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/multimodal/image" \
  -F "file=@chart.png" \
  -F "context=Q3 sales report"
```

### Example: Multimodal Fusion

```bash
curl -X POST "http://localhost:8000/api/v1/multimodal/fuse" \
  -H "Content-Type: application/json" \
  -d '{
    "image_event_id": "uuid-from-image-call",
    "audio_event_id": "uuid-from-audio-call",
    "text": "Meeting transcript context"
  }'
```

## Use Cases

- **Medical imaging** – analyse X-rays + patient audio notes + clinical text
- **Financial reports** – parse charts + earnings call audio + press release text
- **Security monitoring** – process camera feeds + alert audio + incident logs
- **Content moderation** – multi-modal content safety screening at scale

## Docker + Kafka

```bash
docker-compose up --build
# Includes Zookeeper, Kafka broker, and API server
```
