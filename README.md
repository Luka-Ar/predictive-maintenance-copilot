# Predictive Maintenance Copilot — Hybrid Industrial AI Decision Support System

A hybrid ML + RAG + Local LLM platform that transforms machine sensor data into predictive maintenance intelligence, operational alerts, and actionable maintenance recommendations.

## Overview

Predictive Maintenance Copilot is a Phase 2 evolution of an industrial ML dashboard into a full operational intelligence platform. It combines a classical ML prediction engine with governance, condition alerts, and a local LLM powered by retrieval-augmented knowledge.

## Phase Evolution

- Phase 1: ML Predictive Dashboard
- Phase 2: Hybrid AI + RAG + Governance

## Core Features

- ML prediction engine for failure risk probability
- Hybrid AI explanations with local Gemma via Ollama
- RAG knowledge retrieval using ChromaDB
- Condition alerts with severity governance and actions
- Trend intelligence signals (foundation for Phase 3)
- Operational intelligence surface for alerts, actions, and governance
- Clean FastAPI + Next.js architecture

## Architecture Diagram

```
Sensor Input
  → ML Prediction Engine
  → Rule Governance Layer
  → RAG Knowledge Retrieval (ChromaDB)
  → Gemma / Local LLM Reasoning
  → Condition Alerts
  → Trend Intelligence (Phase 3 placeholder)
  → Recommended Actions
  → Frontend Dashboard
```

## Tech Stack

Backend
- Python 3.10+
- FastAPI + Uvicorn
- scikit-learn
- SQLite
- ChromaDB

Frontend
- Next.js (React)
- TypeScript
- Tailwind CSS

ML + LLM
- RandomForest (baseline)
- Ollama (local runtime)
- Gemma (local LLM)

## Project Structure

```
predictive-maintenance-copilot/
├── api/            FastAPI backend and governance
├── web/            Next.js frontend UI
├── rag/            RAG indexing and query tools
├── knowledge/      Curated knowledge base
├── chroma_db/      Local vector database storage
├── models/         Trained model artifacts
├── training/       Training pipeline
├── README.md       Product overview
├── CHANGELOG.md    Release history
├── ROADMAP.md      Phase planning
├── CONTRIBUTING.md Contribution guide
├── LICENSE         MIT license
├── requirements.txt Python dependencies
└── .gitignore      Repo hygiene
```

## Screenshots

Placeholders (add images to screenshots/ and update links):
- Dashboard Overview
  - screenshots/dashboard-overview.png
- Condition Alerts
  - screenshots/condition-alerts.png
- Recommended Actions
  - screenshots/recommended-actions.png
- Knowledge Sources
  - screenshots/knowledge-sources.png

## Installation Guide

Prerequisites
- Python 3.10+
- Node.js 18+
- Ollama

Quick setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Local Development Setup

Terminal 1: Ollama
```bash
ollama pull gemma3:1b
ollama pull nomic-embed-text
ollama run gemma3:1b
```

Terminal 2: Backend
```bash
uvicorn api.main:app --reload
```

Terminal 3: Frontend
```bash
cd web
npm install
npm run dev
```

## How It Works

1. Sensor inputs are normalized and passed into the ML model.
2. Rule governance classifies conditions and triggers alerts.
3. RAG retrieves relevant maintenance context from ChromaDB.
4. Gemma generates explanations constrained by validated status.
5. The UI renders risk, alerts, trends, and actions.

## Risk Tiers

Example mapping used for operational communication:
- 0–10%: Normal
- 10–25%: Advisory
- 25–50%: Warning
- 50%+: Critical

## Condition Alerts

- Thermal Warning / Alert / Critical Thermal Alert
- Torque Load Alert
- Preventive Wear Advisory / Maintenance Alert / Urgent Wear Alert

## Recommended Actions

Actions are aligned to alert severity, such as:
- Monitor wear trend
- Inspect tool condition
- Check cooling efficiency

## Knowledge Sources / RAG

The RAG layer uses a curated knowledge base:
- maintenance_sop.txt
- safety_guidelines.txt
- machine_manual.txt
- failure_cases.txt

## Future Roadmap

See ROADMAP.md for Phase 3 planning.

## Version History

v1.0 — Phase 1
- Initial predictive maintenance ML model
- Dashboard UI
- Failure probability prediction

v2.0 — Phase 2
- Gemma integration
- RAG knowledge base
- ChromaDB
- Condition alerts
- Maintenance governance
- Recommended actions
- Operational intelligence

## License

MIT License
