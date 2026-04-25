export async function postTranscribe(blob: Blob): Promise<string> {
  const form = new FormData();
  form.append("audio", blob, "recording.webm");
  const res = await fetch("/api/transcribe", { method: "POST", body: form });
  if (!res.ok) throw new Error(`POST /api/transcribe failed: ${res.status}`);
  const data = (await res.json()) as { transcript: string };
  return data.transcript;
}
