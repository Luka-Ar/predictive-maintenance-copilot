import chromadb
import requests


# Hardcoded question for the RAG query.
QUESTION = "What should we check when torque and tool wear are high?"

# Ollama endpoints and model names.
EMBED_URL = "http://localhost:11434/api/embeddings"
GENERATE_URL = "http://localhost:11434/api/generate"
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "gemma4:e2b"

# ChromaDB configuration.
CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "industrial_knowledge"
TOP_K = 3


def get_embedding(text):
    """Generate an embedding for the given text using Ollama."""
    payload = {"model": EMBED_MODEL, "prompt": text}
    response = requests.post(EMBED_URL, json=payload, timeout=60)
    response.raise_for_status()

    data = response.json()
    embedding = data.get("embedding")

    if not embedding:
        raise ValueError("No embedding returned by Ollama.")

    return embedding


def build_prompt(context, question):
    """Build a prompt for Gemma using retrieved context."""
    return (
        "You are a maintenance assistant.\n"
        "Answer only from the provided context. If insufficient, say so.\n\n"
        f"Context:\n{context}\n\n"
        f"Question:\n{question}\n\n"
        "Answer:"
    )


def query_rag():
    """Retrieve relevant chunks and ask the local LLM to answer."""
    # Connect to local ChromaDB and load the collection.
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)

    # Embed the question for similarity search.
    question_embedding = get_embedding(QUESTION)

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=TOP_K,
        include=["documents", "metadatas"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    # Print retrieved chunks and metadata.
    print("Retrieved context:")
    for index, (doc, meta) in enumerate(zip(documents, metadatas), start=1):
        source = meta.get("source", "unknown")
        chunk_index = meta.get("chunk_index", "unknown")
        print(f"\n--- Chunk {index} (source: {source}, chunk: {chunk_index}) ---")
        print(doc)

    context_text = "\n\n".join(documents)
    prompt = build_prompt(context_text, QUESTION)

    # Call Gemma to generate the final answer.
    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "temperature": 0.2,
        "num_predict": 200,
    }

    response = requests.post(GENERATE_URL, json=payload, timeout=120)

    if response.status_code != 200:
        print("OLLAMA ERROR STATUS:")
        print(response.status_code)
        print("OLLAMA ERROR BODY:")
        print(response.text)
        return

    data = response.json()

    final_answer = data.get("response", "").strip()

    print("\nFINAL ANSWER:\n")
    print(final_answer if final_answer else "No response returned by Gemma.")


if __name__ == "__main__":
    query_rag()
