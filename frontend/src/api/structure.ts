import type { StructureResponse } from "../types";

export async function postStructure(
  transcript: string,
  patientId: string
): Promise<StructureResponse> {
  const res = await fetch("/api/structure", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transcript, patient_id: patientId }),
  });
  if (!res.ok) throw new Error(`POST /api/structure failed: ${res.status}`);
  return res.json() as Promise<StructureResponse>;
}
