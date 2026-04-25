import { useEffect, useState } from "react";

interface HealthStatus {
  status: string;
  service: string;
  version: string;
}

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<HealthStatus>;
      })
      .then(setHealth)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Connection failed")
      );
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-blue-900 text-white px-4 py-3 safe-top shadow-md">
        <div className="max-w-lg mx-auto flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-blue-500 flex items-center justify-center text-sm font-bold shrink-0">
            SC
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-base font-semibold leading-tight">ShiftChange-Bot</h1>
            <p className="text-xs text-blue-300 truncate">Voice-Structured Handover</p>
          </div>
          {health && (
            <span className="text-xs bg-green-500 rounded-full px-2.5 py-0.5 shrink-0">
              Online
            </span>
          )}
          {error && (
            <span className="text-xs bg-red-500 rounded-full px-2.5 py-0.5 shrink-0">
              Offline
            </span>
          )}
        </div>
      </header>

      <main className="flex-1 px-4 py-6 max-w-lg mx-auto w-full space-y-6">
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            System Status
          </h2>
          {error ? (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
              Backend unreachable: {error}
            </div>
          ) : health ? (
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-4 text-sm divide-y divide-slate-50">
              <div className="flex justify-between py-1.5">
                <span className="text-slate-500">Service</span>
                <span className="font-medium">{health.service}</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-slate-500">Status</span>
                <span className="font-medium text-green-600">{health.status}</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-slate-500">Version</span>
                <span className="font-medium text-slate-400">{health.version}</span>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-4 text-sm text-slate-400 animate-pulse">
              Connecting...
            </div>
          )}
        </section>

        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Shift Handover
          </h2>
          <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 flex flex-col items-center gap-4">
            <button
              className="w-24 h-24 rounded-full bg-blue-700 text-white flex items-center justify-center shadow-lg active:scale-95 transition-transform"
              aria-label="Start voice recording"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
                className="w-11 h-11"
              >
                <path d="M8.25 4.5a3.75 3.75 0 1 1 7.5 0v8.25a3.75 3.75 0 1 1-7.5 0V4.5Z" />
                <path d="M6 10.5a.75.75 0 0 1 .75.75v1.5a5.25 5.25 0 1 0 10.5 0v-1.5a.75.75 0 0 1 1.5 0v1.5a6.751 6.751 0 0 1-6 6.709v2.291h3a.75.75 0 0 1 0 1.5h-7.5a.75.75 0 0 1 0-1.5h3v-2.291a6.751 6.751 0 0 1-6-6.709v-1.5A.75.75 0 0 1 6 10.5Z" />
              </svg>
            </button>
            <p className="text-sm text-slate-500 text-center">
              Tap to start voice handover
            </p>
          </div>
        </section>

        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Recent Handovers
          </h2>
          <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 text-sm text-slate-400 text-center">
            No handovers recorded yet
          </div>
        </section>
      </main>
    </div>
  );
}
