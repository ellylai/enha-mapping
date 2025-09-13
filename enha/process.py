#!/usr/bin/env python3
import sys, os, json, io, datetime
from contextlib import redirect_stdout

import numpy as np
import pandas as pd

# ----- Make repo root importable & set CWD to it -----
HERE = os.path.dirname(os.path.abspath(__file__))     # …/enha
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..")) # …/enha-mapping
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
os.chdir(REPO_ROOT)

from main import run_pipeline  # your function that returns best_result (a dict)

# ---------- helpers: JSON-safe converters ----------

def df_to_table(df: pd.DataFrame, limit: int = 100):
    if df is None:
        return None
    df = df.copy()
    # stringify datetimes
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%dT%H:%M:%S")
    # clip to avoid huge payloads
    if limit is not None and len(df) > limit:
        df = df.head(limit)
    return {
        "__type__": "dataframe",
        "columns": list(df.columns),
        "rows": df.to_dict(orient="records"),
        "truncated": limit is not None and len(df) >= limit,
    }

def to_primitive(x):
    # fast path for common types
    if x is None or isinstance(x, (bool, int, float, str)):
        return x
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, (datetime.date, datetime.datetime)):
        return x.isoformat()
    if isinstance(x, (set, frozenset, tuple, list)):
        return [to_primitive(v) for v in list(x)]
    if isinstance(x, dict):
        # recursively sanitize dict
        return {str(k): to_primitive(v) for k, v in x.items()}
    if isinstance(x, pd.Series):
        return to_primitive(list(x))
    if isinstance(x, pd.DataFrame):
        return df_to_table(x)
    # fallback: describe unknown objects by class name (don’t inline heavy models)
    return {"__type__": type(x).__name__}

def summarize_break_analysis(ba):
    if not isinstance(ba, dict):
        return to_primitive(ba)
    # Pick only light, useful fields if present; drop model objects
    out = {}
    # integers / floats
    for key in ["total_breaks", "break_score"]:
        if key in ba:
            out[key] = to_primitive(ba[key])
    # arrays
    if "break_dates" in ba:
        out["break_dates"] = [to_primitive(d) for d in ba["break_dates"]]
    if "icd_transition_alignment" in ba:
        out["icd_transition_alignment"] = [to_primitive(x) for x in ba["icd_transition_alignment"]]
    # local_chow: keep only F stats & indices/dates if present
    if "local_chow" in ba and isinstance(ba["local_chow"], list):
        trimmed = []
        for bp in ba["local_chow"]:
            if isinstance(bp, dict):
                trimmed.append({
                    "index": to_primitive(bp.get("index")),
                    "date": to_primitive(bp.get("date")),
                    "F": to_primitive(bp.get("F")),
                })
        out["local_chow"] = trimmed
    # segments: keep slope/intercept only
    if "segments" in ba and isinstance(ba["segments"], list):
        out["segments"] = []
        for seg in ba["segments"]:
            if isinstance(seg, dict):
                out["segments"].append({
                    "slope": to_primitive(seg.get("slope")),
                    "intercept": to_primitive(seg.get("intercept")),
                    "start": to_primitive(seg.get("start")),
                    "end": to_primitive(seg.get("end")),
                })
    return out

# ---------- main ----------

def json_out(payload):
    # print ONLY JSON to stdout
    print(json.dumps(payload))

def main():
    prompt = sys.argv[1] if len(sys.argv) > 1 else ""

    # Optional: enforce presence of API key needed by your LLM client
    if not os.environ.get("GEMINI_API_KEY"):
        json_out({"ok": False, "error": "GEMINI_API_KEY is not set on the server."})
        return

    try:
        # redirect prints from the pipeline to stderr so stdout stays pure JSON
        with redirect_stdout(sys.stderr):
            best_result = run_pipeline(prompt)

        # Build a compact, JSON-safe payload
        hyp = (best_result or {}).get("hypothesis", {}) or {}
        payload = {
            "hypothesis": {
                "name": hyp.get("name"),
                "icd9_codes": to_primitive(hyp.get("icd9_codes")),
                "icd10_codes": to_primitive(hyp.get("icd10_codes")),
            },
            "score": to_primitive((best_result or {}).get("score")),
            "artificial_break": to_primitive((best_result or {}).get("artificial_break")),
            "artificial_slope": to_primitive((best_result or {}).get("artificial_slope")),
            "comment": to_primitive((best_result or {}).get("comment")),
            "timeseries": df_to_table((best_result or {}).get("timeseries"), limit=100),
            "rolling_col": to_primitive((best_result or {}).get("rolling_col")),
            "break_analysis": summarize_break_analysis((best_result or {}).get("break_analysis")),
        }

        json_out({"ok": True, "data": payload})

    except Exception as e:
        # Surface Python errors as JSON (don’t crash the Node route)
        json_out({"ok": False, "error": str(e)})

if __name__ == "__main__":
    main()