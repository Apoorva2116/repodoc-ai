import json
from pathlib import Path
from statistics import mean

questions_file = Path("benchmark/questions.json")
results_file = Path("benchmark/results_phi3_rag.json")
output_file = Path("benchmark/corrected_metrics_phi3_rag.json")

with questions_file.open() as f:
    questions = json.load(f)

with results_file.open() as f:
    saved = json.load(f)

question_map = {q["id"]: q for q in questions}
results = saved["results"]

answerable = [
    r for r in results
    if question_map[r["id"]]["type"] == "answerable"
]
unanswerable = [
    r for r in results
    if question_map[r["id"]]["type"] != "answerable"
]

metrics = {
    "model": "phi3:mini + RAG",
    "total_questions": len(results),
    "answerable_questions": len(answerable),
    "unanswerable_questions": len(unanswerable),
    "average_keyword_score": round(
        mean(r["keyword_score"] for r in answerable), 3
    ) if answerable else None,
    "average_source_score": round(
        mean(r["source_score"] for r in answerable), 3
    ) if answerable else None,
    "hit_at_5": round(
        mean(bool(r["hit_at_5"]) for r in answerable), 3
    ) if answerable else None,
    "unknown_detection_rate": round(
        mean(bool(r["unknown_detected"]) for r in unanswerable), 3
    ) if unanswerable else None,
    "false_refusal_rate": round(
        mean(bool(r["unknown_detected"]) for r in answerable), 3
    ) if answerable else None,
    "average_latency_seconds": round(
        mean(r["latency_seconds"] for r in results), 2
    ) if results else None,
}

with output_file.open("w") as f:
    json.dump(metrics, f, indent=2)

print("\nCORRECTED METRICS")
print("=" * 35)
for key, value in metrics.items():
    print(f"{key}: {value}")

print(f"\nSaved to: {output_file}")
print("\nNo AI calls were made.")
