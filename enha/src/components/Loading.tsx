"use client";

export default function Loading({ label = "Working on it…" }: { label?: string }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80">
      <div className="flex flex-col items-center gap-4">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-white/30 border-t-white" />
        <span className="text-white text-lg font-medium">{label}</span>
      </div>
    </div>
  );
}