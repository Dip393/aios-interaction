"use client";

import React, { useEffect, useRef, useState } from "react";

import {
  FilesetResolver,
  HandLandmarker,
} from "@mediapipe/tasks-vision";

export type HandGestureControllerProps = {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  enabled?: boolean;
  /**
   * Kept for backwards compatibility.
   * Gesture -> mouse action mapping lives in VisionPanel.
   */
  controlEnabled?: boolean;
  mirrored?: boolean;
  onResult?: (result: HandGestureResult) => void;
  onError?: (error: Error) => void;
  className?: string;
};

export type HandGestureName =
  | "NONE"
  | "POINT"
  | "PINCH"
  | "OPEN_PALM"
  | "CLOSED_FIST"
  | "PEACE"
  | "THUMBS_UP"
  | "THUMBS_DOWN";

export type HandGestureResult = {
  gesture: HandGestureName;
  confidence: number;
  cursor: {
    x: number;
    y: number;
  } | null;
  hands: number;
  landmarks: Array<{
    x: number;
    y: number;
    z: number;
  }>;
  timestamp: number;
  /**
   * Thumb-tip <-> index-tip distance, normalised by palm size.
   * Small = pinching. Used by the consumer to freeze the cursor
   * while the fingers approach each other.
   */
  pinchDistance?: number;
};

type Point = {
  x: number;
  y: number;
  z: number;
};

const MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task";

const WASM_URL =
  "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@1.1.0/wasm";

const CURSOR_SMOOTHING = 0.35;

/*
 * Distances below are normalised by palm size
 * (wrist -> middle finger MCP), so they do not depend on how far
 * the hand is from the camera.
 */
const PINCH_START_RATIO = 0.3;
const PINCH_END_RATIO = 0.45;
const FINGER_EXTENDED_RATIO = 1.12;
const THUMB_EXTENDED_RATIO = 0.6;

const WRIST = 0;
const THUMB_TIP = 4;
const INDEX_MCP = 5;
const INDEX_PIP = 6;
const INDEX_TIP = 8;
const MIDDLE_MCP = 9;
const MIDDLE_PIP = 10;
const MIDDLE_TIP = 12;
const RING_PIP = 14;
const RING_TIP = 16;
const PINKY_PIP = 18;
const PINKY_TIP = 20;

