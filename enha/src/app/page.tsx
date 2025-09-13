"use client";

import { useState } from "react";
import TextBox from "@/components/TextBox";
import Loading from "@/components/Loading";
import ResultsView, { type BestResult } from "@/components/ResultsView";

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
      if (!res.ok || !json?.ok) throw new Error(json?.error || "Processing failed");
      setData(json.data as BestResult);
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
      
        {!data && !error && !loading && (
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
            <TextBox
              value={input}
              onChange={setInput}
              onSubmit={handleSubmit}
              placeholder="ICD codes for cocaine addiction."
            />
          </>
        )}

        {loading && <Loading label="Analyzing hypothesis and refining..." />}

        {error && (
          <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-red-800 dark:border-red-800 dark:bg-red-950/30 dark:text-red-200">
            {error}
          </div>
        )}

        {data && <ResultsView data={data} />}

      </main>
    </div>
  );
}
