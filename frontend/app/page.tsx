"use client";

import { useState } from "react";
import { Loader2, ScanEye } from "lucide-react";
import { UploadZone } from "./components/UploadZone";
import { ResultCard, PredictionResult } from "./components/ResultCard";
import { cn } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const GENDERS = [
  { value: "female", label: "Mujer" },
  { value: "male",   label: "Hombre" },
];

export default function Home() {
  const [file,    setFile]    = useState<File | null>(null);
  const [gender,  setGender]  = useState("female");
  const [loading, setLoading] = useState(false);
  const [result,  setResult]  = useState<PredictionResult | null>(null);
  const [error,   setError]   = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const form = new FormData();
      form.append("image", file);
      form.append("gender", gender);

      const res = await fetch(`${API_URL}/predict`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.detail ?? `Error ${res.status}`);
      }

      const data: PredictionResult = await res.json();
      setResult(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error desconocido.");
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (f: File | null) => {
    setFile(f);
    setResult(null);
    setError(null);
  };

  return (
    <main className="min-h-screen bg-background flex flex-col items-center py-16 px-4">

      {/* Header */}
      <div className="flex flex-col items-center gap-2 mb-10">
        <div className="flex items-center gap-3">
          <div className="rounded-2xl bg-primary/10 p-3">
            <ScanEye className="h-8 w-8 text-primary" />
          </div>
          <h1 className="text-4xl font-bold tracking-tight">HemoScan</h1>
        </div>
        <p className="text-muted-foreground text-center max-w-md text-sm">
          Estimación de hemoglobina (Hb) a partir de una fotografía de la
          conjuntiva palpebral. Solo para uso orientativo.
        </p>
      </div>

      {/* Card principal */}
      <div className="w-full max-w-md space-y-5">

        {/* Upload */}
        <div className="rounded-2xl border bg-card shadow-sm p-5 space-y-4">
          <h2 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">
            Imagen del ojo
          </h2>
          <UploadZone file={file} onFileChange={handleFileChange} />
        </div>

        {/* Género */}
        <div className="rounded-2xl border bg-card shadow-sm p-5 space-y-3">
          <h2 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">
            Género del paciente
          </h2>
          <div className="grid grid-cols-3 gap-2">
            {GENDERS.map((g) => (
              <button
                key={g.value}
                onClick={() => setGender(g.value)}
                className={cn(
                  "rounded-xl border px-3 py-2 text-sm font-medium transition-all",
                  gender === g.value
                    ? "border-white bg-white text-black shadow"
                    : "border-border bg-background text-foreground hover:border-white/30 hover:bg-muted"
                )}
              >
                {g.label}
              </button>
            ))}
          </div>
        </div>

        {/* Botón */}
        <button
          onClick={handleAnalyze}
          disabled={!file || loading}
          className={cn(
            "w-full rounded-2xl py-3.5 text-base font-semibold transition-all duration-200 shadow",
            "flex items-center justify-center gap-2",
            file && !loading
              ? "bg-white text-black hover:bg-white/90 active:scale-[0.98]"
              : "bg-muted text-muted-foreground cursor-not-allowed"
          )}
        >
          {loading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              Analizando…
            </>
          ) : (
            <>
              <ScanEye className="h-5 w-5" />
              Analizar
            </>
          )}
        </button>

        {/* Error */}
        {error && (
          <div className="rounded-2xl border border-destructive/40 bg-destructive/5 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {/* Resultado */}
        {result && <ResultCard result={result} />}
      </div>

      <p className="mt-12 text-xs text-muted-foreground/50 text-center max-w-xs">
        HemoScan no reemplaza un diagnóstico médico. Los resultados son
        estimaciones basadas en un modelo de aprendizaje automático.
      </p>
    </main>
  );
}
