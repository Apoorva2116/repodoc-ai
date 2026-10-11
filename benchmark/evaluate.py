import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent)
)
import json
import time
from pathlib import Path

from rag.retrieve import retrieve
from rag.qa import ask_llm


# ============================================================
# Configuration
# ============================================================

QUESTIONS_FILE = Path("benchmark/questions.json")
OUTPUT_FILE = Path("benchmark/results_phi3_rag.json")

TOP_K = 5


# ============================================================
# Load benchmark
# ============================================================

def load_questions():

    with open(
        QUESTIONS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# Keyword scoring
# ============================================================

def keyword_score(answer, keywords):

    if not keywords:
        return 1.0

    answer_lower = answer.lower()

    matched = 0

    for keyword in keywords:

        if keyword.lower() in answer_lower:
            matched += 1

    return matched / len(keywords)


# ============================================================
# Source scoring
# ============================================================

def source_score(results, gold_sources):

    if not gold_sources:
        return 1.0

    retrieved_sources = {
        result["source"]
        for result in results
    }

    matched = sum(
        1
        for source in gold_sources
        if source in retrieved_sources
    )

    return matched / len(gold_sources)


# ============================================================
# Retrieval Hit@K
# ============================================================

def retrieval_hit(results, gold_sources):

    if not gold_sources:
        return None

    retrieved_sources = {
        result["source"]
        for result in results
    }

    return int(
        any(
            source in retrieved_sources
            for source in gold_sources
        )
    )


# ============================================================
# Unknown detection
# ============================================================

def detects_unknown(answer):

    answer_lower = answer.lower()

    indicators = [
        "insufficient evidence",
        "not enough evidence",
        "cannot find",
        "can't find",
        "not provided",
        "not mentioned",
        "not specified",
        "does not appear",
        "not available in the repository",
        "repository does not",
        "no evidence"
    ]

    return int(
        any(
            phrase in answer_lower
            for phrase in indicators
        )
    )


# ============================================================
# Main evaluation
# ============================================================

def main():

    questions = load_questions()

    print("=" * 70)
    print("RepoDoc AI - Phi-3 Mini + RAG Evaluation")
    print("=" * 70)

    print(
        f"\nQuestions: {len(questions)}"
    )

    results = []

    total_keyword_score = 0.0
    total_source_score = 0.0

    answerable_count = 0
    unknown_count = 0

    hit_at_5_total = 0

    total_latency = 0.0

    # --------------------------------------------------------
    # Run every question
    # --------------------------------------------------------

    for index, item in enumerate(
        questions,
        start=1
    ):

        question = item["question"]
        question_type = item["type"]

        print(
            f"\n[{index}/{len(questions)}] "
            f"{question}"
        )

        start_time = time.perf_counter()

        # Retrieve evidence
        retrieved = retrieve(
            question,
            top_k=TOP_K
        )

        # Generate answer
        answer = ask_llm(
            question,
            retrieved
        )

        end_time = time.perf_counter()

        latency = end_time - start_time

        total_latency += latency

        # ----------------------------------------------------
        # Scores
        # ----------------------------------------------------

        kw_score = keyword_score(
            answer,
            item["gold_keywords"]
        )

        src_score = source_score(
            retrieved,
            item["gold_sources"]
        )

        hit5 = retrieval_hit(
            retrieved,
            item["gold_sources"]
        )

        unknown = detects_unknown(
            answer
        )

        # ----------------------------------------------------
        # Aggregate
        # ----------------------------------------------------

        if question_type == "answerable":

            answerable_count += 1

            total_keyword_score += kw_score
            total_source_score += src_score

            if hit5 == 1:
                hit_at_5_total += 1

        else:

            if unknown == 1:
                unknown_count += 1

        # ----------------------------------------------------
        # Save result
        # ----------------------------------------------------

        result = {
            "id": item["id"],
            "question": question,
            "type": question_type,
            "answer": answer,
            "retrieved_sources": [
                result["source"]
                for result in retrieved
            ],
            "keyword_score": kw_score,
            "source_score": src_score,
            "hit_at_5": hit5,
            "unknown_detected": unknown,
            "latency_seconds": round(
                latency,
                3
            )
        }

        results.append(result)

        print(
            f"  Keyword score: {kw_score:.2f}"
        )

        print(
            f"  Source score:  {src_score:.2f}"
        )

        if hit5 is not None:

            print(
                f"  Hit@5:         {hit5}"
            )

        print(
            f"  Unknown:       {unknown}"
        )

        print(
            f"  Latency:       {latency:.2f}s"
        )

    # ========================================================
    # Final metrics
    # ========================================================

    if answerable_count > 0:

        avg_keyword_score = (
            total_keyword_score
            / answerable_count
        )

        avg_source_score = (
            total_source_score
            / answerable_count
        )

        hit_at_5 = (
            hit_at_5_total
            / answerable_count
        )

    else:

        avg_keyword_score = 0
        avg_source_score = 0
        hit_at_5 = 0

    unanswerable_count = (
        len(questions)
        - answerable_count
    )

    if unanswerable_count > 0:

        unknown_detection_rate = (
            unknown_count
            / unanswerable_count
        )

    else:

        unknown_detection_rate = 0

    avg_latency = (
        total_latency
        / len(questions)
    )

    metrics = {

        "model": "phi3:mini",

        "rag": True,

        "top_k": TOP_K,

        "total_questions": len(questions),

        "answerable_questions":
            answerable_count,

        "unanswerable_questions":
            unanswerable_count,

        "average_keyword_score":
            round(
                avg_keyword_score,
                3
            ),

        "average_source_score":
            round(
                avg_source_score,
                3
            ),

        "hit_at_5":
            round(
                hit_at_5,
                3
            ),

        "unknown_detection_rate":
            round(
                unknown_detection_rate,
                3
            ),

        "average_latency_seconds":
            round(
                avg_latency,
                3
            )
    }

    # ========================================================
    # Save results
    # ========================================================

    output = {
        "metrics": metrics,
        "results": results
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=2
        )

    # ========================================================
    # Print summary
    # ========================================================

    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)

    print(
        f"Average keyword score: "
        f"{avg_keyword_score:.3f}"
    )

    print(
        f"Average source score:  "
        f"{avg_source_score:.3f}"
    )

    print(
        f"Hit@5:                 "
        f"{hit_at_5:.3f}"
    )

    print(
        f"Unknown detection:     "
        f"{unknown_detection_rate:.3f}"
    )

    print(
        f"Average latency:       "
        f"{avg_latency:.3f}s"
    )

    print(
        f"\nResults saved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
