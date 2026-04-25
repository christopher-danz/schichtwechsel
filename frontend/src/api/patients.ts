import type { Patient, PatientSummary } from "../types";

export async function fetchPatients(): Promise<PatientSummary[]> {
  const res = await fetch("/api/patients");
  if (!res.ok) throw new Error(`GET /api/patients failed: ${res.status}`);
  const data = (await res.json()) as { patients: PatientSummary[] };
  return data.patients;
}

export async function fetchPatient(patientId: string): Promise<Patient> {
  const res = await fetch(`/api/patients/${patientId}`);
  if (!res.ok) throw new Error(`GET /api/patients/${patientId} failed: ${res.status}`);
  return res.json() as Promise<Patient>;
}
