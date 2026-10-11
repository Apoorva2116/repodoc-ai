import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

EVENT_LOG = LOG_DIR / "rag_events.jsonl"

logger = logging.getLogger("repodoc")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.FileHandler(LOG_DIR / "repodoc.log")
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    )
    logger.addHandler(handler)


def start_trace(question):
    """Create a trace record for one user question."""
    return {
        "trace_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "status": "started",
    }


def log_event(trace, event, **fields):
    """Append a structured event without overwriting earlier events."""
    record = {
        **trace,
        "event": event,
        **fields,
    }

    with EVENT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def timed_call(function, *args, **kwargs):
    """Return (result, elapsed_seconds), preserving raised exceptions."""
    started = time.perf_counter()
    try:
        result = function(*args, **kwargs)
        elapsed = time.perf_counter() - started
        return result, round(elapsed, 4)
    except Exception:
        elapsed = time.perf_counter() - started
        logger.exception(
            "Function %s failed after %.4f seconds",
            getattr(function, "__name__", "unknown"),
            elapsed,
        )
        raise


def record_question(trace, question, retrieved, answer,
                    retrieval_seconds, generation_seconds,
                    status="success", error=None):
    """Record one completed RAG request and its diagnostics."""
    distances = [float(item["distance"]) for item in retrieved]

    log_event(
        trace,
        "rag_request",
        status=status,
        retrieval_seconds=retrieval_seconds,
        generation_seconds=generation_seconds,
        total_seconds=round(retrieval_seconds + generation_seconds, 4),
        retrieved_count=len(retrieved),
        sources=list(dict.fromkeys(
            item["source"] for item in retrieved
        )),
        distances=distances,
        answer_characters=len(answer or ""),
        error=error,
    )
