import { useState } from "react";
import { postConfirmMissing, postSign } from "../api/handoverCards";
import type { CompletenessScore, Inconsistency, SignResponse, StructureResponse } from "../types";
import type { ActionItem, SBARStructure } from "../types/sbar";

interface Props {
  data: StructureResponse;
  onSigned?: () => void;
}

const VITAL_LABELS: Record<string, string> = {
  temperature: "Temperatur",
  oxygen_saturation: "SpO₂",
  heart_rate: "Herzfrequenz",
  blood_pressure: "Blutdruck",
  respiratory_rate: "Atemfrequenz",
  pain_score: "Schmerz",
};

const QUALIFIER_LABELS: Record<string, string> = {
  stable: "stabil",
  improving: "besser",
  worsening: "schlechter",
  unchanged: "unverändert",
  abnormal: "auffällig",
};

const PRIORITY_LABEL: Record<ActionItem["priority"], string> = {
  routine: "Routine",
  urgent: "Dringend",
  critical: "Kritisch",
};

const PRIORITY_CLASS: Record<ActionItem["priority"], string> = {
  routine: "bg-slate-100 text-slate-600",
  urgent: "bg-amber-100 text-amber-700",
  critical: "bg-red-100 text-red-700",
};

const MISSING_LABELS: Record<string, string> = {
  allergies_not_mentioned: "Allergien nicht erwähnt",
  situation_empty: "Situation fehlt",
  no_recommendation: "Keine Empfehlung",
  no_vital_signs: "Keine Vitalwerte erwähnt",
  no_medications: "Keine Medikamente erwähnt",
  open_diagnostics_not_addressed: "Ausstehende Diagnostik nicht adressiert",
};

function SBARHeading({ title }: { title: string }) {
  return (
    <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
      {title}
    </p>
  );
}

function SBARSituation({ sbar }: { sbar: SBARStructure }) {
  return (
    <section className="bg-blue-50 rounded-lg px-4 py-3">
      <SBARHeading title="Situation" />
      <p className="text-sm text-slate-800 leading-relaxed">{sbar.situation}</p>
    </section>
  );
}

function SBARBackground({ sbar }: { sbar: SBARStructure }) {
  const bg = sbar.background;
  const hasContent =
    bg.admission_reason ||
    bg.relevant_history.length > 0 ||
    bg.current_medications.length > 0 ||
    bg.allergies_mentioned.length > 0 ||
    bg.allergies_explicitly_none;

  if (!hasContent) return null;

  return (
    <section>
      <SBARHeading title="Hintergrund" />
      <div className="space-y-1 text-sm text-slate-700">
        {bg.admission_reason && (
          <p>
            <span className="text-slate-400 text-xs">Aufnahmegrund:</span>{" "}
            {bg.admission_reason}
          </p>
        )}
        {bg.current_medications.length > 0 && (
          <p>
            <span className="text-slate-400 text-xs">Medikamente:</span>{" "}
            {bg.current_medications.join(", ")}
          </p>
        )}
        {bg.allergies_explicitly_none && (
          <p className="text-green-700 text-xs font-medium">
            Keine bekannten Allergien (explizit bestätigt)
          </p>
        )}
        {bg.allergies_mentioned.length > 0 && (
          <p>
            <span className="text-slate-400 text-xs">Allergien:</span>{" "}
            {bg.allergies_mentioned.join(", ")}
          </p>
        )}
        {bg.relevant_history.length > 0 && (
          <p>
            <span className="text-slate-400 text-xs">Vorgeschichte:</span>{" "}
            {bg.relevant_history.join(", ")}
          </p>
        )}
      </div>
    </section>
  );
}

function SBARAssessment({ sbar }: { sbar: SBARStructure }) {
  const a = sbar.assessment;
  const hasContent =
    a.current_status ||
    a.vital_mentions.length > 0 ||
    a.complications.length > 0 ||
    a.pending_diagnostics.length > 0;

  if (!hasContent) return null;

  return (
    <section>
      <SBARHeading title="Beurteilung" />
      <div className="space-y-1.5 text-sm text-slate-700">
        {a.current_status && <p className="leading-relaxed">{a.current_status}</p>}
        {a.vital_mentions.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-1">
            {a.vital_mentions.map((v, i) => (
              <span
                key={i}
                className="bg-slate-50 rounded-md px-2 py-0.5 text-xs text-slate-600 border border-slate-200"
              >
                {VITAL_LABELS[v.parameter] ?? v.parameter}
                {v.qualifier && ` (${QUALIFIER_LABELS[v.qualifier] ?? v.qualifier})`}
              </span>
            ))}
          </div>
        )}
        {a.complications.length > 0 && (
          <p className="text-red-700">
            <span className="text-xs">Komplikationen:</span>{" "}
            {a.complications.join(", ")}
          </p>
        )}
        {a.pending_diagnostics.length > 0 && (
          <p>
            <span className="text-slate-400 text-xs">Ausstehend:</span>{" "}
            {a.pending_diagnostics.join(", ")}
          </p>
        )}
      </div>
    </section>
  );
}

