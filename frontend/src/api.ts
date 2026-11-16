import type { AnalysisResponse, Example, Health, LogDocument } from "./types";

export async function checked(response: Response): Promise<Response> {
  if (!response.ok) {
    let message = `Request failed (${response.status}). Please try again.`;
    try {
      const body = await response.json();
      if (typeof body?.error?.message === "string")
        message = body.error.message;
    } catch {
      /* An upstream proxy may return HTML. */
    }
    throw new Error(message);
  }
  return response;
}

export async function upload<T>(
  path: string,
  file: File,
  signal: AbortSignal,
  accessCode?: string,
): Promise<T> {
  const body = new FormData();
  body.append("file", file);
  const response = await checked(
    await fetch(`/api/${path}`, {
      method: "POST",
      body,
      signal,
      headers: accessCode ? { Authorization: `Bearer ${accessCode}` } : undefined,
    }),
  );
  return response.json() as Promise<T>;
}

export const preview = (file: File, signal: AbortSignal) =>
  upload<LogDocument>("preview", file, signal);
export const analyze = (file: File, signal: AbortSignal, accessCode?: string) =>
  upload<AnalysisResponse>("analyze", file, signal, accessCode);
export async function getSavedReport(id: string, signal: AbortSignal): Promise<AnalysisResponse> {
  return (await checked(await fetch(`/api/examples/${encodeURIComponent(id)}/report`, { signal }))).json();
}
export async function getExamples(): Promise<Example[]> {
  return (await checked(await fetch("/api/examples"))).json();
}
export async function getHealth(): Promise<Health> {
  return (await checked(await fetch("/api/health"))).json();
}
