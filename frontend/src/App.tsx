import { useEffect, useState } from "react";
import { fetchPatients, fetchPatient } from "./api/patients";
import PatientList from "./components/PatientList";
import PatientDetail from "./components/PatientDetail";
import RecordingSection from "./components/RecordingSection";
import type { Patient, PatientSummary } from "./types";

export default function App() {
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [transcript, setTranscript] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPatients()
      .then(setPatients)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Verbindung fehlgeschlagen")
      )
      .finally(() => setLoadingList(false));
  }, []);

  function handleSelectPatient(id: string) {
    setSelectedId(id);
    setSelectedPatient(null);
    setTranscript(null);
    setLoadingDetail(true);
    fetchPatient(id)
      .then(setSelectedPatient)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Patient konnte nicht geladen werden")
      )
      .finally(() => setLoadingDetail(false));
  }

  const today = new Date().toLocaleDateString("de-DE", {
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });

  return (
    <div className="min-h-screen bg-slate-100">
      {/* Header */}
      <header className="bg-blue-900 text-white px-6 py-3 shadow-md">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-xs font-bold">
              SW
            </div>
            <h1 className="font-semibold tracking-tight">Schichtwechsel</h1>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium">Dr. Müller</p>
            <p className="text-xs text-blue-300">{today}</p>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6 space-y-4">
        {/* Error banner */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Patient list card */}
        <section className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-700">Patienten — aktuelle Schicht</h2>
            <span className="text-xs text-slate-400">{patients.length} Patienten</span>
          </div>

          {loadingList ? (
            <div className="px-4 py-6 text-sm text-slate-400 animate-pulse text-center">
              Lade Patienten…
            </div>
          ) : (
            <PatientList
              patients={patients}
              selectedId={selectedId}
              onSelect={handleSelectPatient}
            />
          )}
        </section>

        {/* Patient detail card */}
        {selectedId && (
          <section>
            {loadingDetail && (
              <div className="bg-white rounded-xl shadow-sm border border-slate-100 px-4 py-8 text-center text-sm text-slate-400 animate-pulse">
                Lade Patientenakte…
              </div>
            )}
            {selectedPatient && (
              <PatientDetail patient={selectedPatient}>
                <RecordingSection
                  patientId={selectedPatient.patient_id}
                  onTranscript={setTranscript}
                />
                {transcript && (
                  <section className="border-t border-slate-100 pt-4">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                      Transkript
                    </h3>
                    <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {transcript}
                    </p>
                  </section>
                )}
              </PatientDetail>
            )}
          </section>
        )}

        {!selectedId && !loadingList && patients.length > 0 && (
          <p className="text-center text-sm text-slate-400 py-4">
            Patienten auswählen, um die Übergabe zu starten
          </p>
        )}
      </main>
    </div>
  );
}
