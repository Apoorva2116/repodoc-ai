import chromadb
import ollama


# ============================================================
# Configuration
# ============================================================

DB_DIR = "chroma_db"
COLLECTION_NAME = "realworld_flask"

EMBED_MODEL = "nomic-embed-text"

DEFAULT_TOP_K = 5


# ============================================================
# Load ChromaDB
# ============================================================

client = chromadb.PersistentClient(
    path=DB_DIR
)

collection = client.get_collection(
    name=COLLECTION_NAME
)


# ============================================================
# Retrieve relevant chunks
# ============================================================

def retrieve(query, top_k=DEFAULT_TOP_K):

    # Convert the user question into an embedding
    response = ollama.embeddings(
        model=EMBED_MODEL,
        prompt=query
    )

    query_embedding = response["embedding"]

    # Search ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    retrieved = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):

        retrieved.append(
            {
                "text": document,
                "source": metadata["source"],
                "language": metadata["language"],
                "chunk_index": metadata["chunk_index"],
                "distance": distance,
            }
        )

    return retrieved


# ============================================================
# Display retrieved chunks
# ============================================================

def display_results(query, results):

    print("\n" + "=" * 70)
    print("QUERY")
    print("=" * 70)

    print(query)

    print("\n" + "=" * 70)
    print(f"TOP {len(results)} RETRIEVED CHUNKS")
    print("=" * 70)

    for i, result in enumerate(results, start=1):

        print(f"\n--- RESULT {i} ---")

        print(
            f"Source: {result['source']}"
        )

        print(
            f"Language: {result['language']}"
        )

        print(
            f"Chunk: {result['chunk_index']}"
        )

        print(
            f"Distance: {result['distance']:.4f}"
        )

        print("\nContent:")

        print(result["text"][:1200])

        print()


# ============================================================
# Test retrieval
# ============================================================

if __name__ == "__main__":

    question = input(
        "\nAsk a question about the repository: "
    ).strip()

    if not question:

        print("No question provided.")

    else:

        results = retrieve(
            question,
            top_k=DEFAULT_TOP_K
        )

        display_results(
            question,
            results
        )
