# Knowledge Base

This directory contains documents and manuals for the RAG (Retrieval-Augmented Generation) system.

## Contents

- **test_manual.txt** - Sample test manual with machine profiles, failure indicators, and maintenance guidelines
- Additional documents can be added here for semantic search and retrieval

## Usage

Documents in this folder are indexed by ChromaDB for semantic search via the RAG system. The embeddings are generated using the nomic-embed-text model from Ollama.

## File Format

Supports:
- .txt (plain text)
- .md (markdown)
- Add more formats as needed

## Integration

These documents are loaded and embedded into the vector database (chroma_db/) for retrieval-augmented generation, enabling the LLM to provide context-aware explanations based on maintenance knowledge.
