# Personal Knowledge Base

A self-hosted AI system that ingests voice messages, converts them to structured knowledge, and exposes a conversational interface that can reason over personal history.

Audio files are transcribed, translated, summarized, and semantically indexed. Everything is stored permanently in a vector database and queryable via a chat interface accessible over Tailscale. Raw files are archived to Nextcloud and deleted locally after a configurable number of days.

See **[ROADMAP.md](ROADMAP.md)** for the full architecture and implementation plan.

---

## What It Does

- Accepts audio file uploads via a web app or local directory
- Runs a processing pipeline (on a schedule or on demand) that:
  - Transcribes audio with faster-whisper
  - Translates, summarizes, and extracts structured information with Gemma-4-E4B via llama.cpp
  - Stores results in SQLite and a Qdrant vector database
  - Maintains a 7-day rolling JSON cache for recent entries
  - Archives raw audio to Nextcloud and deletes local copies after N days
- Exposes a RAG-augmented chat endpoint that retrieves relevant personal history when answering questions
- Integrates with Open WebUI as a full chat interface

---

## Stack

- **Backend**: Python / FastAPI
- **LLM**: Gemma-4-E4B running in llama.cpp (`llama-server`)
- **Transcription**: faster-whisper (Phase 1–3); Gemma-4-E4B native audio (Phase 4, pending llama.cpp support)
- **Vector DB**: Qdrant (Docker)
- **Metadata DB**: SQLite
- **Scheduling**: APScheduler
- **Archive**: Nextcloud (WebDAV)
- **Remote Access**: Tailscale
- **Chat UI**: Open WebUI

---

## Project Status

This project is in active development. See [ROADMAP.md](ROADMAP.md) for phased implementation details.

**Phase 1**: Foundation & Infrastructure — file ingestion, Nextcloud archiving, scheduling  
**Phase 2**: Processing Pipeline — transcription + LLM post-processing  
**Phase 3**: Vector DB & RAG — semantic search and chat interface  
**Phase 4**: Native audio via Gemma-4-E4B (blocked on llama.cpp issue #21325)
