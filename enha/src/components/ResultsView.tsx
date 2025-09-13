"use client";

import { useState, useMemo } from "react";

type DataFrameLike = {
  __type__: "dataframe";
  columns: string[];
  rows: Array<Record<string, any>>;
  truncated?: boolean;
};

function isDataFrameLike(x: any): x is DataFrameLike {
  return !!x && x.__type__ === "dataframe" && Array.isArray(x.columns) && Array.isArray(x.rows);
}

export type Iteration = {
  index: number;
  hypothesis?: {
    name?: string;
    icd9_codes?: string[];
    icd10_codes?: string[];
  };
  score?: number | string;
  artificial_break?: boolean;
  artificial_slope?: number | string | null;
  comment?: string;
  timeseries?: {
    __type__: "dataframe";
    columns: string[];
    rows: Array<Record<string, any>>;
    truncated?: boolean;
  } | null;
  rolling_col?: string;
  plot_png?: string | null;
};

export type ResultsPayload = {
  iterations: Iteration[];
  bestIndex: number;
  best?: Iteration | null;
};

export default function ResultsView({ data }: { data: ResultsPayload }) {
  const { iterations = [], bestIndex = 0 } = data || {};
  const [selected, setSelected] = useState<number>(bestIndex);

  const sel = useMemo(
    () => iterations.find((it) => it.index === selected) ?? iterations[bestIndex] ?? null,
    [iterations, selected, bestIndex]
  );

  const df = isDataFrameLike(sel?.timeseries) ? sel!.timeseries : null;


  return (
    <section className="mx-auto max-w-4xl flex flex-col gap-6">
      {/* Thumbnails */}
      {iterations.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {iterations.slice(0, 9).map((it) => {
            const isBest = it.index === bestIndex;
            const isSel = it.index === selected;
            return (
              <button
                key={it.index}
                onClick={() => setSelected(it.index)}
                className={[
                  "group relative rounded-lg border p-2 text-left",
                  isSel ? "ring-2 ring-blue-500 border-blue-300" : "border-gray-200 dark:border-gray-800",
                  isBest ? "bg-blue-50/50 dark:bg-blue-900/10" : "",
                ].join(" ")}
              >
                {it.plot_png ? (
                  <img
                    src={`data:image/png;base64,${it.plot_png}`}
                    alt={`Iteration ${it.index} chart`}
                    className="h-32 w-full object-contain rounded"
                  />
                ) : (
                  <div className="h-32 w-full grid place-items-center text-xs text-gray-500">
                    No chart
                  </div>
                )}
                <div className="mt-2 flex items-center justify-between">
                  <div className="text-xs">
                    <div className="font-medium">Iter {it.index}</div>
                    <div className="text-gray-500">Score: {it.score ?? "—"}</div>
                  </div>
                  {isBest && (
                    <span className="rounded bg-blue-600 px-2 py-0.5 text-[10px] font-semibold text-white">
                      BEST
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* Main panel for selected iteration */}
      {sel && (
        <div className="rounded-xl border border-gray-200 p-5 dark:border-gray-800">
          <div className="flex items-start justify-between gap-4">
            <h2 className="text-lg font-semibold">Iteration {sel.index}</h2>
            {sel.index === bestIndex && (
              <span className="rounded bg-blue-600 px-2 py-0.5 text-xs font-semibold text-white">Chosen</span>
            )}
          </div>

          {sel.plot_png && (
            <div className="mt-3">
              <img
                src={`data:image/png;base64,${sel.plot_png}`}
                alt="Selected iteration chart"
                className="w-full rounded-md border border-gray-100 dark:border-gray-800"
              />
            </div>
          )}

          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div>
              <div className="font-medium">Score (max F)</div>
              <div>{sel.score ?? "—"}</div>
            </div>
            <div>
              <div className="font-medium">Artificial break</div>
              <div>{String(sel.artificial_break)}</div>
            </div>
            <div>
              <div className="font-medium">Artificial slope</div>
              <div>{sel.artificial_slope ?? "—"}</div>
            </div>
            {sel.comment && (
              <div className="sm:col-span-2">
                <div className="font-medium">Comment</div>
                <div>{sel.comment}</div>
              </div>
            )}
          </div>

          {/* Codes */}
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div>
              <div className="font-medium">ICD-9</div>
              <div className="text-xs break-words">
                {sel.hypothesis?.icd9_codes?.length
                  ? sel.hypothesis.icd9_codes.join(", ")
                  : "—"}
              </div>
            </div>
            <div>
              <div className="font-medium">ICD-10</div>
              <div className="text-xs break-words">
                {sel.hypothesis?.icd10_codes?.length
                  ? sel.hypothesis.icd10_codes.join(", ")
                  : "—"}
              </div>
            </div>
          </div>

          {/* Table preview */}
          {df && (
            <div className="mt-5 overflow-auto">
              <table className="min-w-full text-xs">
                <thead>
                  <tr>
                    {df.columns.map((c) => (
                      <th key={c} className="border-b border-gray-200 dark:border-gray-800 px-2 py-1 text-left">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {df.rows.slice(0, 12).map((row, i) => (
                    <tr key={i} className="border-b border-gray-100 dark:border-gray-900/50">
                      {df.columns.map((c) => (
                        <td key={c} className="px-2 py-1">{String(row[c] ?? "")}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="mt-2 text-[11px] text-gray-500">
                Showing first 12 rows{df.truncated ? " (truncated)" : ""}.
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}