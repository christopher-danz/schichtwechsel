import type { Patient, VitalReading } from "../types";

interface Props {
  patient: Patient;
  children?: React.ReactNode; // slot for recording section (Phase C)
}

function latestVitals(vitals: VitalReading[]): Map<string, VitalReading> {
  const latest = new Map<string, VitalReading>();
  for (const v of vitals) {
    const existing = latest.get(v.parameter);
    if (!existing || v.recorded_at > existing.recorded_at) {
      latest.set(v.parameter, v);
    }
  }
  return latest;
}

function formatVitalTime(isoStr: string): string {
  const d = new Date(isoStr);
  return d.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" });
}

const VITAL_LABELS: Record<string, string> = {
  temperature: "Temp.",
  oxygen_saturation: "SpO₂",
  heart_rate: "HF",
  blood_pressure: "RR",
  respiratory_rate: "AF",
  pain_score: "Schmerz",
};

const VITAL_UNITS: Record<string, string> = {
  temperature: "°C",
  oxygen_saturation: "%",
  heart_rate: "/min",
  blood_pressure: "mmHg",
  respiratory_rate: "/min",
  pain_score: "/10",
};

function vitalColorClass(p: VitalReading): string {
  if (p.parameter === "temperature" && p.value > 37.8) return "text-amber-600 font-semibold";
  if (p.parameter === "oxygen_saturation" && p.value < 92) return "text-red-600 font-semibold";
  return "text-slate-800";
}

export default function PatientDetail({ patient, children }: Props) {
  const latest = latestVitals(patient.recent_vitals);
  const latestTemp = latest.get("temperature");
  const displayedParams = ["temperature", "oxygen_saturation", "heart_rate"];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
      {/* Header */}
      <div className="bg-blue-900 text-white px-5 py-4">
        <div className="flex items-baseline gap-2">
          <span className="text-lg font-semibold">{patient.demographics.name}</span>
          <span className="text-blue-300 text-sm">· Bett {patient.bed}</span>
        </div>
        <p className="text-blue-200 text-sm mt-0.5">{patient.main_diagnosis}</p>
        <p className="text-blue-300 text-xs mt-0.5">
          {patient.demographics.age} Jahre ·{" "}
          {patient.demographics.sex === "F" ? "weiblich" : patient.demographics.sex === "M" ? "männlich" : "divers"}
        </p>
      </div>

      <div className="p-5 space-y-5">
        {/* Vitals */}
        {latest.size > 0 && (
          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Letzte Vitalwerte
              {latestTemp && (
                <span className="ml-2 normal-case font-normal text-slate-400">
                  (zuletzt {formatVitalTime(latestTemp.recorded_at)} Uhr)
                </span>
              )}
            </h3>
            <div className="flex gap-3 flex-wrap">
              {displayedParams.map((param) => {
                const v = latest.get(param);
                if (!v) return null;
                return (
                  <div
                    key={param}
                    className="bg-slate-50 rounded-lg px-3 py-2 text-center min-w-[72px]"
                  >
                    <p className={`text-lg leading-tight ${vitalColorClass(v)}`}>
                      {v.value}
                    </p>
                    <p className="text-xs text-slate-400">
                      {VITAL_LABELS[param]} {VITAL_UNITS[param] ?? v.unit}
                    </p>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* Allergies */}
        {patient.allergies.length > 0 && (
          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-red-500 mb-2">
              Allergien
            </h3>
            <ul className="space-y-1">
              {patient.allergies.map((a, i) => (
                <li
                  key={i}
                  className="flex items-center gap-2 text-sm bg-red-50 rounded-lg px-3 py-1.5"
                >
                  <span className="w-2 h-2 rounded-full bg-red-500 shrink-0" />
                  <span className="font-medium text-red-800">{a.substance}</span>
                  {a.reaction && (
                    <span className="text-red-600 text-xs">({a.reaction})</span>
                  )}
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Medications */}
        {patient.medications.length > 0 && (
          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Aktive Medikamente
            </h3>
            <ul className="space-y-1">
              {patient.medications
                .filter((m) => m.status === "active")
                .map((m, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-1.5 shrink-0" />
                    <span className="text-slate-700">
                      {m.name}
                      {m.dose && <span className="text-slate-500"> {m.dose}</span>}
                      {m.frequency && (
                        <span className="text-slate-400 text-xs"> · {m.frequency}</span>
                      )}
                    </span>
                  </li>
                ))}
            </ul>
          </section>
        )}

        {/* Open diagnostics */}
        {patient.open_diagnostics.length > 0 && (
          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Ausstehende Diagnostik
            </h3>
            <ul className="space-y-1">
              {patient.open_diagnostics.map((d, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-slate-600">
                  <span
                    className={[
                      "px-1.5 py-0.5 rounded text-xs font-medium",
                      d.status === "in_progress"
                        ? "bg-amber-100 text-amber-700"
                        : "bg-slate-100 text-slate-500",
                    ].join(" ")}
                  >
                    {d.status === "in_progress" ? "läuft" : "ausstehend"}
                  </span>
                  {d.name}
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Slot for recording section injected by Phase C */}
        {children}
      </div>
    </div>
  );
}
