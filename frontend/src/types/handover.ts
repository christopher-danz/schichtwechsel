import type { SBARStructure } from "./sbar";

export type InconsistencyType = "VITAL_TREND" | "MED_STATE" | "ALLERGY_COLLISION";
export type InconsistencySeverity = "INFO" | "WARN" | "CRITICAL";

export interface Inconsistency {
  type: InconsistencyType;
  severity: InconsistencySeverity;
  message: string;
  evidence: Record<string, unknown>;
}

export interface CompletenessScore {
  score: number;
  missing_items: string[];
  details: Record<string, boolean>;
}

export interface HandoverCard {
  card_id: string;
  patient_id: string;
  recorded_at: string;
  raw_transcript: string;
  sbar: SBARStructure;
  inconsistencies: Inconsistency[];
  completeness: CompletenessScore;
  signed: boolean;
  signed_at?: string;
  signed_by?: string;
}

export interface TranscribeResponse {
  transcript: string;
  duration_ms: number;
  provider: "gradium" | "whisper-local" | "browser-webspeech";
}

export interface StructureResponse {
  card_id: string;
  sbar: SBARStructure;
  inconsistencies: Inconsistency[];
  completeness: CompletenessScore;
}

export interface ConfirmMissingRequest {
  item: string;
  value: "explicitly_none" | "addressed_separately" | "not_applicable";
}

export interface SignResponse {
  card_id: string;
  signed_at: string;
  audit_hash: string;
}
