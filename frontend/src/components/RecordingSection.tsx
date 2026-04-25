import { useCallback, useEffect, useRef, useState } from "react";
import { postTranscribe } from "../api/transcribe";

interface Props {
  patientId: string;
  onTranscript: (transcript: string) => void;
}

type RecordingState = "idle" | "recording" | "processing";

// Web Speech API — not yet in all TS DOM typings
interface SpeechRecognitionEvent extends Event {
  readonly results: SpeechRecognitionResultList;
}
interface SpeechRecognitionLike extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((ev: SpeechRecognitionEvent) => void) | null;
  onerror: ((ev: Event) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}

function getSpeechRecognition(): SpeechRecognitionLike | null {
  const w = window as unknown as Record<string, unknown>;
  const Ctor = (w["SpeechRecognition"] ?? w["webkitSpeechRecognition"]) as
    | (new () => SpeechRecognitionLike)
    | undefined;
  return Ctor ? new Ctor() : null;
}

export default function RecordingSection({ patientId, onTranscript }: Props) {
  const [state, setState] = useState<RecordingState>("idle");
  const [liveCaption, setLiveCaption] = useState("");
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);

  // Cleanup on unmount or patient change
  useEffect(() => {
    return () => {
      recognitionRef.current?.stop();
      mediaRecorderRef.current?.stop();
    };
  }, [patientId]);

  const startRecording = useCallback(async () => {
    setError(null);
    setLiveCaption("");

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError("Mikrofon konnte nicht gestartet werden.");
      return;
    }

    chunksRef.current = [];
    const recorder = new MediaRecorder(stream, {
      mimeType: MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm",
    });
    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    mediaRecorderRef.current = recorder;
    recorder.start(250);

    // Live captions via Web Speech API
    const recognition = getSpeechRecognition();
    if (recognition) {
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "de-DE";
      recognition.onresult = (ev) => {
        let interim = "";
        let final = "";
        for (let i = 0; i < ev.results.length; i++) {
          const r = ev.results[i];
          if (r.isFinal) final += r[0].transcript + " ";
          else interim += r[0].transcript;
        }
        setLiveCaption((final + interim).trim());
      };
      recognition.onerror = () => {
        /* non-fatal: captions stop but recording continues */
      };
      try {
        recognition.start();
      } catch {
        /* already started or not available */
      }
      recognitionRef.current = recognition;
    }

    setState("recording");
  }, []);

  const stopRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (!recorder) return;

    recognitionRef.current?.stop();
    recognitionRef.current = null;
    setState("processing");

    recorder.onstop = async () => {
      // Release mic
      recorder.stream.getTracks().forEach((t) => t.stop());

      const blob = new Blob(chunksRef.current, {
        type: recorder.mimeType || "audio/webm",
      });
      try {
        const transcript = await postTranscribe(blob);
        onTranscript(transcript);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Transkription fehlgeschlagen"
        );
      } finally {
        setState("idle");
        setLiveCaption("");
      }
    };

    recorder.stop();
    mediaRecorderRef.current = null;
  }, [onTranscript]);

  return (
    <section className="border-t border-slate-100 pt-4">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
        Übergabe aufnehmen
      </h3>

      {/* Record / Stop button */}
      <div className="flex items-center gap-3">
        {state === "idle" && (
          <button
            onClick={() => void startRecording()}
            className="flex items-center gap-2 bg-blue-700 hover:bg-blue-800 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            <span className="w-3 h-3 rounded-full bg-white" />
            Aufnahme starten
          </button>
        )}

        {state === "recording" && (
          <button
            onClick={stopRecording}
            className="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            <span className="w-3 h-3 rounded-sm bg-white" />
            Aufnahme beenden
          </button>
        )}

        {state === "processing" && (
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <span className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            Wird transkribiert…
          </div>
        )}

        {state === "recording" && (
          <span className="flex items-center gap-1.5 text-xs text-red-600 animate-pulse">
            <span className="w-2 h-2 rounded-full bg-red-600" />
            REC
          </span>
        )}
      </div>

      {/* Live caption */}
      {state === "recording" && (
        <div className="mt-3 min-h-[56px] bg-slate-50 rounded-lg px-3 py-2 text-sm text-slate-600 leading-relaxed">
          {liveCaption || (
            <span className="text-slate-400 italic">Sprechen Sie jetzt…</span>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <p className="mt-2 text-xs text-red-600">{error}</p>
      )}
    </section>
  );
}
