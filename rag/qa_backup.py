import ollama

from rag.retrieve import retrieve


# ============================================================
# Configuration
# ============================================================

LLM_MODEL = "phi3:mini"
TOP_K = 5


# ============================================================
# Build RAG prompt
# ============================================================

def build_prompt(question, results):

    context_parts = []

    for i, result in enumerate(results, start=1):

        context_parts.append(
            f"""
SOURCE {i}
File: {result['source']}
Chunk: {result['chunk_index']}

{result['text']}
"""
        )

    context = "\n".join(context_parts)

    prompt = f"""
You are RepoDoc AI, an assistant that answers questions
about a software repository.

Answer the user's question using ONLY the repository
evidence provided below.

Rules:

1. Do not use outside knowledge.
2. Do not invent implementation details.
3. If the evidence is insufficient, say exactly:
   INSUFFICIENT EVIDENCE
4. Mention the relevant source file(s).
5. Give a concise technical explanation.
6. Base every factual claim on the retrieved evidence.

REPOSITORY EVIDENCE
===================

{context}

USER QUESTION
=============

{question}

ANSWER:
"""

    return prompt


# ============================================================
# Ask LLM
# ============================================================

def ask_llm(question, results):

    prompt = build_prompt(
        question,
        results
    )

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    question = input(
        "\nAsk a question about the repository: "
    ).strip()

    if not question:

        print("No question provided.")

    else:

        print("\nRetrieving relevant repository chunks...")

        results = retrieve(
            question,
            top_k=TOP_K
        )

        print("Generating answer with Phi-3 Mini...\n")

        answer = ask_llm(
            question,
            results
        )

        print("=" * 70)
        print("RepoDoc AI ANSWER")
        print("=" * 70)

        print(answer)

        print("\n" + "=" * 70)
        print("RETRIEVED SOURCES")
        print("=" * 70)

        seen = set()

        for result in results:

            source = result["source"]

            if source not in seen:

                print(f"- {source}")

                seen.add(source)
