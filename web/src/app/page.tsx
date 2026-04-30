"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";

type PredictionResponse = {
  prediction: 0 | 1;
  failure_probability: number;
  explanation: string;
};

type FormData = {
  Type: "L" | "M" | "H";
  Air_temperature_K: number;
  Process_temperature_K: number;
  Rotational_speed_rpm: number;
  Torque_Nm: number;
  Tool_wear_min: number;
};

type HistoryItem = {
  id: number;
  created_at: string;
  machine_type: "L" | "M" | "H";
  prediction: 0 | 1;
  failure_probability: number;
  explanation: string;
};

const API_URL = "http://127.0.0.1:8000/predict";
const HISTORY_URL = "http://127.0.0.1:8000/history";

type ConfirmationModalProps = {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText: string;
  cancelText: string;
  loading?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
};

function ConfirmationModal({
  isOpen,
  title,
  message,
  confirmText,
  cancelText,
  loading = false,
  onCancel,
  onConfirm,
}: ConfirmationModalProps) {
  const cancelButtonRef = useRef<HTMLButtonElement>(null);
  const clearButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    // Default keyboard focus starts on Cancel for safer actions.
    cancelButtonRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onCancel();
        return;
      }

      if (event.key === "Enter") {
        event.preventDefault();
        onConfirm();
        return;
      }

      if (event.key === "Tab") {
        // Keep focus trapped between modal action buttons.
        const focusable = [cancelButtonRef.current, clearButtonRef.current].filter(
          Boolean
        ) as HTMLButtonElement[];

        if (focusable.length === 0) {
          return;
        }

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onCancel, onConfirm]);

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4 backdrop-blur-sm"
      style={{ animation: "modalFadeIn 220ms ease-out" }}
    >
      <div
        className="w-full max-w-md rounded-3xl border border-slate-200 bg-slate-50 p-6 shadow-[0_18px_40px_-24px_rgba(15,23,42,0.35)] sm:p-8"
        style={{ animation: "modalScaleIn 220ms ease-out" }}
      >
        <div className="flex items-start gap-3.5">
          <div className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-full bg-amber-100/80 text-amber-700">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="h-3.5 w-3.5"
              aria-hidden="true"
            >
              <path d="M12 9v4" />
              <path d="M12 17h.01" />
              <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            </svg>
          </div>

          <div className="flex-1">
            <h3 className="text-xl font-bold tracking-tight text-slate-900">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600/85">{message}</p>
          </div>
        </div>

        <div className="mt-8 flex justify-end gap-2.5">
          <button
            ref={cancelButtonRef}
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="rounded-lg border border-slate-300 bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {cancelText}
          </button>
          <button
            ref={clearButtonRef}
            type="button"
            onClick={onConfirm}
            disabled={loading}
            className="rounded-lg border border-rose-700 bg-rose-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:scale-[1.02] hover:bg-rose-700 hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Clearing..." : confirmText}
          </button>
        </div>
      </div>

      <style jsx global>{`
        @keyframes modalFadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        @keyframes modalScaleIn {
          from {
            opacity: 0;
            transform: scale(0.95);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
      `}</style>
    </div>
  );
}

