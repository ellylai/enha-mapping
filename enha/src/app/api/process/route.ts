// enha/src/app/api/process/route.ts
import { NextRequest, NextResponse } from "next/server";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";

export const runtime = "nodejs";
const execFileP = promisify(execFile);

export async function POST(req: NextRequest) {
  try {
    const { prompt } = await req.json();
    if (typeof prompt !== "string" || !prompt.trim()) {
      return NextResponse.json({ ok: false, error: "Invalid prompt" }, { status: 400 });
    }

    const scriptPath = path.join(process.cwd(), "process.py");      // enha/process.py
    const repoRoot   = path.resolve(process.cwd(), "..");            // enha-mapping/

    const { stdout } = await execFileP(
      process.platform === "win32" ? "python" : "python3",
      [scriptPath, prompt],
      {
        cwd: repoRoot,                    // 👈 run with CWD = repo root
        timeout: 120_000,
        maxBuffer: 50 * 1024 * 1024,
        // (optional) mute warnings:
        // env: { ...process.env, PYTHONWARNINGS: "ignore" },
      }
    );

    // If you used my tolerant JSON parser earlier, keep that. Otherwise:
    const parsed = JSON.parse(stdout);
    return NextResponse.json(parsed, { status: 200 });
  } catch (err: any) {
    const msg =
      err?.stderr?.toString?.() ||
      err?.stdout?.toString?.() ||
      err?.message ||
      "Python execution failed";
    return NextResponse.json({ ok: false, error: msg }, { status: 500 });
  }
}