function SBARRecommendation({ sbar }: { sbar: SBARStructure }) {
  if (sbar.recommendation.length === 0) return null;

  return (
    <section>
      <SBARHeading title="Empfehlung" />
      <ul className="space-y-1">
        {sbar.recommendation.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-sm">
            <span
              className={`shrink-0 text-xs px-1.5 py-0.5 rounded font-medium mt-0.5 ${PRIORITY_CLASS[item.priority]}`}
            >
              {PRIORITY_LABEL[item.priority]}
            </span>
            <span className="text-slate-700 leading-snug">
              {item.action}
              {item.timing && (
                <span className="text-slate-400 ml-1 text-xs">· {item.timing}</span>
              )}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function InconsistencyBanner({ items }: { items: Inconsistency[] }) {
  if (items.length === 0) return null;

  const rowClass = (sev: Inconsistency["severity"]) => {
    if (sev === "CRITICAL") return "bg-red-50 border-red-300 text-red-800";
    if (sev === "WARN") return "bg-amber-50 border-amber-300 text-amber-800";
    return "bg-blue-50 border-blue-200 text-blue-700";
  };

  return (
    <div className="space-y-2">
      {items.map((item, i) => (
        <div
          key={i}
          className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-sm ${rowClass(item.severity)}`}
        >
          <span className="shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center text-xs font-bold border-current mt-0.5">
            !
          </span>
          <p className="leading-snug">{item.message}</p>
        </div>
      ))}
    </div>
  );
}

interface CompletenessBarProps {
  completeness: CompletenessScore;
  cardId: string;
  onConfirmed: (updated: CompletenessScore) => void;
}

function CompletenessBar({ completeness, cardId, onConfirmed }: CompletenessBarProps) {
  const [confirming, setConfirming] = useState(false);
  const [confirmError, setConfirmError] = useState<string | null>(null);

  const pct = Math.round(completeness.score * 100);
  const barColor =
    pct >= 90 ? "bg-green-500" : pct >= 70 ? "bg-amber-400" : "bg-red-400";

  const showAllergyConfirm = completeness.missing_items.includes("allergies_not_mentioned");

  async function handleConfirmAllergies() {
    setConfirming(true);
    setConfirmError(null);
    try {
      const result = await postConfirmMissing(cardId, "allergies", "explicitly_none");
      onConfirmed(result.completeness);
    } catch (err) {
      setConfirmError(err instanceof Error ? err.message : "Fehler");
    } finally {
      setConfirming(false);
    }
  }

  return (
    <div className="space-y-2">
      <div>
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-slate-500">Vollständigkeit</span>
          <span className="text-sm font-semibold text-slate-700">{pct}%</span>
        </div>
        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${barColor}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {completeness.missing_items.length > 0 && (
        <ul className="space-y-0.5">
          {completeness.missing_items.map((item, i) => (
            <li key={i} className="text-xs text-slate-400 flex items-center gap-1">
              <span className="w-1 h-1 rounded-full bg-slate-300 shrink-0" />
              {MISSING_LABELS[item] ?? item}
            </li>
          ))}
        </ul>
      )}

      {showAllergyConfirm && (
        <div>
          <button
            onClick={() => void handleConfirmAllergies()}
            disabled={confirming}
            className="flex items-center gap-2 text-sm font-medium text-amber-700 bg-amber-50 border border-amber-200 hover:bg-amber-100 disabled:opacity-50 px-3 py-1.5 rounded-lg transition-colors"
          >
            {confirming ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-amber-600 border-t-transparent rounded-full animate-spin" />
                Wird gespeichert…
              </>
            ) : (
              "Keine bekannten Allergien bestätigen"
            )}
          </button>
          {confirmError && (
            <p className="text-xs text-red-600 mt-1">{confirmError}</p>
          )}
        </div>
      )}
    </div>
  );
}

interface SignSectionProps {
  cardId: string;
  onSigned?: () => void;
}

function SignSection({ cardId, onSigned }: SignSectionProps) {
  const [signing, setSigning] = useState(false);
  const [signResult, setSignResult] = useState<SignResponse | null>(null);
  const [signError, setSignError] = useState<string | null>(null);

  async function handleSign() {
    setSigning(true);
    setSignError(null);
    try {
      const result = await postSign(cardId, "Dr. Müller");
      setSignResult(result);
      onSigned?.();
    } catch (err) {
      setSignError(err instanceof Error ? err.message : "Fehler beim Signieren");
    } finally {
      setSigning(false);
    }
  }

  if (signResult) {
    const signedAt = new Date(signResult.signed_at).toLocaleString("de-DE", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
    return (
      <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3">
        <div className="flex items-center gap-2 text-green-800 font-semibold text-sm mb-1">
          <span className="w-5 h-5 rounded-full bg-green-600 text-white flex items-center justify-center text-xs">
            ✓
          </span>
          Übergabe abgeschlossen
        </div>
        <p className="text-xs text-green-700">
          Dr. Müller · {signedAt} Uhr
        </p>
        <p className="text-xs text-green-600 mt-0.5 font-mono truncate">
          {signResult.audit_hash}
        </p>
      </div>
    );
  }

  return (
    <div>
      <button
        onClick={() => void handleSign()}
        disabled={signing}
        className="w-full flex items-center justify-center gap-2 bg-blue-900 hover:bg-blue-800 disabled:opacity-50 text-white text-sm font-semibold px-4 py-3 rounded-xl transition-colors"
      >
        {signing ? (
          <>
            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Übergabe wird signiert…
          </>
        ) : (
          "Übergabe abschließen"
        )}
      </button>
      {signError && (
        <p className="text-xs text-red-600 mt-1 text-center">{signError}</p>
      )}
    </div>
  );
}

export default function SBARCard({ data, onSigned }: Props) {
  const [completeness, setCompleteness] = useState<CompletenessScore>(data.completeness);

  return (
    <div className="border-t border-slate-100 pt-4 space-y-4">
      <InconsistencyBanner items={data.inconsistencies} />

      <SBARSituation sbar={data.sbar} />
      <SBARBackground sbar={data.sbar} />
      <SBARAssessment sbar={data.sbar} />
      <SBARRecommendation sbar={data.sbar} />

      <CompletenessBar
        completeness={completeness}
        cardId={data.card_id}
        onConfirmed={setCompleteness}
      />

      <SignSection cardId={data.card_id} onSigned={onSigned} />
    </div>
  );
}
