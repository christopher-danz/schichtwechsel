export type VitalParameter =
  | "temperature"
  | "blood_pressure"
  | "heart_rate"
  | "oxygen_saturation"
  | "respiratory_rate"
  | "pain_score";

export interface Allergy {
  substance: string;
  reaction?: string;
  severity: "mild" | "moderate" | "severe";
}

export interface Medication {
  name: string;
  dose?: string;
  frequency?: string;
  route?: string;
  status: "active" | "paused" | "discontinued";
  started_at?: string;
}

export interface VitalReading {
  parameter: VitalParameter;
  value: number;
  unit: string;
  recorded_at: string;
}

export interface OpenDiagnostic {
  name: string;
  ordered_at?: string;
  status: "pending" | "in_progress" | "resulted";
  result?: string;
}

export interface PatientDemographics {
  age: number;
  sex: "M" | "F" | "D";
  name: string;
}

export interface Patient {
  patient_id: string;
  bed: string;
  demographics: PatientDemographics;
  main_diagnosis: string;
  allergies: Allergy[];
  medications: Medication[];
  recent_vitals: VitalReading[];
  open_diagnostics: OpenDiagnostic[];
}

export interface PatientSummary {
  patient_id: string;
  bed: string;
  demographics: PatientDemographics;
  main_diagnosis: string;
}
