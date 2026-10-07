"use client";

import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  FilesetResolver,
  HandLandmarker,
  type HandLandmarkerResult,
} from "@mediapipe/tasks-vision";

export type HandGestureControllerProps = {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  enabled?: boolean;
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

const DEFAULT_SMOOTHING = 0.28;

const PINCH_START_DISTANCE = 0.055;
const PINCH_END_DISTANCE = 0.075;

const CLICK_COOLDOWN_MS = 450;

const INDEX_TIP = 8;
const INDEX_PIP = 6;
const INDEX_MCP = 5;

const MIDDLE_TIP = 12;
const MIDDLE_PIP = 10;

const RING_TIP = 16;
const RING_PIP = 14;

const PINKY_TIP = 20;
const PINKY_PIP = 18;

const THUMB_TIP = 4;
const THUMB_IP = 3;

function distance(a: Point, b: Point): number {
  return Math.sqrt(
    Math.pow(a.x - b.x, 2) +
      Math.pow(a.y - b.y, 2) +
      Math.pow(a.z - b.z, 2),
  );
}

function isFingerExtended(
  landmarks: Point[],
  tipIndex: number,
  pipIndex: number,
): boolean {
  if (!landmarks[tipIndex] || !landmarks[pipIndex]) {
    return false;
  }

  return landmarks[tipIndex].y < landmarks[pipIndex].y;
}

function isThumbExtended(landmarks: Point[]): boolean {
  if (!landmarks[THUMB_TIP] || !landmarks[THUMB_IP]) {
    return false;
  }

  return Math.abs(landmarks[THUMB_TIP].x - landmarks[THUMB_IP].x) > 0.045;
}

function detectGesture(landmarks: Point[]): {
  gesture: HandGestureName;
  confidence: number;
} {
  if (landmarks.length < 21) {
    return {
      gesture: "NONE",
      confidence: 0,
    };
  }

  const indexExtended = isFingerExtended(
    landmarks,
    INDEX_TIP,
    INDEX_PIP,
  );

  const middleExtended = isFingerExtended(
    landmarks,
    MIDDLE_TIP,
    MIDDLE_PIP,
  );

  const ringExtended = isFingerExtended(
    landmarks,
    RING_TIP,
    RING_PIP,
  );

  const pinkyExtended = isFingerExtended(
    landmarks,
    PINKY_TIP,
    PINKY_PIP,
  );

  const thumbExtended = isThumbExtended(landmarks);

  const pinchDistance = distance(
    landmarks[THUMB_TIP],
    landmarks[INDEX_TIP],
  );

  /*
   * PINCH
   *
   * Thumb + index finger close together.
   */
  if (pinchDistance < PINCH_START_DISTANCE) {
    return {
      gesture: "PINCH",
      confidence: Math.min(
        1,
        Math.max(
          0,
          1 - pinchDistance / PINCH_START_DISTANCE,
        ),
      ),
    };
  }

  /*
   * POINT
   *
   * Only index finger extended.
   */
  if (
    indexExtended &&
    !middleExtended &&
    !ringExtended &&
    !pinkyExtended
  ) {
    return {
      gesture: "POINT",
      confidence: 0.9,
    };
  }

  /*
   * PEACE
   *
   * Index + middle extended.
   */
  if (
    indexExtended &&
    middleExtended &&
    !ringExtended &&
    !pinkyExtended
  ) {
    return {
      gesture: "PEACE",
      confidence: 0.9,
    };
  }

  /*
   * OPEN PALM
   */
  if (
    thumbExtended &&
    indexExtended &&
    middleExtended &&
    ringExtended &&
    pinkyExtended
  ) {
    return {
      gesture: "OPEN_PALM",
      confidence: 0.9,
    };
  }

  /*
   * THUMBS UP
   *
   * Thumb extended while other fingers remain folded.
   */
  if (
    thumbExtended &&
    !indexExtended &&
    !middleExtended &&
    !ringExtended &&
    !pinkyExtended &&
    landmarks[THUMB_TIP].y < landmarks[THUMB_IP].y
  ) {
    return {
      gesture: "THUMBS_UP",
      confidence: 0.85,
    };
  }

  /*
   * CLOSED FIST
   */
  if (
    !indexExtended &&
    !middleExtended &&
    !ringExtended &&
    !pinkyExtended &&
    !thumbExtended
  ) {
    return {
      gesture: "CLOSED_FIST",
      confidence: 0.85,
    };
  }

  return {
    gesture: "NONE",
    confidence: 0.4,
  };
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function smoothValue(
  previous: number | null,
  current: number,
  smoothing: number,
): number {
  if (previous === null) {
    return current;
  }

  return previous + (current - previous) * smoothing;
}

export default function HandGestureController({
  videoRef,
  enabled = true,
  controlEnabled = false,
  mirrored = true,
  onResult,
  onError,
  className = "",
}: HandGestureControllerProps) {
  const [ready, setReady] = useState(false);
  const [tracking, setTracking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const landmarkerRef = useRef<HandLandmarker | null>(null);

  const animationFrameRef =
    useRef<number | null>(null);

  const lastVideoTimeRef = useRef(-1);

  const previousCursorRef = useRef<{
    x: number;
    y: number;
  } | null>(null);

  const pinchActiveRef = useRef(false);

  const lastClickTimeRef = useRef(0);

  const mountedRef = useRef(false);

  const initializingRef = useRef(false);

  const processingRef = useRef(false);

  const initialize = useCallback(async () => {
    if (initializingRef.current) {
      return;
    }

    if (landmarkerRef.current) {
      return;
    }

    initializingRef.current = true;

    try {
      setError(null);

      const vision = await FilesetResolver.forVisionTasks(
        WASM_URL,
      );

      const landmarker =
        await HandLandmarker.createFromOptions(
          vision,
          {
            baseOptions: {
              modelAssetPath: MODEL_URL,
              delegate: "GPU",
            },

            runningMode: "VIDEO",

            numHands: 1,

            minHandDetectionConfidence: 0.55,

            minHandPresenceConfidence: 0.55,

            minTrackingConfidence: 0.55,
          },
        );

      if (!mountedRef.current) {
        landmarker.close();
        return;
      }

      landmarkerRef.current = landmarker;

      setReady(true);
    } catch (err) {
      const normalizedError =
        err instanceof Error
          ? err
          : new Error(String(err));

      setError(normalizedError.message);

      onError?.(normalizedError);
    } finally {
      initializingRef.current = false;
    }
  }, [onError]);

  const emitResult = useCallback(
    (
      gesture: HandGestureName,
      confidence: number,
      cursor: {
        x: number;
        y: number;
      } | null,
      landmarks: Point[],
      hands: number,
    ) => {
      onResult?.({
        gesture,
        confidence,
        cursor,
        hands,
        landmarks,
        timestamp: performance.now(),
      });
    },
    [onResult],
  );

  const processVideo = useCallback(() => {
    if (!mountedRef.current) {
      return;
    }

    const video = videoRef.current;

    const landmarker = landmarkerRef.current;

    if (
      !enabled ||
      !video ||
      !landmarker ||
      video.readyState < 2 ||
      video.videoWidth === 0 ||
      video.videoHeight === 0
    ) {
      animationFrameRef.current =
        requestAnimationFrame(processVideo);

      return;
    }

    /*
     * MediaPipe should not receive the exact same video frame
     * repeatedly.
     */
    if (
      video.currentTime === lastVideoTimeRef.current
    ) {
      animationFrameRef.current =
        requestAnimationFrame(processVideo);

      return;
    }

    if (processingRef.current) {
      animationFrameRef.current =
        requestAnimationFrame(processVideo);

      return;
    }

    processingRef.current = true;

    try {
      const timestamp = performance.now();

      const result: HandLandmarkerResult =
        landmarker.detectForVideo(
          video,
          timestamp,
        );

      lastVideoTimeRef.current =
        video.currentTime;

      const firstHand =
        result.landmarks?.[0];

      if (!firstHand || firstHand.length < 21) {
        setTracking(false);

        previousCursorRef.current = null;

        /*
         * Losing the hand automatically releases pinch.
         * This prevents a stuck click/drag state.
         */
        pinchActiveRef.current = false;

        emitResult(
          "NONE",
          0,
          null,
          [],
          result.landmarks?.length ?? 0,
        );

        return;
      }

      setTracking(true);

      const landmarks: Point[] =
        firstHand.map((landmark) => ({
          x: landmark.x,
          y: landmark.y,
          z: landmark.z,
        }));

      const detected =
        detectGesture(landmarks);

      /*
       * Index finger tip is used as virtual cursor.
       */
      let cursorX = landmarks[INDEX_TIP].x;
      let cursorY = landmarks[INDEX_TIP].y;

      /*
       * User-facing mirrored preview:
       *
       * Camera image is mirrored horizontally,
       * therefore the logical screen cursor is
       * horizontally inverted as well.
       */
      if (mirrored) {
        cursorX = 1 - cursorX;
      }

      cursorX = clamp(cursorX, 0, 1);
      cursorY = clamp(cursorY, 0, 1);

      const previous =
        previousCursorRef.current;

      const smoothedX = smoothValue(
        previous?.x ?? null,
        cursorX,
        DEFAULT_SMOOTHING,
      );

      const smoothedY = smoothValue(
        previous?.y ?? null,
        cursorY,
        DEFAULT_SMOOTHING,
      );

      previousCursorRef.current = {
        x: smoothedX,
        y: smoothedY,
      };

      const normalizedCursor = {
        x: smoothedX,
        y: smoothedY,
      };

      /*
       * The controller only reports gestures.
       *
       * Native OS mouse movement/clicking will be connected
       * separately through Tauri.
       */
      if (controlEnabled) {
        const now = Date.now();

        if (
          detected.gesture === "PINCH" &&
          !pinchActiveRef.current &&
          now - lastClickTimeRef.current >=
            CLICK_COOLDOWN_MS
        ) {
          pinchActiveRef.current = true;

          lastClickTimeRef.current = now;
        }

        if (
          detected.gesture !== "PINCH" &&
          pinchActiveRef.current
        ) {
          /*
           * Hysteresis:
           *
           * PINCH_END_DISTANCE is intentionally larger
           * than PINCH_START_DISTANCE.
           *
           * This makes the pinch state less sensitive
           * to tiny hand movements.
           */
          const currentPinchDistance =
            distance(
              landmarks[THUMB_TIP],
              landmarks[INDEX_TIP],
            );

          if (
            currentPinchDistance >
            PINCH_END_DISTANCE
          ) {
            pinchActiveRef.current = false;
          }
        }
      } else {
        pinchActiveRef.current = false;
      }

      emitResult(
        detected.gesture,
        detected.confidence,
        normalizedCursor,
        landmarks,
        result.landmarks?.length ?? 0,
      );
    } catch (err) {
      const normalizedError =
        err instanceof Error
          ? err
          : new Error(String(err));

      setError(normalizedError.message);

      onError?.(normalizedError);
    } finally {
      processingRef.current = false;
    }

    animationFrameRef.current =
      requestAnimationFrame(processVideo);
  }, [
    controlEnabled,
    emitResult,
    enabled,
    mirrored,
    onError,
    videoRef,
  ]);

  useEffect(() => {
    mountedRef.current = true;

    void initialize();

    return () => {
      mountedRef.current = false;

      if (
        animationFrameRef.current !== null
      ) {
        cancelAnimationFrame(
          animationFrameRef.current,
        );

        animationFrameRef.current = null;
      }

      landmarkerRef.current?.close();

      landmarkerRef.current = null;

      previousCursorRef.current = null;

      pinchActiveRef.current = false;
    };
  }, [initialize]);

  useEffect(() => {
    if (!enabled || !ready) {
      if (
        animationFrameRef.current !== null
      ) {
        cancelAnimationFrame(
          animationFrameRef.current,
        );

        animationFrameRef.current = null;
      }

      return;
    }

    if (animationFrameRef.current === null) {
      animationFrameRef.current =
        requestAnimationFrame(processVideo);
    }

    return () => {
      if (
        animationFrameRef.current !== null
      ) {
        cancelAnimationFrame(
          animationFrameRef.current,
        );

        animationFrameRef.current = null;
      }
    };
  }, [
    enabled,
    ready,
    processVideo,
  ]);

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