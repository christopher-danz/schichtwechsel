import type { PatientSummary } from "../types";

export type PatientStatus = "pending" | "in-progress" | "signed";

interface Props {
  patients: PatientSummary[];
  selectedId: string | null;
  statuses: Record<string, PatientStatus>;
  onSelect: (id: string) => void;
}

function StatusDot({ status }: { status: PatientStatus }) {
  if (status === "signed") {
    return (
      <span className="w-5 h-5 rounded-full bg-green-500 text-white flex items-center justify-center text-[10px] font-bold shrink-0">
        ✓
      </span>
    );
  }
  if (status === "in-progress") {
    return <span className="w-3 h-3 rounded-full bg-amber-400 animate-pulse shrink-0 mt-1" />;
  }
  return <span className="w-3 h-3 rounded-full bg-slate-200 shrink-0 mt-1" />;
}

export default function PatientSidebar({
  patients,
  selectedId,
  statuses,
  onSelect,
}: Props) {
  const signedCount = patients.filter((p) => statuses[p.patient_id] === "signed").length;

  return (
    <aside className="w-72 flex-shrink-0 bg-white border-r border-slate-200 flex flex-col overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-100 flex-shrink-0">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Aktuelle Schicht
        </p>
        <div className="flex items-center justify-between mt-1">
          <p className="text-xs text-slate-400">
            {signedCount} / {patients.length} übergeben
          </p>
          {signedCount === patients.length && patients.length > 0 && (
            <span className="text-xs font-medium text-green-600">Vollständig</span>
          )}
        </div>
        {patients.length > 0 && (
          <div className="mt-2 h-1 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-green-500 rounded-full transition-all duration-500"
              style={{ width: `${(signedCount / patients.length) * 100}%` }}
            />
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto divide-y divide-slate-50">
        {patients.map((p) => {
          const selected = p.patient_id === selectedId;
          const status = statuses[p.patient_id] ?? "pending";

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
                  "w-9 h-9 rounded-lg flex items-center justify-center text-xs font-bold shrink-0",
                  selected ? "bg-blue-700 text-white" : "bg-slate-100 text-slate-600",
                ].join(" ")}
              >
                {p.bed}
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-800 truncate">
                  {p.demographics.name}
                </p>
                <p className="text-xs text-slate-400 truncate">{p.main_diagnosis}</p>
              </div>

              <div className="flex flex-col items-center gap-1 shrink-0">
                <StatusDot status={status} />
                <span className="text-[10px] text-slate-300">{p.demographics.age}J.</span>
              </div>
            </button>
          );
        })}
      </div>
    </aside>
  );
}