export default function Home() {
  const [form, setForm] = useState<FormData>({
    Type: "L",
    Air_temperature_K: 300,
    Process_temperature_K: 310,
    Rotational_speed_rpm: 1500,
    Torque_Nm: 45,
    Tool_wear_min: 100,
  });
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [clearingHistory, setClearingHistory] = useState(false);
  const [showClearModal, setShowClearModal] = useState(false);

  const probabilityPercent = result
    ? Math.max(0, Math.min(100, result.failure_probability * 100))
    : 0;
  const probabilityBarColor =
    probabilityPercent < 20
      ? "bg-emerald-500"
      : probabilityPercent <= 50
        ? "bg-amber-400"
        : "bg-rose-500";

  const fetchHistory = useCallback(async () => {
    try {
      const response = await fetch(HISTORY_URL);

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "Failed to fetch history");
      }

      const data: HistoryItem[] = await response.json();
      setHistory(data);
      setHistoryError(null);
    } catch (fetchError) {
      const message =
        fetchError instanceof Error
          ? fetchError.message
          : "Could not load prediction history.";
      setHistoryError(message);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchHistory();
  }, [fetchHistory]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(form),
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "Request failed");
      }

      const data: PredictionResponse = await response.json();
      setResult(data);
      await fetchHistory();
    } catch (submitError) {
      const message =
        submitError instanceof Error
          ? submitError.message
          : "Something went wrong while calling the API.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const fillLowRiskExample = () => {
    setForm({
      Type: "L",
      Air_temperature_K: 300,
      Process_temperature_K: 305,
      Rotational_speed_rpm: 1550,
      Torque_Nm: 38,
      Tool_wear_min: 60,
    });
  };

  const fillHighRiskExample = () => {
    setForm({
      Type: "H",
      Air_temperature_K: 300,
      Process_temperature_K: 315,
      Rotational_speed_rpm: 1350,
      Torque_Nm: 68,
      Tool_wear_min: 180,
    });
  };

  const handleClearHistory = async () => {
    try {
      setClearingHistory(true);
      const response = await fetch(HISTORY_URL, {
        method: "DELETE",
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "Failed to clear history");
      }

      await fetchHistory();
      setShowClearModal(false);
    } catch (clearError) {
      const message =
        clearError instanceof Error ? clearError.message : "Could not clear prediction history.";
      setHistoryError(message);
    } finally {
      setClearingHistory(false);
    }
  };

  const formatTimestamp = (value: string) => {
    const parsedDate = new Date(value);
    if (Number.isNaN(parsedDate.getTime())) {
      return value;
    }
    return parsedDate.toLocaleString();
  };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_#f8fafc_0%,_#e2e8f0_45%,_#cbd5e1_100%)] px-4 py-12 sm:py-16">
      <section className="mx-auto w-full max-w-6xl">
        <header className="mb-10 text-center sm:mb-12">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Predictive Maintenance Copilot
          </h1>
          <p className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">
            Submit machine sensor values to estimate failure risk and get a concise explanation.
          </p>
        </header>

        <div className="grid grid-cols-1 gap-7 lg:grid-cols-2">
          <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
            <h2 className="text-xl font-semibold text-slate-900">Input Parameters</h2>
            <p className="mt-1 text-sm text-slate-600">All fields are required.</p>

            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={fillLowRiskExample}
                className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 transition hover:bg-emerald-100"
              >
                Low Risk Example
              </button>
              <button
                type="button"
                onClick={fillHighRiskExample}
                className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-700 transition hover:bg-rose-100"
              >
                High Risk Example
              </button>
            </div>

            <form className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2" onSubmit={handleSubmit}>
              <label className="flex flex-col gap-1.5 text-sm font-medium text-slate-700">
                Type
                <select
                  className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                  value={form.Type}
                  onChange={(e) =>
                    setForm((prev) => ({ ...prev, Type: e.target.value as "L" | "M" | "H" }))
                  }
                >
                  <option value="L">L</option>
                  <option value="M">M</option>
                  <option value="H">H</option>
                </select>
              </label>

              <label className="flex flex-col gap-1.5 text-sm font-medium text-slate-700">
                Air temperature (K)
                <input
                  type="number"
                  step="any"
                  className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                  value={form.Air_temperature_K}
                  onChange={(e) =>
                    setForm((prev) => ({ ...prev, Air_temperature_K: Number(e.target.value) }))
                  }
                  required
                />
              </label>

              <label className="flex flex-col gap-1.5 text-sm font-medium text-slate-700">
                Process temperature (K)
                <input
                  type="number"
                  step="any"
                  className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                  value={form.Process_temperature_K}
                  onChange={(e) =>
                    setForm((prev) => ({ ...prev, Process_temperature_K: Number(e.target.value) }))
                  }
                  required
                />
              </label>

              <label className="flex flex-col gap-1.5 text-sm font-medium text-slate-700">
                Rotational speed (rpm)
                <input
                  type="number"
                  step="any"
                  className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                  value={form.Rotational_speed_rpm}
                  onChange={(e) =>
                    setForm((prev) => ({ ...prev, Rotational_speed_rpm: Number(e.target.value) }))
                  }
                  required
                />
              </label>

              <label className="flex flex-col gap-1.5 text-sm font-medium text-slate-700">
                Torque (Nm)
                <input
                  type="number"
                  step="any"
                  className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                  value={form.Torque_Nm}
                  onChange={(e) => setForm((prev) => ({ ...prev, Torque_Nm: Number(e.target.value) }))}
                  required
                />
              </label>

              <label className="flex flex-col gap-1.5 text-sm font-medium text-slate-700">
                Tool wear (min)
                <input
                  type="number"
                  step="any"
                  className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                  value={form.Tool_wear_min}
                  onChange={(e) => setForm((prev) => ({ ...prev, Tool_wear_min: Number(e.target.value) }))}
                  required
                />
              </label>

              <div className="mt-2 sm:col-span-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading && (
                    <span
                      className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
                      aria-hidden="true"
                    />
                  )}
                  {loading ? "Predicting..." : "Predict Failure Risk"}
                </button>
              </div>
            </form>

            {error && (
              <div className="mt-5 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {error}
              </div>
            )}
          </article>

          <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-xl font-semibold text-slate-900">Prediction Result</h2>
              {result && (
                <span
                  className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${
                    result.prediction === 1
                      ? "border border-rose-200 bg-rose-50 text-rose-700"
                      : "border border-emerald-200 bg-emerald-50 text-emerald-700"
                  }`}
                >
                  {result.prediction === 1 ? "High Risk" : "Low Risk"}
                </span>
              )}
            </div>

            {!result ? (
              <p className="mt-4 text-sm leading-6 text-slate-600">
                Submit the form to view prediction status, probability, and explanation.
              </p>
            ) : (
              <div className="mt-5 space-y-5">
                <div>
                  <p className="text-sm font-medium text-slate-700">Prediction status</p>
                  <p className="mt-1 text-base font-semibold text-slate-900">
                    {result.prediction === 1 ? "Failure risk detected" : "Low failure risk"}
                  </p>
                </div>

                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-sm font-medium text-slate-700">Failure probability</p>
                    <p className="text-sm font-semibold text-slate-900">
                      {probabilityPercent.toFixed(1)}%
                    </p>
                  </div>
                  <div className="h-3 w-full overflow-hidden rounded-full bg-slate-200">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ease-out ${probabilityBarColor}`}
                      style={{ width: `${probabilityPercent}%` }}
                    />
                  </div>
                </div>

                <div>
                  <p className="text-sm font-medium text-slate-700">Explanation</p>
                  <p className="mt-2 rounded-lg border border-slate-300 bg-slate-100 p-3 text-sm leading-6 text-slate-800">
                    {result.explanation}
                  </p>
                </div>
              </div>
            )}

            <div className="mt-6 border-t border-slate-200 pt-5">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium text-slate-700">Recent History</p>
                <button
                  type="button"
                  onClick={() => setShowClearModal(true)}
                  disabled={clearingHistory}
                  className="rounded-md border border-slate-300 bg-white px-3 py-1 text-xs font-semibold text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {clearingHistory ? "Clearing..." : "Clear History"}
                </button>
              </div>

              {historyError && (
                <p className="mt-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
                  {historyError}
                </p>
              )}

              {history.length === 0 && !historyError ? (
                <p className="mt-2 text-sm text-slate-600">No history yet</p>
              ) : (
                <div className="mt-2 space-y-2">
                  {history.map((item) => (
                    <article key={item.id} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="text-xs text-slate-500">
                          {formatTimestamp(item.created_at)} | Type {item.machine_type}
                        </p>
                        <span
                          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                            item.prediction === 1
                              ? "border border-rose-200 bg-rose-50 text-rose-700"
                              : "border border-emerald-200 bg-emerald-50 text-emerald-700"
                          }`}
                        >
                          {item.prediction === 1 ? "High Risk" : "Low Risk"}
                        </span>
                      </div>

                      <p className="mt-2 text-sm font-medium text-slate-700">
                        Failure probability: {(item.failure_probability * 100).toFixed(1)}%
                      </p>
                      <p className="mt-1 whitespace-pre-wrap break-words text-sm text-slate-600">
                        {item.explanation}
                      </p>
                    </article>
                  ))}
                </div>
              )}
            </div>
          </article>
        </div>
      </section>

      <ConfirmationModal
        isOpen={showClearModal}
        title="Clear Prediction History"
        message="Are you sure you want to clear all prediction history?"
        confirmText="Clear"
        cancelText="Cancel"
        loading={clearingHistory}
        onCancel={() => setShowClearModal(false)}
        onConfirm={handleClearHistory}
      />
    </main>
  );
}
