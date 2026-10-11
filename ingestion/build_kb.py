from pathlib import Path
import re
import hashlib

import chromadb
import ollama


# ============================================================
# Configuration
# ============================================================

REPO = Path("corpus")
DB_DIR = "chroma_db"
COLLECTION_NAME = "realworld_flask"

EMBED_MODEL = "nomic-embed-text"

# Keep chunks small enough for the embedding model
CHUNK_SIZE = 250
OVERLAP = 80


# ============================================================
# File filtering
# ============================================================

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
}

EXCLUDED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pyc",
}

INCLUDED_EXTENSIONS = {
    ".py",
    ".md",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".ini",
    ".sh",
    ".txt",
}

INCLUDED_FILENAMES = {
    "Dockerfile",
    "README",
    "LICENSE",
}


def should_include(path: Path) -> bool:
    """
    Decide whether a repository file should be included
    in the knowledge base.
    """

    # Exclude unwanted directories
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return False

    # Never include environment secrets
    if path.name == ".env":
        return False

    # Exclude binary/cache files
    if path.suffix.lower() in EXCLUDED_EXTENSIONS:
        return False

    # Include important extensionless files
    if path.name in INCLUDED_FILENAMES:
        return True

    # Include supported file types
    return path.suffix.lower() in INCLUDED_EXTENSIONS


# ============================================================
# Language detection
# ============================================================

def get_language(path: Path) -> str:

    suffix = path.suffix.lower()

    languages = {
        ".py": "python",
        ".md": "markdown",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".json": "json",
        ".toml": "toml",
        ".ini": "ini",
        ".sh": "shell",
        ".txt": "text",
    }

    if path.name == "Dockerfile":
        return "dockerfile"

    return languages.get(suffix, "text")


# ============================================================
# Generic text chunking
# ============================================================

def split_text(text: str):

    words = text.split()

    if len(words) <= CHUNK_SIZE:
        return [text.strip()]

    chunks = []

    start = 0

    while start < len(words):

        end = min(start + CHUNK_SIZE, len(words))

        chunk = " ".join(words[start:end]).strip()

        if chunk:
            chunks.append(chunk)

        if end == len(words):
            break

        start = end - OVERLAP

    return chunks


# ============================================================
# Python-aware chunking
# ============================================================

def split_python(content: str):

    # Split around top-level classes/functions where possible
    pattern = re.compile(
        r"(?=^(?:async\s+def|def|class)\s+\w+)",
        re.MULTILINE,
    )

    parts = re.split(pattern, content)

    chunks = []

    for part in parts:

        part = part.strip()

        if not part:
            continue

        # Keep reasonably sized functions/classes together
        if len(part.split()) <= CHUNK_SIZE:
            chunks.append(part)

        else:
            # Split oversized functions/classes
            chunks.extend(split_text(part))

    return chunks


# ============================================================
# Create chunks + metadata
# ============================================================

def make_chunks(path: Path, content: str):

    language = get_language(path)

    if language == "python":
        raw_chunks = split_python(content)
    else:
        raw_chunks = split_text(content)

    results = []

    for index, chunk in enumerate(raw_chunks):

        chunk_id = hashlib.md5(
            f"{path}:{index}:{chunk}".encode()
        ).hexdigest()

        results.append(
            {
                "id": chunk_id,

                "text": chunk,

                "metadata": {
                    "source": str(path),
                    "file_type": path.suffix.lower() or path.name,
                    "language": language,
                    "chunk_index": index,
                },
            }
        )

    return results


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 60)
    print("RepoDoc AI - Building Knowledge Base")
    print("=" * 60)

    # --------------------------------------------------------
    # Find repository files
    # --------------------------------------------------------

    files = [
        path
        for path in REPO.rglob("*")
        if path.is_file() and should_include(path)
    ]

    print(f"\nFiles found: {len(files)}")

    # --------------------------------------------------------
    # Create chunks
    # --------------------------------------------------------

    all_chunks = []

    for path in sorted(files):

        try:

            content = path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            if not content.strip():
                continue

            chunks = make_chunks(path, content)

            all_chunks.extend(chunks)

            print(
                f"{path}: {len(chunks)} chunks"
            )

        except Exception as e:

            print(
                f"SKIPPED {path}: {e}"
            )

    print("\n" + "=" * 60)
    print(f"Total chunks: {len(all_chunks)}")
    print("=" * 60)

    # --------------------------------------------------------
    # Connect to ChromaDB
    # --------------------------------------------------------

    print("\nConnecting to ChromaDB...")

    client = chromadb.PersistentClient(
        path=DB_DIR
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Delete previous collection so we don't create
    # duplicate chunks when rebuilding the KB.
    # --------------------------------------------------------

    try:

        client.delete_collection(
            COLLECTION_NAME
        )

        print(
            f"Deleted existing collection: "
            f"{COLLECTION_NAME}"
        )

    except Exception:

        print(
            "No existing collection found. "
            "Creating a new one."
        )

    # --------------------------------------------------------
    # Create clean collection
    # --------------------------------------------------------

    collection = client.create_collection(
        name=COLLECTION_NAME,

        metadata={
            "description":
                "RepoDoc AI knowledge base for RealWorld Flask"
        },
    )

    # --------------------------------------------------------
    # Generate embeddings
    # --------------------------------------------------------

    print(
        "\nAdding chunks and generating embeddings..."
    )

    batch_size = 50

    for start in range(
        0,
        len(all_chunks),
        batch_size,
    ):

        batch = all_chunks[
            start:start + batch_size
        ]

        embeddings = []

        for item in batch:

            response = ollama.embeddings(
                model=EMBED_MODEL,
                prompt=item["text"],
            )

            embeddings.append(
                response["embedding"]
            )

        collection.upsert(

            ids=[
                item["id"]
                for item in batch
            ],

            documents=[
                item["text"]
                for item in batch
            ],

            metadatas=[
                item["metadata"]
                for item in batch
            ],

            embeddings=embeddings,
        )

        current = min(
            start + batch_size,
            len(all_chunks),
        )

        print(
            f"Indexed {current}/"
            f"{len(all_chunks)} chunks"
        )

    # --------------------------------------------------------
    # Final verification
    # --------------------------------------------------------

    final_count = collection.count()

    print("\n" + "=" * 60)
    print("KNOWLEDGE BASE READY")
    print("=" * 60)

    print(
        f"Collection: {COLLECTION_NAME}"
    )

    print(
        f"Chunks generated: {len(all_chunks)}"
    )

    print(
        f"Chunks stored: {final_count}"
    )

    print(
        f"Database: {DB_DIR}/"
    )

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    if final_count != len(all_chunks):

        print("\nWARNING:")
        print(
            "Stored chunk count does not match "
            "generated chunk count."
        )

    else:

        print(
            "\n✓ Knowledge base count verified."
        )


if __name__ == "__main__":
    main()
