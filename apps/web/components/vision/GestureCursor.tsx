"use client";

import React from "react";

export type GestureCursorPosition = {
  x: number;
  y: number;
};

export interface GestureCursorProps {
  position?: GestureCursorPosition | null;

  gesture?: string;

  visible?: boolean;

  size?: number;

  label?: string;

  className?: string;
}

const gestureLabels: Record<
  string,
  string
> = {
  NONE: "",
  OPEN_PALM: "Open Palm",
  CLOSED_FIST: "Fist",
  POINT: "Point",
  PEACE: "Peace",
  THUMBS_UP: "Thumbs Up",
  THUMBS_DOWN: "Thumbs Down",
  PINCH: "Pinch",
  OK: "OK",
  SWIPE_LEFT: "Swipe Left",
  SWIPE_RIGHT: "Swipe Right",
  SWIPE_UP: "Swipe Up",
  SWIPE_DOWN: "Swipe Down",
};

export default function GestureCursor({
  position = null,
  gesture = "NONE",
  visible = true,
  size = 32,
  label,
  className = "",
}: GestureCursorProps) {
  if (
    !visible ||
    !position
  ) {
    return null;
  }

  const normalizedX =
    Math.max(
      0,
      Math.min(100, position.x)
    );

  const normalizedY =
    Math.max(
      0,
      Math.min(100, position.y)
    );

  const gestureLabel =
    label ??
    gestureLabels[
      gesture.toUpperCase()
    ] ??
    gesture;

  const isPinch =
    gesture.toUpperCase() ===
    "PINCH";

  const isPoint =
    gesture.toUpperCase() ===
    "POINT";

  return (
    <div
      className={`pointer-events-none absolute z-30 ${className}`}
      style={{
        left: `${normalizedX}%`,
        top: `${normalizedY}%`,
        transform:
          "translate(-50%, -50%)",
      }}
    >
      <div
        className={`relative flex items-center justify-center rounded-full border-2 shadow-lg ${
          isPinch
            ? "border-blue-400 bg-blue-500/30"
            : isPoint
            ? "border-white bg-white/20"
            : "border-blue-300 bg-blue-500/20"
        }`}
        style={{
          width: size,
          height: size,
        }}
      >
        <span
          className={`absolute inset-1 rounded-full ${
            isPinch
              ? "animate-ping bg-blue-400/30"
              : "bg-blue-400/10"
          }`}
        />

        <span
          className={`relative h-2.5 w-2.5 rounded-full ${
            isPinch
              ? "bg-blue-300"
              : "bg-white"
          }`}
        />
      </div>

      {gestureLabel && (
        <div className="absolute left-1/2 top-full mt-2 -translate-x-1/2 whitespace-nowrap rounded-md bg-black/70 px-2 py-1 text-[9px] font-medium text-white backdrop-blur">
          {gestureLabel}
        </div>
      )}
    </div>
  );
}