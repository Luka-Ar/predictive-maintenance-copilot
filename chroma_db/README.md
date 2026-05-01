# ChromaDB Vector Store

This directory contains the ChromaDB vector database collections.

## Purpose

Stores embeddings generated from knowledge base documents for semantic search and retrieval.

## Collections

- **maintenance_knowledge** - Main collection for maintenance documents and guidelines
- Add more collections as needed for different knowledge domains

## Storage

ChromaDB data is stored here when the RAG system initializes and indexes documents.

## Note

This directory should be added to .gitignore to prevent committing vector data to git. The database will be regenerated on first run.
