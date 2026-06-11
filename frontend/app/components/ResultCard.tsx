"use client";

import { AlertTriangle, CheckCircle2, Droplets } from "lucide-react";
import { cn } from "@/lib/utils";

export interface PredictionResult {
  hb_pred_gdl: number;
  threshold:   number;
  gender:      string;
  diagnosis:   "ANEMIA" | "NORMAL";
  anemia:      boolean;
}

interface Props {
  result: PredictionResult;
}

const GENDER_LABEL: Record<string, string> = {
  male:   "Hombre",
  female: "Mujer",
};

export function ResultCard({ result }: Props) {
  const isAnemia = result.anemia;
  const color = isAnemia ? "red" : "green";

  return (
    <div className="rounded-2xl border border-border bg-card overflow-hidden">

      {/* Header coloreado */}
      <div
        className={cn(
          "px-6 py-5 flex items-center justify-between",
          isAnemia ? "bg-red-500/10" : "bg-green-500/10"
        )}
      >
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "rounded-full p-2",
              isAnemia ? "bg-red-500/20" : "bg-green-500/20"
            )}
          >
            {isAnemia
              ? <AlertTriangle className="h-5 w-5 text-red-400" />
              : <CheckCircle2 className="h-5 w-5 text-green-400" />
            }
          </div>
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-widest font-medium">
              Diagnóstico
            </p>
            <p className={cn(
              "text-lg font-bold leading-tight",
              isAnemia ? "text-red-400" : "text-green-400"
            )}>
              {isAnemia ? "Posible Anemia" : "Normal"}
            </p>
          </div>
        </div>

        {/* Valor Hb grande */}
        <div className="text-right">
          <div className="flex items-baseline gap-1 justify-end">
            <span className="text-4xl font-bold tracking-tight">
              {result.hb_pred_gdl.toFixed(1)}
            </span>
            <span className="text-sm text-muted-foreground">g/dL</span>
          </div>
          <p className="text-xs text-muted-foreground">hemoglobina</p>
        </div>
      </div>

      {/* Cuerpo */}
      <div className="px-6 py-4 space-y-4">

        {/* Barra */}
        <HbBar value={result.hb_pred_gdl} threshold={result.threshold} isAnemia={isAnemia} />

        {/* Detalles */}
        <div className="grid grid-cols-2 gap-2 pt-1">
          <Detail label="Umbral OMS" value={`${result.threshold} g/dL`} />
          <Detail label="Género" value={GENDER_LABEL[result.gender] ?? result.gender} />
        </div>

        {/* Disclaimer */}
        {isAnemia && (
          <p className="text-xs text-muted-foreground border-t border-border pt-3">
            Resultado orientativo. Consulta con un profesional de la salud
            para un diagnóstico definitivo mediante análisis de sangre.
          </p>
        )}
      </div>
    </div>
  );
}

function HbBar({
  value, threshold, isAnemia,
}: {
  value: number; threshold: number; isAnemia: boolean;
}) {
  const MAX_HB = 18;
  const pct       = Math.min((value / MAX_HB) * 100, 100);
  const threshPct = (threshold / MAX_HB) * 100;

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>0 g/dL</span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-px h-3 bg-foreground/30" />
          Umbral {threshold}
        </span>
        <span>{MAX_HB} g/dL</span>
      </div>
      <div className="relative h-2 w-full rounded-full bg-muted overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-700",
            isAnemia ? "bg-red-500" : "bg-green-500"
          )}
          style={{ width: `${pct}%` }}
        />
        <div
          className="absolute top-0 h-full w-px bg-foreground/40"
          style={{ left: `${threshPct}%` }}
        />
      </div>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-muted/50 px-3 py-2.5 space-y-0.5">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-semibold">{value}</p>
    </div>
  );
}
