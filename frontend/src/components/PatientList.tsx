import type { PatientSummary } from "../types";

interface Props {
  patients: PatientSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export default function PatientList({ patients, selectedId, onSelect }: Props) {
  if (patients.length === 0) {
    return (
      <div className="text-sm text-slate-400 text-center py-6">
        Keine Patienten geladen
      </div>
    );
  }

  return (
    <div className="divide-y divide-slate-100">
      {patients.map((p) => {
        const selected = p.patient_id === selectedId;
        return (
          <button
            key={p.patient_id}
            onClick={() => onSelect(p.patient_id)}
            className={[
              "w-full text-left px-4 py-3 flex items-center gap-3 transition-colors",
              selected
                ? "bg-blue-50 border-l-4 border-blue-700"
                : "hover:bg-slate-50 border-l-4 border-transparent",
            ].join(" ")}
          >
            <div
              className={[
                "w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold shrink-0",
                selected ? "bg-blue-700 text-white" : "bg-slate-100 text-slate-600",
              ].join(" ")}
            >
              {p.bed}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-slate-800 truncate">
                {p.demographics.name}
              </p>
              <p className="text-xs text-slate-500 truncate">{p.main_diagnosis}</p>
            </div>
            <span className="text-xs text-slate-400 shrink-0">
              {p.demographics.age} J.
            </span>
          </button>
        );
      })}
    </div>
  );
}
