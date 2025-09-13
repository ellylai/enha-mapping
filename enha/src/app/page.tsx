"use client";
import { useState } from "react";
import TextBox from "@/components/TextBox";
import Loading from "@/components/Loading";

type BestResult = any;

function ResultsView({ data }: { data: BestResult }) {
  // Expecting structure like:
  // {
  //   hypothesis: { name, icd9_codes: [...], icd10_codes: [...] },
  //   score: number,
  //   artificial_break: boolean,
  //   artificial_slope: number,
  //   comment: string,
  //   timeseries: { __type__: "dataframe", columns: string[], rows: Array<Record<string, any>> }
  //   break_analysis: {...}
  // }

  const hyp = data?.hypothesis ?? {};
  const icd9 = hyp?.icd9_codes ?? [];
  const icd10 = hyp?.icd10_codes ?? [];

  return (
    <section className="mx-auto max-w-3xl flex flex-col gap-6">
      <div className="rounded-xl border border-gray-200 p-5 dark:border-gray-800">
        <h2 className="text-lg font-semibold mb-2">Best Hypothesis</h2>
        <div className="text-sm">
          <div><span className="font-medium">Name:</span> {hyp?.name ?? "—"}</div>
          <div><span className="font-medium">Score (max F):</span> {data?.score ?? "—"}</div>
          <div><span className="font-medium">Artificial break:</span> {String(data?.artificial_break)}</div>
          <div><span className="font-medium">Artificial slope:</span> {data?.artificial_slope ?? "—"}</div>
          <div className="mt-2"><span className="font-medium">Comment:</span> {data?.comment ?? "—"}</div>

          <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <div className="font-medium">ICD-9 ({icd9.length})</div>
              <div className="text-xs break-words">{Array.isArray(icd9) ? icd9.join(", ") : "—"}</div>
            </div>
            <div>
              <div className="font-medium">ICD-10 ({icd10.length})</div>
              <div className="text-xs break-words">{Array.isArray(icd10) ? icd10.join(", ") : "—"}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Tiny preview of timeseries (first 10 rows) if present */}
      {data?.timeseries?.__type__ === "dataframe" && (
        <div className="rounded-xl border border-gray-200 p-5 dark:border-gray-800">
          <h3 className="font-semibold mb-2">Timeseries (preview)</h3>
          <div className="overflow-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr>
                  {data.timeseries.columns.map((c: string) => (
                    <th key={c} className="border-b border-gray-200 dark:border-gray-800 px-2 py-1 text-left">{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.timeseries.rows.slice(0, 10).map((row: any, i: number) => (
                  <tr key={i} className="border-b border-gray-100 dark:border-gray-900/50">
                    {data.timeseries.columns.map((c: string) => (
                      <td key={c} className="px-2 py-1">{String(row[c] ?? "")}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-2 text-[11px] text-gray-500">Showing first 10 rows.</div>
        </div>
      )}
    </section>
  );
}

export default function Home() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<BestResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // When user submits, flip to loading. (You can kick off your async work here later.)
  const handleSubmit = async (v: string) => {
    setLoading(true);
    setData(null);
    setLoading(true);

    try {
      const res = await fetch("/api/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: v }),
      });
      const json = await res.json();
      if (!res.ok || !json?.ok) {
        throw new Error(json?.error || "Processing failed");
      }
      setData(json.data);
    } catch (e: any) {
      setError(e?.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  // ⛔ While loading, render ONLY the loading screen (nothing else in the DOM).
  if (loading) {
    return <Loading label="Mapping codes and fetching data…" />;
  }

  return (
    <div 
      className="
        font-sans 
        grid grid-rows-[20px_1fr_20px] 
        items-center justify-items-center 
        min-h-screen p-8 pb-20 gap-16 sm:p-20">
      <main 
        className="
        row-start-2 justify-self-stretch w-full 
        max-w-3xl mx-auto flex flex-col gap-8 items-stretch">
      
        {!data && !error && (
          <>
            <ol className="font-mono list-inside list-decimal text-sm/6 text-center sm:text-left">
                <li className="mb-2 tracking-[-.01em]">
                  Give us your prompt, e.g.{" "}
                  <code className="bg-black/5 dark:bg-white/10 font-mono font-semibold px-1 py-0.5 rounded">
                    ICD codes for cocaine addiction
                  </code>
                </li>
                <li className="tracking-[-.01em]">Press Enter to submit.</li>
              </ol>
          </>
        )}

        {error && (
          <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-red-800 dark:border-red-800 dark:bg-red-950/30 dark:text-red-200">
            {error}
          </div>
        )}

        {data && <ResultsView data={data} />}

        <TextBox
          value={input}
          onChange={setInput}
          onSubmit={handleSubmit}
          placeholder="ICD codes for cocaine addiction."
        />

      </main>
    </div>
  );
}
