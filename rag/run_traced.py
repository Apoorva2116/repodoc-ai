import sys

from rag.retrieve import retrieve
from rag.qa import ask_llm, TOP_K, LLM_MODEL, AVAILABLE_MODELS
from rag.observability import (
    start_trace,
    log_event,
    timed_call,
    record_question,
)


def run_traced(question, show_output=True, model=LLM_MODEL):
    """Run retrieval and generation while recording observability data."""
    if model not in AVAILABLE_MODELS:
        raise ValueError(f"Unsupported model: {model}")

    trace = start_trace(question)
    trace["model"] = model

    retrieved = []
    answer = ""
    retrieval_seconds = 0.0
    generation_seconds = 0.0

    try:
        retrieved, retrieval_seconds = timed_call(
            retrieve, question, top_k=TOP_K
        )

        log_event(
            trace,
            "retrieval_complete",
            elapsed_seconds=retrieval_seconds,
            retrieved_count=len(retrieved),
            sources=list(dict.fromkeys(
                item["source"] for item in retrieved
            )),
            distances=[float(item["distance"]) for item in retrieved],
        )

        answer, generation_seconds = timed_call(
            ask_llm, question, retrieved, model=model
        )

        record_question(
            trace,
            question,
            retrieved,
            answer,
            retrieval_seconds,
            generation_seconds,
        )

        if show_output:
            print("\n" + "=" * 65)
            print("RepoDoc AI")
            print(f"Model: {model}")
            print("=" * 65)
            print(answer)

            print("\nRetrieved sources:")
            for source in dict.fromkeys(
                item["source"] for item in retrieved
            ):
                print(f"- {source}")

            print(f"\nRetrieval time: {retrieval_seconds:.2f}s")
            print(f"Generation time: {generation_seconds:.2f}s")
            print(
                f"Total time: "
                f"{retrieval_seconds + generation_seconds:.2f}s"
            )
            print(f"Trace ID: {trace['trace_id']}")

        return {
            "answer": answer,
            "chunks": retrieved,
            "trace_id": trace["trace_id"],
            "retrieval_seconds": retrieval_seconds,
            "generation_seconds": generation_seconds,
            "model": model,
        }

    except Exception as exc:
        record_question(
            trace,
            question,
            retrieved,
            answer,
            retrieval_seconds,
            generation_seconds,
            status="error",
            error=str(exc),
        )
        raise


def run(question):
    return run_traced(question, show_output=True)


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]).strip()

    if not question:
        question = input("Ask RepoDoc AI: ").strip()

    if not question:
        print("Please enter a question.")
        raise SystemExit(1)

    run(question)
