"use client";

type DataFrameLike = {
  __type__: "dataframe";
  columns: string[];
  rows: Array<Record<string, any>>;
  truncated?: boolean;
};

function isDataFrameLike(x: any): x is DataFrameLike {
  return !!x && x.__type__ === "dataframe" && Array.isArray(x.columns) && Array.isArray(x.rows);
}

export type BestResult = {
  hypothesis?: {
    name?: string;
    icd9_codes?: string[];
    icd10_codes?: string[];
  };
  score?: number | string;
  artificial_break?: boolean;
  artificial_slope?: number | string | null;
  comment?: string;
  timeseries?: DataFrameLike | null;
  rolling_col?: string;
  break_analysis?: any; // summarized object from process.py
  plot_png?: string | null; // base64 (no prefix)
};

export default function ResultsView({ data }: { data: BestResult }) {
  const hyp = data?.hypothesis ?? {};
  const icd9 = hyp.icd9_codes ?? [];
  const icd10 = hyp.icd10_codes ?? [];

  const df = isDataFrameLike(data?.timeseries) ? data!.timeseries : null;

  return (
    <section className="mx-auto max-w-3xl flex flex-col gap-6">
      {/* Summary */}
      <div className="rounded-xl border border-gray-200 p-5 dark:border-gray-800">
        <h2 className="text-lg font-semibold mb-2">Chosen Result</h2>
        <div className="text-sm space-y-1">
          <div>
            <span className="font-medium">Hypothesis:</span> {hyp?.name ?? "—"}
          </div>
          <div>
            <span className="font-medium">Score (max F):</span> {data?.score ?? "—"}
          </div>
          <div>
            <span className="font-medium">Artificial break:</span>{" "}
            {data?.artificial_break !== undefined ? String(data.artificial_break) : "—"}
          </div>
          <div>
            <span className="font-medium">Artificial slope:</span>{" "}
            {data?.artificial_slope ?? "—"}
          </div>
          {data?.comment && (
            <div className="pt-2">
              <span className="font-medium">Comment:</span> {data.comment}
            </div>
          )}
        </div>
      </div>

      {/* Chart */}
      {data?.plot_png && (
        <div className="rounded-xl border border-gray-200 p-5 dark:border-gray-800">
          <h3 className="font-semibold mb-2">Rolling Count (Chart)</h3>
          <img
            src={`data:image/png;base64,${data.plot_png}`}
            alt="Timeseries chart"
            className="w-full rounded-md border border-gray-100 dark:border-gray-800"
          />
        </div>
      )}

      {/* Codes */}
      <div className="rounded-xl border border-gray-200 p-5 dark:border-gray-800">
        <h3 className="font-semibold mb-2">Code Sets</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <div className="font-medium">ICD-9 ({icd9.length})</div>
            <div className="text-xs break-words">
              {icd9.length ? icd9.join(", ") : "—"}
            </div>
          </div>
          <div>
            <div className="font-medium">ICD-10 ({icd10.length})</div>
            <div className="text-xs break-words">
              {icd10.length ? icd10.join(", ") : "—"}
            </div>
          </div>
        </div>
      </div>

      {/* Timeseries preview table */}
      {df && (
        <div className="rounded-xl border border-gray-200 p-5 dark:border-gray-800">
          <h3 className="font-semibold mb-2">Timeseries (preview)</h3>
          <div className="overflow-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr>
                  {df.columns.map((c) => (
                    <th
                      key={c}
                      className="border-b border-gray-200 dark:border-gray-800 px-2 py-1 text-left"
                    >
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {df.rows.slice(0, 12).map((row, i) => (
                  <tr
                    key={i}
                    className="border-b border-gray-100 dark:border-gray-900/50"
                  >
                    {df.columns.map((c) => (
                      <td key={c} className="px-2 py-1">
                        {String(row[c] ?? "")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-2 text-[11px] text-gray-500">
            Showing first 12 rows{df.truncated ? " (truncated)" : ""}.
          </div>
        </div>
      )}
    </section>
  );
}