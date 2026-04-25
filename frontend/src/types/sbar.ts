import type { VitalParameter } from "./patient";

export type VitalQualifier =
  | "stable"
  | "improving"
  | "worsening"
  | "unchanged"
  | "abnormal";

export interface BackgroundFields {
  admission_reason?: string;
  admission_date?: string;
  relevant_history: string[];
  current_medications: string[];
  allergies_mentioned: string[];
  allergies_explicitly_none: boolean;
}

export interface VitalMention {
  parameter: VitalParameter;
  value?: string;
  qualifier?: VitalQualifier;
}

export interface AssessmentFields {
  current_status?: string;
  vital_mentions: VitalMention[];
  complications: string[];
  pending_diagnostics: string[];
}

export interface ActionItem {
  action: string;
  timing?: string;
  priority: "routine" | "urgent" | "critical";
}

export interface SBARStructure {
  situation: string;
  background: BackgroundFields;
  assessment: AssessmentFields;
  recommendation: ActionItem[];
}
