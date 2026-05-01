from pathlib import Path

import chromadb
import requests


# Configuration values for the local RAG setup.
KNOWLEDGE_DIR = Path("knowledge")
CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "industrial_knowledge"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
FILE_CATEGORY_MAP = {
    "maintenance_sop.txt": "SOP",
    "safety_guidelines.txt": "Safety",
    "machine_manual.txt": "Manual",
    "failure_cases.txt": "Failure Case",
}


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping character chunks."""
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk)

        # Move forward while keeping overlap between chunks.
        start += chunk_size - overlap

    return chunks


def get_embedding(text):
    """Get an embedding vector from the local Ollama embeddings API."""
    payload = {
        "model": EMBED_MODEL,
        "prompt": text,
    }

    response = requests.post(OLLAMA_EMBED_URL, json=payload, timeout=60)
    response.raise_for_status()

    data = response.json()
    embedding = data.get("embedding")

    if not embedding:
        raise ValueError("No embedding returned by Ollama.")

    return embedding


def index_documents():
    """Read text files, chunk them, embed them, and store in ChromaDB."""
    txt_files = sorted(KNOWLEDGE_DIR.glob("*.txt"))

    if not txt_files:
        print("No .txt files found in knowledge/ folder.")
        return

    # Create a persistent local ChromaDB client and refresh the collection.
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    total_chunks = 0

    for file_path in txt_files:
        text = file_path.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        category = FILE_CATEGORY_MAP.get(file_path.name, "Reference")

        for chunk_index, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)

            # Stable ID prevents duplicate entries when re-indexing the same file.
            doc_id = f"{file_path.name}_{chunk_index}"

            collection.upsert(
                ids=[doc_id],
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[
                    {
                        "source": file_path.name,
                        "category": category,
                        "chunk_index": chunk_index,
                    }
                ],
            )

            total_chunks += 1

    print(f"Indexed {total_chunks} chunks into collection '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    index_documents()
