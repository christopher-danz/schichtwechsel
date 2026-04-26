import { useEffect, useState } from "react";
import { fetchPatients, fetchPatient } from "./api/patients";
import { postStructure } from "./api/structure";
import PatientSidebar from "./components/PatientSidebar";
import type { PatientStatus } from "./components/PatientSidebar";
import PatientDetail from "./components/PatientDetail";
import RecordingSection from "./components/RecordingSection";
import SBARCard from "./components/SBARCard";
import type { Patient, PatientSummary, StructureResponse } from "./types";

export default function App() {
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [transcript, setTranscript] = useState<string | null>(null);
  const [structuring, setStructuring] = useState(false);
  const [sbarData, setSbarData] = useState<StructureResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [patientStatus, setPatientStatus] = useState<Record<string, PatientStatus>>({});

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
    setSbarData(null);
    setError(null);
    setLoadingDetail(true);
    setPatientStatus((prev) => {
      if ((prev[id] ?? "pending") === "pending") {
        return { ...prev, [id]: "in-progress" };
      }
      return prev;
    });
    fetchPatient(id)
      .then(setSelectedPatient)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Patient konnte nicht geladen werden")
      )
      .finally(() => setLoadingDetail(false));
  }

  function handleTranscript(t: string) {
    setTranscript(t);
    setSbarData(null);
  }

  function handleSigned(patientId: string) {
    setPatientStatus((prev) => ({ ...prev, [patientId]: "signed" }));
  }

  function nextPendingPatient(): PatientSummary | null {
    return (
      patients.find((p) => (patientStatus[p.patient_id] ?? "pending") !== "signed") ?? null
    );
  }

  async function handleStructure() {
    if (!transcript || !selectedId) return;
    setStructuring(true);
    setError(null);
    try {
      const data = await postStructure(transcript, selectedId);
      setSbarData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Strukturierung fehlgeschlagen");
    } finally {
      setStructuring(false);
    }
  }

  const today = new Date().toLocaleDateString("de-DE", {
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });

  const allDone =
    patients.length > 0 && patients.every((p) => patientStatus[p.patient_id] === "signed");

  const currentPatientSigned = selectedId !== null && patientStatus[selectedId] === "signed";
  const next = currentPatientSigned ? nextPendingPatient() : null;

  return (
    <div className="h-screen flex flex-col bg-slate-100">
      {/* Header */}
      <header className="bg-blue-900 text-white px-6 py-3 shadow-md flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-xs font-bold">
              SW
            </div>
            <div>
              <h1 className="font-semibold tracking-tight leading-none">Schichtwechsel</h1>
              <p className="text-xs text-blue-300 mt-0.5">Station Innere 3</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium">Dr. Müller</p>
            <p className="text-xs text-blue-300">{today} · 06:00–18:00</p>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        {loadingList ? (
          <aside className="w-72 flex-shrink-0 bg-white border-r border-slate-200 px-4 py-6">
            <div className="animate-pulse space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-14 bg-slate-100 rounded-lg" />
              ))}
            </div>
          </aside>
        ) : (
          <PatientSidebar
            patients={patients}
            selectedId={selectedId}
            statuses={patientStatus}
            onSelect={handleSelectPatient}
          />
        )}

        {/* Main pane */}
        <main className="flex-1 overflow-y-auto p-6 space-y-4">
          {/* Error banner */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* All-done celebration */}
          {allDone && !selectedId && (
            <div className="bg-green-50 border border-green-200 rounded-xl px-6 py-8 text-center">
              <div className="w-12 h-12 rounded-full bg-green-500 text-white flex items-center justify-center text-xl font-bold mx-auto mb-3">
                ✓
              </div>
              <h2 className="text-lg font-semibold text-green-800 mb-1">
                Schichtwechsel abgeschlossen
              </h2>
              <p className="text-sm text-green-600">
                Alle {patients.length} Patienten wurden übergeben.
              </p>
            </div>
          )}

          {/* Empty state */}
          {!selectedId && !allDone && !loadingList && patients.length > 0 && (
            <div className="flex flex-col items-center justify-center h-64 text-center">
              <div className="w-12 h-12 rounded-full bg-slate-200 flex items-center justify-center text-2xl mb-4">
                ←
              </div>
              <p className="text-slate-500 font-medium">Patienten auswählen</p>
              <p className="text-sm text-slate-400 mt-1">
                Wählen Sie einen Patienten aus der Liste, um die Übergabe zu starten.
              </p>
            </div>
          )}

          {/* Detail loading */}
          {selectedId && loadingDetail && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 px-4 py-8 text-center text-sm text-slate-400 animate-pulse">
              Lade Patientenakte…
            </div>
          )}

          {/* Patient detail + recording + SBAR */}
          {selectedPatient && (
            <PatientDetail patient={selectedPatient}>
              <RecordingSection
                patientId={selectedPatient.patient_id}
                onTranscript={handleTranscript}
              />

              {transcript && (
                <section className="border-t border-slate-100 pt-4 space-y-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Transkript
                  </h3>
                  <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                    {transcript}
                  </p>
                  {!sbarData && (
                    <button
                      onClick={() => void handleStructure()}
                      disabled={structuring}
                      className="flex items-center gap-2 bg-blue-700 hover:bg-blue-800 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
                    >
                      {structuring ? (
                        <>
                          <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          SBAR wird erstellt…
                        </>
                      ) : (
                        "SBAR erstellen"
                      )}
                    </button>
                  )}
                </section>
              )}

              {sbarData && (
                <SBARCard
                  data={sbarData}
                  onSigned={() => handleSigned(selectedPatient.patient_id)}
                />
              )}
            </PatientDetail>
          )}

          {/* Post-sign navigation */}
          {currentPatientSigned && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 px-5 py-4">
              {next ? (
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-700">Nächster Patient</p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Bett {next.bed} · {next.demographics.name}
                    </p>
                  </div>
                  <button
                    onClick={() => handleSelectPatient(next.patient_id)}
                    className="flex items-center gap-2 bg-blue-700 hover:bg-blue-800 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
                  >
                    Nächster Patient →
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center text-sm font-bold shrink-0">
                    ✓
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-green-800">
                      Schichtwechsel abgeschlossen
                    </p>
                    <p className="text-xs text-green-600 mt-0.5">
                      Alle {patients.length} Patienten wurden übergeben.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
