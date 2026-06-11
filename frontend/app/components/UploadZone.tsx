"use client";

import { useRef, useState, DragEvent, ChangeEvent } from "react";
import { UploadCloud, X, ImageIcon, Camera } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  onFileChange: (file: File | null) => void;
  file: File | null;
}

export function UploadZone({ onFileChange, file }: Props) {
  const inputRef   = useRef<HTMLInputElement>(null);
  const cameraRef  = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.type.startsWith("image/")) onFileChange(dropped);
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] ?? null;
    if (selected) onFileChange(selected);
  };

  const preview = file ? URL.createObjectURL(file) : null;

  return (
    <div className="space-y-2">
      {/* Zona drag & drop */}
      <div
        onClick={() => !file && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={cn(
          "relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed transition-all duration-200 overflow-hidden",
          "min-h-[220px] cursor-pointer select-none",
          dragging
            ? "border-primary bg-primary/5 scale-[1.01]"
            : "border-border bg-muted/30 hover:border-white/30 hover:bg-muted/50",
          file && "cursor-default"
        )}
      >
        {/* Input galería */}
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleChange}
        />
        {/* Input cámara — capture="environment" abre la cámara trasera en móvil */}
        <input
          ref={cameraRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={handleChange}
        />

        {preview ? (
          <>
            <img
              src={preview}
              alt="preview"
              className="h-full w-full object-contain max-h-[220px]"
            />
            <button
              onClick={(e) => { e.stopPropagation(); onFileChange(null); }}
              className="absolute top-2 right-2 rounded-full bg-background/80 p-1 shadow hover:bg-destructive hover:text-white transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </>
        ) : (
          <div className="flex flex-col items-center gap-3 p-8 text-muted-foreground">
            <div className="rounded-full bg-white/10 p-4">
              <UploadCloud className="h-8 w-8 text-white" />
            </div>
            <div className="text-center">
              <p className="text-sm font-medium text-foreground">
                Arrastra una imagen o haz clic
              </p>
              <p className="text-xs mt-1">JPG, PNG · foto de la conjuntiva palpebral</p>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground/60">
              <ImageIcon className="h-3 w-3" />
              <span>Tira el párpado inferior hacia abajo antes de fotografiar</span>
            </div>
          </div>
        )}
      </div>

      {/* Botón tomar foto — solo visible cuando no hay imagen */}
      {!file && (
        <button
          onClick={() => cameraRef.current?.click()}
          className={cn(
            "w-full flex items-center justify-center gap-2 rounded-2xl border border-border",
            "py-3 text-sm font-medium text-muted-foreground",
            "hover:border-white/30 hover:text-foreground hover:bg-muted/50 transition-all"
          )}
        >
          <Camera className="h-4 w-4" />
          Tomar foto
        </button>
      )}
    </div>
  );
}
