#!/usr/bin/env python3
import sys, os, json, io, datetime, base64, warnings
from contextlib import redirect_stdout
from typing import Optional

import numpy as np
import pandas as pd

# Headless matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")  # quiet noisy warnings

# ----- Repo root & cwd -----
HERE = os.path.dirname(os.path.abspath(__file__))     # …/enha
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..")) # …/enha-mapping
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
os.chdir(REPO_ROOT)

from main import run_pipeline  # returns the single BEST result (dict) per your code

# ---------- helpers ----------
def df_to_table(df: pd.DataFrame, limit: int = 200):
    if df is None:
        return None
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%dT%H:%M:%S")
    if limit is not None and len(df) > limit:
        df = df.head(limit)
    return {
        "__type__": "dataframe",
        "columns": list(df.columns),
        "rows": df.to_dict(orient="records"),
        "truncated": limit is not None and len(df) >= limit,
    }

def to_primitive(x):
    if x is None or isinstance(x, (bool, int, float, str)):
        return x
    if isinstance(x, (np.integer,)):   return int(x)
    if isinstance(x, (np.floating,)):  return float(x)
    if isinstance(x, (np.bool_,)):     return bool(x)
    if isinstance(x, (datetime.date, datetime.datetime)): return x.isoformat()
    if isinstance(x, (set, frozenset, tuple, list)):
        return [to_primitive(v) for v in list(x)]
    if isinstance(x, dict):
        return {str(k): to_primitive(v) for k, v in x.items()}
    if isinstance(x, pd.Series):
        return to_primitive(list(x))
    if isinstance(x, pd.DataFrame):
        return df_to_table(x)
    return {"__type__": type(x).__name__}

def plot_timeseries_png(ts: pd.DataFrame, ycol: str) -> Optional[str]:
    if ts is None or not isinstance(ts, pd.DataFrame) or not isinstance(ycol, str) or ycol not in ts.columns:
        return None

    # choose x axis
    if isinstance(ts.index, pd.DatetimeIndex):
        x = ts.index
        xlab = ts.index.name or "date"
    else:
        dt_cols = [c for c in ts.columns if pd.api.types.is_datetime64_any_dtype(ts[c])]
        if dt_cols:
            x = ts[dt_cols[0]]
            xlab = dt_cols[0]
        else:
            x = ts.iloc[:, 0]
            xlab = ts.columns[0]

    fig, ax = plt.subplots(figsize=(7, 3.5), dpi=144)
    ax.plot(x, ts[ycol])
    ax.set_title("Rolling Count")
    ax.set_xlabel(xlab)
    ax.set_ylabel(ycol)
    ax.grid(True, alpha=0.25)
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")

def json_out(payload):
    print(json.dumps(payload))

# ---------- main ----------
def main():
    prompt = sys.argv[1] if len(sys.argv) > 1 else ""

    # Your LLM client needs this; fail fast if missing
    if not os.environ.get("GEMINI_API_KEY"):
        json_out({"ok": False, "error": "GEMINI_API_KEY is not set on the server."})
        return

    try:
        # Keep stdout clean; pipeline prints -> stderr
        with redirect_stdout(sys.stderr):
            best_result = run_pipeline(prompt)  # <-- returns the BEST single result

        if not best_result:
            json_out({"ok": False, "error": "No result produced"})
            return

        hyp = (best_result or {}).get("hypothesis", {}) or {}
        ts  = (best_result or {}).get("timeseries")
        y   = (best_result or {}).get("rolling_col")

        plot_png = plot_timeseries_png(ts, y) if isinstance(ts, pd.DataFrame) and isinstance(y, str) else None

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
            "timeseries": to_primitive(ts) if isinstance(ts, pd.DataFrame) else None,
            "rolling_col": to_primitive(y),
            "break_analysis": to_primitive((best_result or {}).get("break_analysis")),
            "plot_png": plot_png,
        }

        json_out({"ok": True, "data": payload})

    except Exception as e:
        json_out({"ok": False, "error": str(e)})

if __name__ == "__main__":
    main()