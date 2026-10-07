"use client";

import React from "react";

type VisionOverlayProps = {
  active?: boolean;
  gesture?: string;
  gestureConfidence?: number;
  hands?: number;
  fps?: number;
  processing?: boolean;
  showGesture?: boolean;
  showHands?: boolean;
  showStats?: boolean;
  showInstructions?: boolean;
  instruction?: string;
  className?: string;
};

const gestureLabels: Record<string, string> = {
  NONE: "No Gesture",
  OPEN_PALM: "Open Palm",
  CLOSED_FIST: "Closed Fist",
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

const gestureActions: Record<string, string> = {
  NONE: "Waiting",
  OPEN_PALM: "Pause",
  CLOSED_FIST: "Hold",
  POINT: "Move Cursor",
  PEACE: "Navigation",
  THUMBS_UP: "Confirm",
  THUMBS_DOWN: "Reject",
  PINCH: "Left Click",
  OK: "Confirm",
  SWIPE_LEFT: "Previous",
  SWIPE_RIGHT: "Next",
  SWIPE_UP: "Scroll Up",
  SWIPE_DOWN: "Scroll Down",
};

function getGestureLabel(gesture: string): string {
  const normalized = gesture.toUpperCase();

  return (
    gestureLabels[normalized] ??
    normalized.replaceAll("_", " ")
  );
}

function getGestureAction(gesture: string): string {
  const normalized = gesture.toUpperCase();

  return gestureActions[normalized] ?? "Detected";
}

function clamp(
  value: number,
  min: number,
  max: number,
): number {
  return Math.min(max, Math.max(min, value));
}

export default function VisionOverlay({
  active = false,
  gesture = "NONE",
  gestureConfidence = 0,
  hands = 0,
  fps = 0,
  processing = false,
  showGesture = true,
  showHands = true,
  showStats = true,
  showInstructions = true,
  instruction,
  className = "",
}: VisionOverlayProps) {
  const normalizedGesture = gesture.toUpperCase();

  const confidence = clamp(
    gestureConfidence,
    0,
    1,
  );

  const confidencePercent = Math.round(
    confidence * 100,
  );

  const gestureLabel =
    getGestureLabel(normalizedGesture);

  const gestureAction =
    getGestureAction(normalizedGesture);

  return (
    <div
      className={`pointer-events-none absolute inset-0 z-20 ${className}`}
    >
      {/* =========================================================
          TOP STATUS
      ========================================================= */}

      <div className="absolute left-3 top-3 flex items-center gap-2">
        {/* Vision status */}

        <div className="flex items-center gap-2 rounded-full border border-[#263249] bg-black/60 px-3 py-1.5 shadow-lg backdrop-blur">
          <span
            className={`h-2 w-2 rounded-full ${
              active
                ? processing
                  ? "animate-pulse bg-amber-400"
                  : "bg-[#43d19e] shadow-[0_0_10px_#43d19e]"
                : "bg-[#64748b]"
            }`}
          />

          <span className="text-[10px] font-medium text-white">
            {active
              ? "Vision Active"
              : "Vision Inactive"}
          </span>
        </div>

        {/* Processing */}

        {processing && active && (
          <div className="rounded-full border border-blue-400/20 bg-blue-500/10 px-2.5 py-1.5 text-[10px] text-blue-200 shadow-lg backdrop-blur">
            Processing
          </div>
        )}
      </div>

      {/* =========================================================
          GESTURE INFORMATION
      ========================================================= */}

      {showGesture && active && (
        <div className="absolute right-3 top-3 w-[190px] rounded-xl border border-[#263249] bg-black/65 p-3 shadow-lg backdrop-blur">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-[9px] font-semibold uppercase tracking-[0.16em] text-[#71809a]">
                Gesture
              </p>

              <p className="mt-1 text-sm font-semibold text-white">
                {gestureLabel}
              </p>
            </div>

            <span className="rounded-md bg-[#111827] px-2 py-1 text-[9px] font-medium text-[#91a0b8]">
              {gestureAction}
            </span>
          </div>

          {/* Confidence */}

          <div className="mt-3">
            <div className="mb-1 flex items-center justify-between">
              <span className="text-[9px] text-[#71809a]">
                Confidence
              </span>

              <span className="text-[9px] font-medium text-white">
                {confidencePercent}%
              </span>
            </div>

            <div className="h-1.5 overflow-hidden rounded-full bg-[#1a2436]">
              <div
                className="h-full rounded-full bg-[#5b8cff] transition-all duration-150"
                style={{
                  width: `${confidencePercent}%`,
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* =========================================================
          STATS
      ========================================================= */}

      {showStats && active && (
        <div className="absolute bottom-3 right-3 flex items-center gap-2">
          {/* Hands */}

          {showHands && (
            <div className="rounded-lg border border-[#263249] bg-black/60 px-2.5 py-1.5 shadow-lg backdrop-blur">
              <span className="text-[9px] text-[#71809a]">
                Hands
              </span>

              <span className="ml-1.5 text-[10px] font-semibold text-white">
                {hands}
              </span>
            </div>
          )}

          {/* FPS */}

          <div className="rounded-lg border border-[#263249] bg-black/60 px-2.5 py-1.5 shadow-lg backdrop-blur">
            <span className="text-[9px] text-[#71809a]">
              FPS
            </span>

            <span className="ml-1.5 text-[10px] font-semibold text-white">
              {fps}
            </span>
          </div>
        </div>
      )}

      {/* =========================================================
          INSTRUCTIONS
      ========================================================= */}

      {showInstructions &&
        active &&
        instruction && (
          <div className="absolute bottom-3 left-1/2 max-w-[80%] -translate-x-1/2 rounded-lg border border-[#263249] bg-black/65 px-4 py-2 text-center shadow-lg backdrop-blur">
            <p className="text-[10px] leading-4 text-[#d9e2f2]">
              {instruction}
            </p>
          </div>
        )}
    </div>
  );
}