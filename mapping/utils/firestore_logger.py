# mapping/utils/firestore_logger.py
"""
Firestore-only logging (no Cloud Storage).
- One doc per run in /runs/{runId}
- Per-iteration docs in /runs/{runId}/iterations/{i}
- Text logs as chunked docs under:
    /runs/{runId}/logs/{autoId}
    /runs/{runId}/iterations/{i}/logs/{autoId}
- Optional code snippets under:
    /runs/{runId}/iterations/{i}/code/{filename}
"""

import os
from datetime import datetime
from typing import Optional

from google.cloud import firestore  # pip install google-cloud-firestore

_PROJECT = os.environ.get("GCP_PROJECT_ID")  # must be set by your .env

# Create a single Firestore client for the process.
_fs = firestore.Client(project=_PROJECT)


def create_run_doc(run_id: str, user_desc: str) -> None:
    """Create the run doc when a pipeline starts."""
    _fs.collection("runs").document(run_id).set(
        {
            "userDesc": user_desc,
            "status": "running",
            "startedAt": datetime.utcnow(),
        },
        merge=True,
    )


def finalize_run(
    run_id: str,
    best_result: dict,
    *,
    status: str = "succeeded",
    best_iteration_index: Optional[int] = None,
) -> None:
    """Mark the run complete and write small summary fields."""
    best_iter = (
        int(best_iteration_index)
        if best_iteration_index is not None
        else int(best_result.get("iteration", -1))
    )

    br = best_result.get("break_analysis", {}) or {}
    payload = {
        "status": status,
        "endedAt": datetime.utcnow(),
        "bestIteration": best_iter,
        "bestScore": float(best_result.get("score", 0.0)),
        "comment": best_result.get("comment", ""),
        "summary": {
            "totalBreaks": int(br.get("total_breaks", 0) or 0),
            "globalChowF": br.get("global_chow_F"),
            "globalChowP": br.get("global_chow_p"),
        },
    }
    _fs.collection("runs").document(run_id).set(payload, merge=True)


def log_iteration_meta(
    run_id: str,
    i: int,
    *,
    score: float,
    hypothesis_name: str,
    comment: str = "",
) -> None:
    """Write/merge the small iteration metadata (no blobs)."""
    _fs.collection("runs").document(run_id).collection("iterations").document(
        str(i)
    ).set(
        {
            "score": float(score),
            "hypothesisName": str(hypothesis_name),
            "comment": str(comment or ""),
            "createdAt": datetime.utcnow(),
        },
        merge=True,
    )


def append_run_log(run_id: str, text: str, *, seq: int) -> None:
    """Append a chunk of terminal text at the run level."""
    _fs.collection("runs").document(run_id).collection("logs").add(
        {"seq": int(seq), "text": text, "createdAt": datetime.utcnow()}
    )


def append_iter_log(run_id: str, i: int, text: str, *, seq: int) -> None:
    """Append a chunk of terminal text at the iteration level."""
    _fs.collection("runs").document(run_id).collection("iterations").document(
        str(i)
    ).collection("logs").add(
        {"seq": int(seq), "text": text, "createdAt": datetime.utcnow()}
    )


def save_code(
    run_id: str,
    i: int,
    *,
    filename: str,
    content: str,
    language: str = "text",
) -> None:
    """Persist a small code file/snippet under an iteration."""
    _fs.collection("runs").document(run_id).collection("iterations").document(
        str(i)
    ).collection("code").document(filename).set(
        {
            "language": language,
            "content": content,
            "createdAt": datetime.utcnow(),
        }
    )