function distance(a: Point, b: Point): number {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

/**
 * Classify one hand.
 *
 * `aspect` (video width / height) converts MediaPipe's per-axis
 * normalised coordinates into a uniform space so distances are
 * not stretched on 16:9 frames.
 *
 * `pinchActive` enables hysteresis: once pinching, the fingers have
 * to open past PINCH_END_RATIO before the pinch is released.
 */
export function classifyHand(
  landmarks: Point[],
  aspect = 16 / 9,
  pinchActive = false,
): {
  gesture: HandGestureName;
  confidence: number;
  pinchDistance: number;
} {
  if (landmarks.length < 21) {
    return {
      gesture: "NONE",
      confidence: 0,
      pinchDistance: Number.POSITIVE_INFINITY,
    };
  }

  const p: Point[] = landmarks.map((l) => ({
    x: l.x * aspect,
    y: l.y,
    z: 0,
  }));

  const palm = distance(p[WRIST], p[MIDDLE_MCP]);

  if (palm < 1e-4) {
    return {
      gesture: "NONE",
      confidence: 0,
      pinchDistance: Number.POSITIVE_INFINITY,
    };
  }

  const extended = (tip: number, pip: number) =>
    distance(p[WRIST], p[tip]) >
    distance(p[WRIST], p[pip]) * FINGER_EXTENDED_RATIO;

  const indexExtended = extended(INDEX_TIP, INDEX_PIP);
  const middleExtended = extended(MIDDLE_TIP, MIDDLE_PIP);
  const ringExtended = extended(RING_TIP, RING_PIP);
  const pinkyExtended = extended(PINKY_TIP, PINKY_PIP);

  const thumbExtended =
    distance(p[THUMB_TIP], p[INDEX_MCP]) / palm >
    THUMB_EXTENDED_RATIO;

  const pinchDistance =
    distance(p[THUMB_TIP], p[INDEX_TIP]) / palm;

  /*
   * A closed fist also brings thumb and index tips together.
   * A real pinch keeps the index finger at least partly open.
   */
  const indexNotCurled =
    distance(p[WRIST], p[INDEX_TIP]) >=
    distance(p[WRIST], p[INDEX_PIP]);

  const pinching =
    (pinchDistance < PINCH_START_RATIO ||
      (pinchActive && pinchDistance < PINCH_END_RATIO)) &&
    (indexNotCurled || pinchDistance < 0.18);

  if (pinching) {
    return {
      gesture: "PINCH",
      confidence: clamp(1 - pinchDistance / PINCH_END_RATIO, 0.5, 1),
      pinchDistance,
    };
  }

  if (
    indexExtended &&
    !middleExtended &&
    !ringExtended &&
    !pinkyExtended
  ) {
    return { gesture: "POINT", confidence: 0.9, pinchDistance };
  }

  if (
    indexExtended &&
    middleExtended &&
    !ringExtended &&
    !pinkyExtended
  ) {
    return { gesture: "PEACE", confidence: 0.9, pinchDistance };
  }

  if (
    thumbExtended &&
    indexExtended &&
    middleExtended &&
    ringExtended &&
    pinkyExtended
  ) {
    return { gesture: "OPEN_PALM", confidence: 0.9, pinchDistance };
  }

  if (
    thumbExtended &&
    !indexExtended &&
    !middleExtended &&
    !ringExtended &&
    !pinkyExtended &&
    p[THUMB_TIP].y < p[INDEX_MCP].y
  ) {
    return { gesture: "THUMBS_UP", confidence: 0.85, pinchDistance };
  }

  if (
    !indexExtended &&
    !middleExtended &&
    !ringExtended &&
    !pinkyExtended &&
    !thumbExtended
  ) {
    return { gesture: "CLOSED_FIST", confidence: 0.85, pinchDistance };
  }

  return { gesture: "NONE", confidence: 0.4, pinchDistance };
}

export default function HandGestureController({
  videoRef,
  enabled = true,
  mirrored = true,
  onResult,
  onError,
  className = "",
}: HandGestureControllerProps) {
  const [ready, setReady] = useState(false);
  const [tracking, setTracking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const landmarkerRef = useRef<HandLandmarker | null>(null);

  /*
   * Callbacks/props live in refs so that parent re-renders
   * (which happen on every gesture result) never tear down
   * the MediaPipe model or restart the detection loop.
   */
  const onResultRef = useRef(onResult);
  const onErrorRef = useRef(onError);
  const mirroredRef = useRef(mirrored);

  useEffect(() => {
    onResultRef.current = onResult;
    onErrorRef.current = onError;
    mirroredRef.current = mirrored;
  });

  /*
   * Create the landmarker exactly once.
   */
  useEffect(() => {
    let cancelled = false;
    let created: HandLandmarker | null = null;

    const create = async () => {
      try {
        setError(null);

        const fileset =
          await FilesetResolver.forVisionTasks(WASM_URL);

        const buildOptions = (delegate: "GPU" | "CPU") => ({
          baseOptions: {
            modelAssetPath: MODEL_URL,
            delegate,
          },
          runningMode: "VIDEO" as const,
          numHands: 1,
          minHandDetectionConfidence: 0.55,
          minHandPresenceConfidence: 0.55,
          minTrackingConfidence: 0.55,
        });

        let landmarker: HandLandmarker;

        try {
          landmarker = await HandLandmarker.createFromOptions(
            fileset,
            buildOptions("GPU"),
          );
        } catch {
          /* GPU delegate is not available everywhere (e.g. some WebViews). */
          landmarker = await HandLandmarker.createFromOptions(
            fileset,
            buildOptions("CPU"),
          );
        }

        if (cancelled) {
          landmarker.close();
          return;
        }

        created = landmarker;
        landmarkerRef.current = landmarker;
        setReady(true);
      } catch (err) {
        if (cancelled) {
          return;
        }

        const normalized =
          err instanceof Error ? err : new Error(String(err));

        setError(normalized.message);
        onErrorRef.current?.(normalized);
      }
    };

    void create();

    return () => {
      cancelled = true;

      landmarkerRef.current = null;

      try {
        created?.close();
      } catch {
        /* already closed */
      }

      setReady(false);
    };
  }, []);

  /*
   * Detection loop.
   *
   * One loop per (enabled, ready) change. The next frame is ALWAYS
   * scheduled from `finally`, so "no hand", errors or early exits
   * can never stop the loop.
   */
  useEffect(() => {
    if (!enabled || !ready) {
      return;
    }

    let active = true;
    let rafId = 0;

    let lastVideoTime = -1;
    let lastTimestamp = 0;
    let smoothed: { x: number; y: number } | null = null;
    let pinchActive = false;
    let wasTracking = false;
    let lastErrorMessage = "";

    const emit = (result: HandGestureResult) => {
      onResultRef.current?.(result);
    };

    const tick = () => {
      if (!active) {
        return;
      }

      try {
        const video = videoRef.current;
        const landmarker = landmarkerRef.current;

        if (
          video &&
          landmarker &&
          video.readyState >= 2 &&
          video.videoWidth > 0 &&
          video.videoHeight > 0 &&
          video.currentTime !== lastVideoTime
        ) {
          lastVideoTime = video.currentTime;

          const now = performance.now();
          const timestamp =
            now > lastTimestamp ? now : lastTimestamp + 1;
          lastTimestamp = timestamp;

          const result = landmarker.detectForVideo(
            video,
            timestamp,
          );

          const handCount = result.landmarks?.length ?? 0;
          const hand = result.landmarks?.[0];

          if (!hand || hand.length < 21) {
            if (wasTracking) {
              wasTracking = false;
              setTracking(false);
            }

            smoothed = null;
            pinchActive = false;

            emit({
              gesture: "NONE",
              confidence: 0,
              cursor: null,
              hands: handCount,
              landmarks: [],
              timestamp: now,
            });
          } else {
            if (!wasTracking) {
              wasTracking = true;
              setTracking(true);
            }

            const landmarks: Point[] = hand.map((l) => ({
              x: l.x,
              y: l.y,
              z: l.z,
            }));

            const detected = classifyHand(
              landmarks,
              video.videoWidth / video.videoHeight,
              pinchActive,
            );

            pinchActive = detected.gesture === "PINCH";

            /* Index fingertip is the virtual cursor. */
            let cursorX = landmarks[INDEX_TIP].x;
            const cursorY = landmarks[INDEX_TIP].y;

            /* Preview is mirrored, so the logical X is inverted. */
            if (mirroredRef.current) {
              cursorX = 1 - cursorX;
            }

            cursorX = clamp(cursorX, 0, 1);

            const targetY = clamp(cursorY, 0, 1);

            smoothed = smoothed
              ? {
                  x:
                    smoothed.x +
                    (cursorX - smoothed.x) * CURSOR_SMOOTHING,
                  y:
                    smoothed.y +
                    (targetY - smoothed.y) * CURSOR_SMOOTHING,
                }
              : { x: cursorX, y: targetY };

            emit({
              gesture: detected.gesture,
              confidence: detected.confidence,
              cursor: { x: smoothed.x, y: smoothed.y },
              hands: handCount,
              landmarks,
              timestamp: now,
              pinchDistance: detected.pinchDistance,
            });
          }
        }
      } catch (err) {
        const normalized =
          err instanceof Error ? err : new Error(String(err));

        /* Report each distinct error once, not once per frame. */
        if (normalized.message !== lastErrorMessage) {
          lastErrorMessage = normalized.message;
          setError(normalized.message);
          onErrorRef.current?.(normalized);
        }
      } finally {
        if (active) {
          rafId = requestAnimationFrame(tick);
        }
      }
    };

    rafId = requestAnimationFrame(tick);

    return () => {
      active = false;
      cancelAnimationFrame(rafId);
      setTracking(false);
    };
  }, [enabled, ready, videoRef]);

  return (
    <div
      className={`pointer-events-none ${className}`}
      aria-hidden="true"
    >
      {error && (
        <span className="sr-only">
          Hand tracking error: {error}
        </span>
      )}

      <span className="sr-only">
        Hand tracking{" "}
        {ready
          ? tracking
            ? "active"
            : "ready"
          : "initializing"}
      </span>
    </div>
  );
}