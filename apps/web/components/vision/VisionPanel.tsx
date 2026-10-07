"use client";

import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import { invoke } from "@tauri-apps/api/core";

import HandGestureController, {
  type HandGestureResult,
} from "./HandGestureController";

import GestureCursor from "./GestureCursor";

import VisionOverlay from "./VisionOverlay";

type VisionPanelProps = {
  className?: string;
  autoStart?: boolean;
};

type MouseCommandResult = {
  success: boolean;
  message: string;
};

type ScreenSize = {
  width: number;
  height: number;
};

type ScreenPoint = {
  x: number;
  y: number;
};

const CLICK_COOLDOWN_MS = 500;

/* A gesture must persist this many frames before it triggers anything. */
const STABLE_FRAMES = 3;
const PINCH_STABLE_FRAMES = 2;

/* Hold an open palm this long to pause / resume control. */
const PALM_HOLD_MS = 800;

/* Ignore native moves smaller than this (pixels). */
const MIN_MOVE_PX = 2;

/*
 * Cursor stops following the finger while thumb and index approach
 * each other, so the click lands where the user was pointing.
 */
const PINCH_FREEZE_DISTANCE = 0.6;

/*
 * Only the central part of the camera frame is mapped to the screen,
 * so the screen edges are reachable without leaving the frame.
 */
const ACTIVE_X_MIN = 0.12;
const ACTIVE_X_MAX = 0.88;
const ACTIVE_Y_MIN = 0.1;
const ACTIVE_Y_MAX = 0.8;

function clamp(
  value: number,
  min: number,
  max: number,
): number {
  return Math.min(max, Math.max(min, value));
}

function mapRange(
  value: number,
  min: number,
  max: number,
): number {
  return clamp((value - min) / (max - min), 0, 1);
}

export default function VisionPanel({
  className = "",
  autoStart = true,
}: VisionPanelProps) {
  const videoRef =
    useRef<HTMLVideoElement | null>(null);

  const streamRef =
    useRef<MediaStream | null>(null);

  const mountedRef =
    useRef(false);

  const startingRef =
    useRef(false);

  const wantCameraRef =
    useRef(false);

  const cameraGenerationRef =
    useRef(0);

  const tauriAvailableRef =
    useRef(false);

  /* Control state mirrored in refs so the per-frame handler is stable. */
  const controlEnabledRef =
    useRef(false);

  const pausedRef =
    useRef(false);

  /* Gesture stabilisation. */
  const candidateGestureRef =
    useRef("NONE");

  const candidateCountRef =
    useRef(0);

  const stableGestureRef =
    useRef("NONE");

  const palmStartRef =
    useRef<number | null>(null);

  const palmLatchedRef =
    useRef(false);

  const lastClickTimeRef =
    useRef(0);

  /* Native mouse plumbing. */
  const screenSizeRef =
    useRef<ScreenSize | null>(null);

  const screenSizePromiseRef =
    useRef<Promise<ScreenSize | null> | null>(null);

  const pendingMoveRef =
    useRef<ScreenPoint | null>(null);

  const lastSentRef =
    useRef<ScreenPoint | null>(null);

  const mouseMoveInFlightRef =
    useRef(false);

  const lastStatusRef =
    useRef("");

  const frameCountRef =
    useRef(0);

  const fpsStartRef =
    useRef<number | null>(null);

  const [cameraActive, setCameraActive] =
    useState(false);

  const [cameraLoading, setCameraLoading] =
    useState(false);

  const [cameraError, setCameraError] =
    useState<string | null>(null);

  const [controlEnabled, setControlEnabled] =
    useState(false);

  const [paused, setPaused] =
    useState(false);

  const [gesture, setGesture] =
    useState("NONE");

  const [gestureConfidence, setGestureConfidence] =
    useState(0);

  const [cursor, setCursor] =
    useState<{
      x: number;
      y: number;
    } | null>(null);

  const [hands, setHands] =
    useState(0);

  const [processing, setProcessing] =
    useState(false);

  const [fps, setFps] =
    useState(0);

  const [mouseStatus, setMouseStatus] =
    useState("Hands-free control disabled");

  const [tauriAvailable, setTauriAvailable] =
    useState(false);

  /*
   * Status text. Only touches React state when the text changes,
   * so it is safe to call on every frame.
   */
  const setStatus = useCallback(
    (message: string) => {
      if (lastStatusRef.current === message) {
        return;
      }

      lastStatusRef.current = message;

      if (mountedRef.current) {
        setMouseStatus(message);
      }
    },
    [],
  );

  /*
   * Detect whether we are running
   * inside the Tauri desktop runtime.
   */
  useEffect(() => {
    mountedRef.current = true;

    const available =
      typeof window !== "undefined" &&
      "__TAURI_INTERNALS__" in window;

    tauriAvailableRef.current = available;

    setTauriAvailable(available);

    if (!available) {
      setStatus(
        "Browser mode — native mouse control unavailable",
      );
    }

    return () => {
      mountedRef.current = false;
    };
  }, [setStatus]);

  /*
   * Reset everything that tracks gestures / pending mouse work.
   */
  const resetGestureState = useCallback(() => {
    candidateGestureRef.current = "NONE";
    candidateCountRef.current = 0;
    stableGestureRef.current = "NONE";

    palmStartRef.current = null;
    palmLatchedRef.current = false;

    lastClickTimeRef.current = 0;

    pendingMoveRef.current = null;
    lastSentRef.current = null;
  }, []);

  /*
   * Stop camera.
   */
  const stopCamera = useCallback(() => {
    wantCameraRef.current = false;

    cameraGenerationRef.current += 1;

    const stream = streamRef.current;

    streamRef.current = null;

    if (videoRef.current) {
      try {
        videoRef.current.pause();
      } catch {
        // Ignore cleanup errors.
      }

      videoRef.current.srcObject = null;
    }

    if (stream) {
      stream
        .getTracks()
        .forEach((track) => {
          try {
            track.stop();
          } catch {
            // Ignore already stopped tracks.
          }
        });
    }

    setCameraActive(false);
    setCameraLoading(false);

    setGesture("NONE");
    setGestureConfidence(0);
    setCursor(null);
    setHands(0);
    setProcessing(false);
    setFps(0);

    frameCountRef.current = 0;
    fpsStartRef.current = null;

    resetGestureState();

    screenSizeRef.current = null;
    screenSizePromiseRef.current = null;

    controlEnabledRef.current = false;
    pausedRef.current = false;

    setControlEnabled(false);
    setPaused(false);

    setStatus("Hands-free control disabled");
  }, [resetGestureState, setStatus]);

  /*
   * Start camera.
   */
  const startCamera = useCallback(async () => {
    wantCameraRef.current = true;

    /*
     * If a start is already in flight (React Strict Mode double
     * effect, quick double click) the in-flight call re-checks
     * `wantCameraRef` in `finally` and restarts if needed.
     */
    if (startingRef.current) {
      return;
    }

    if (streamRef.current) {
      return;
    }

    if (
      typeof navigator === "undefined" ||
      !navigator.mediaDevices?.getUserMedia
    ) {
      setCameraError(
        "Camera access is not supported by this browser.",
      );

      return;
    }

    startingRef.current = true;

    const generation =
      ++cameraGenerationRef.current;

    try {
      setCameraLoading(true);
      setCameraError(null);

      const stream =
        await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: "user",
            width: {
              ideal: 1280,
            },
            height: {
              ideal: 720,
            },
            frameRate: {
              ideal: 30,
              max: 30,
            },
          },
          audio: false,
        });

      if (
        !mountedRef.current ||
        generation !== cameraGenerationRef.current
      ) {
        stream
          .getTracks()
          .forEach((track) => track.stop());

        return;
      }

      streamRef.current = stream;

      /*
       * Camera unplugged / taken away by the OS:
       * reflect it in the UI instead of silently freezing.
       */
      stream.getVideoTracks().forEach((track) => {
        track.addEventListener("ended", () => {
          if (
            streamRef.current !== stream ||
            !mountedRef.current
          ) {
            return;
          }

          stopCamera();

          setCameraError(
            "Camera disconnected. Press Retry Camera.",
          );
        });
      });

      const video = videoRef.current;

      if (!video) {
        stream
          .getTracks()
          .forEach((track) => track.stop());

        streamRef.current = null;

        return;
      }

      /*
       * Only assign srcObject once for this stream.
       */
      if (video.srcObject !== stream) {
        video.srcObject = stream;
      }

      video.muted = true;
      video.playsInline = true;
      video.autoplay = true;

      await new Promise<void>((resolve) => {
        if (video.readyState >= 1) {
          resolve();
          return;
        }

        const handleMetadata = () => {
          video.removeEventListener(
            "loadedmetadata",
            handleMetadata,
          );

          resolve();
        };

        video.addEventListener(
          "loadedmetadata",
          handleMetadata,
        );
      });

      if (
        !mountedRef.current ||
        generation !== cameraGenerationRef.current
      ) {
        return;
      }

      if (video.paused) {
        try {
          await video.play();
        } catch (error) {
          if (
            error instanceof DOMException &&
            error.name === "AbortError"
          ) {
            return;
          }

          throw error;
        }
      }

      if (
        !mountedRef.current ||
        generation !== cameraGenerationRef.current
      ) {
        return;
      }

      setCameraActive(true);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : String(error);

      setCameraError(message);

      streamRef.current
        ?.getTracks()
        .forEach((track) => track.stop());

      streamRef.current = null;

      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    } finally {
      startingRef.current = false;

      if (mountedRef.current) {
        setCameraLoading(false);
      }

      /*
       * A start was requested while this one was being superseded
       * (Strict Mode mount -> cleanup -> mount). Start again.
       */
      if (
        wantCameraRef.current &&
        mountedRef.current &&
        !streamRef.current &&
        generation !== cameraGenerationRef.current
      ) {
        void startCamera();
      }
    }
  }, [stopCamera]);

  /*
   * Automatically start camera.
   */
  useEffect(() => {
    if (!autoStart) {
      return;
    }

    void startCamera();

    return () => {
      stopCamera();
    };
  }, [
    autoStart,
    startCamera,
    stopCamera,
  ]);

  /*
   * Calculate FPS.
   */
  const updateFps = useCallback(() => {
    frameCountRef.current += 1;

    const now = performance.now();

    if (fpsStartRef.current === null) {
      fpsStartRef.current = now;
      return;
    }

    const elapsed =
      now - fpsStartRef.current;

    if (elapsed >= 1000) {
      const calculatedFps =
        (frameCountRef.current * 1000) /
        elapsed;

      setFps(
        Math.round(
          Math.min(
            60,
            calculatedFps,
          ),
        ),
      );

      frameCountRef.current = 0;
      fpsStartRef.current = now;
    }
  }, []);

  /*
   * Screen size: fetched ONCE (single shared promise) when control is
   * enabled, then read synchronously from `screenSizeRef` on every
   * frame. A failure is cached too, so there is never a retry per frame.
   */
  const getScreenSize =
    useCallback((): Promise<ScreenSize | null> => {
      if (!tauriAvailableRef.current) {
        return Promise.resolve(null);
      }

      if (!screenSizePromiseRef.current) {
        screenSizePromiseRef.current = (async () => {
          try {
            const screen =
              await invoke<ScreenSize>(
                "vision_mouse_screen_size",
              );

            if (
              screen &&
              screen.width > 0 &&
              screen.height > 0
            ) {
              screenSizeRef.current = screen;

              return screen;
            }
          } catch (error) {
            console.warn(
              "Native screen size unavailable, using window.screen:",
              error,
            );
          }

          /*
           * Fallback (e.g. non-Windows builds): derive from the webview.
           */
          const scale = /win/i.test(navigator.platform)
            ? window.devicePixelRatio || 1
            : 1;

          const fallback = {
            width: Math.round(window.screen.width * scale),
            height: Math.round(window.screen.height * scale),
          };

          if (fallback.width > 0 && fallback.height > 0) {
            screenSizeRef.current = fallback;

            return fallback;
          }

          return null;
        })();
      }

      return screenSizePromiseRef.current;
    }, []);

  /*
   * Sends queued mouse moves, one invoke at a time.
   * While an invoke is in flight only the NEWEST target is kept,
   * so the cursor never lags behind a backlog.
   */
  const flushMouseMove =
    useCallback(async () => {
      if (mouseMoveInFlightRef.current) {
        return;
      }

      mouseMoveInFlightRef.current = true;

      try {
        while (
          pendingMoveRef.current &&
          mountedRef.current
        ) {
          const target = pendingMoveRef.current;

          pendingMoveRef.current = null;

          const last = lastSentRef.current;

          if (
            last &&
            Math.abs(last.x - target.x) < MIN_MOVE_PX &&
            Math.abs(last.y - target.y) < MIN_MOVE_PX
          ) {
            continue;
          }

          lastSentRef.current = target;

          await invoke<MouseCommandResult>(
            "vision_mouse_move",
            {
              x: target.x,
              y: target.y,
            },
          );
        }
      } catch (error) {
        console.error(
          "Failed to move native mouse:",
          error,
        );

        lastSentRef.current = null;

        setStatus("Native mouse control error");
      } finally {
        mouseMoveInFlightRef.current = false;
      }
    }, [setStatus]);

  /*
   * Move native OS mouse (normalised camera position -> screen pixels).
   */
  const moveNativeMouse =
    useCallback(
      (position: { x: number; y: number }) => {
        if (!tauriAvailableRef.current) {
          return;
        }

        const screen = screenSizeRef.current;

        if (!screen) {
          /* Not resolved yet — shared promise, no extra invoke. */
          void getScreenSize();

          return;
        }

        pendingMoveRef.current = {
          x: Math.round(
            mapRange(
              position.x,
              ACTIVE_X_MIN,
              ACTIVE_X_MAX,
            ) * Math.max(0, screen.width - 1),
          ),
          y: Math.round(
            mapRange(
              position.y,
              ACTIVE_Y_MIN,
              ACTIVE_Y_MAX,
            ) * Math.max(0, screen.height - 1),
          ),
        };

        void flushMouseMove();
      },
      [flushMouseMove, getScreenSize],
    );

  /*
   * Native left click.
   */
  const clickNativeMouse =
    useCallback(async () => {
      if (!tauriAvailableRef.current) {
        return;
      }

      const now = Date.now();

      if (
        now - lastClickTimeRef.current <
        CLICK_COOLDOWN_MS
      ) {
        return;
      }

      lastClickTimeRef.current = now;

      try {
        await invoke<MouseCommandResult>(
          "vision_mouse_click",
        );

        setStatus("Left click");
      } catch (error) {
        console.error(
          "Failed to click native mouse:",
          error,
        );

        setStatus("Native mouse click error");
      }
    }, [setStatus]);

  /*
   * Handle MediaPipe result.
   *
   * Stable identity (reads state through refs) so the controller
   * never sees a changing callback.
   */
  const handleVisionResult =
    useCallback(
      (result: HandGestureResult) => {
        if (!mountedRef.current) {
          return;
        }

        /* Always show tracking feedback. */
        setGesture(result.gesture);
        setGestureConfidence(result.confidence);
        setCursor(result.cursor);
        setHands(result.hands);
        setProcessing(result.hands > 0);

        updateFps();

        /*
         * Stabilise: a gesture must be seen for a few consecutive
         * frames before it becomes the "stable" gesture. Losing the
         * hand is applied immediately (safe direction).
         */
        const raw = result.cursor
          ? result.gesture
          : "NONE";

        if (raw === candidateGestureRef.current) {
          candidateCountRef.current += 1;
        } else {
          candidateGestureRef.current = raw;
          candidateCountRef.current = 1;
        }

        const needed =
          raw === "NONE"
            ? 1
            : raw === "PINCH"
            ? PINCH_STABLE_FRAMES
            : STABLE_FRAMES;

        const previousStable =
          stableGestureRef.current;

        if (candidateCountRef.current >= needed) {
          stableGestureRef.current = raw;
        }

        const stable = stableGestureRef.current;

        /*
         * Hands-free OFF: show tracking only, never touch the OS mouse.
         */
        if (!controlEnabledRef.current) {
          palmStartRef.current = null;
          palmLatchedRef.current = false;

          return;
        }

        /*
         * Open palm held = pause / resume.
         * Latched so one hold toggles exactly once.
         */
        const now = performance.now();

        if (stable === "OPEN_PALM") {
          if (palmStartRef.current === null) {
            palmStartRef.current = now;
          }

          if (
            !palmLatchedRef.current &&
            now - palmStartRef.current >= PALM_HOLD_MS
          ) {
            palmLatchedRef.current = true;

            const next = !pausedRef.current;

            pausedRef.current = next;

            pendingMoveRef.current = null;

            setPaused(next);
          }
        } else {
          palmStartRef.current = null;
          palmLatchedRef.current = false;
        }

        if (pausedRef.current) {
          setStatus(
            "Paused — hold open palm to resume",
          );

          return;
        }

        if (!tauriAvailableRef.current) {
          setStatus(
            "Preview mode — open AIOS desktop app for mouse control",
          );

          return;
        }

        if (stable === "NONE") {
          setStatus(
            "Control enabled — show your hand",
          );

          return;
        }

        if (stable === "OPEN_PALM") {
          setStatus(
            "Open palm — keep holding to pause",
          );

          return;
        }

        /*
         * POINT -> move native mouse.
         * Frozen while thumb/index approach each other (pre-click).
         */
        if (stable === "POINT") {
          if (
            result.gesture === "POINT" &&
            result.cursor &&
            (result.pinchDistance === undefined ||
              result.pinchDistance >
                PINCH_FREEZE_DISTANCE)
          ) {
            moveNativeMouse(result.cursor);
          }

          setStatus("Cursor control active");

          return;
        }

        /*
         * PINCH -> one left click per pinch (POINT -> PINCH edge).
         */
        if (stable === "PINCH") {
          if (previousStable !== "PINCH") {
            void clickNativeMouse();
          }

          return;
        }

        if (stable === "CLOSED_FIST") {
          setStatus("Fist detected — control idle");

          return;
        }

        setStatus(
          "Control enabled — point with your index finger",
        );
      },
      [
        clickNativeMouse,
        moveNativeMouse,
        setStatus,
        updateFps,
      ],
    );

  /*
   * Toggle hands-free control.
   */
  const toggleControl =
    useCallback(() => {
      if (!cameraActive) {
        return;
      }

      const next = !controlEnabledRef.current;

      controlEnabledRef.current = next;
      pausedRef.current = false;

      resetGestureState();

      setPaused(false);
      setControlEnabled(next);

      if (!next) {
        setStatus("Hands-free control disabled");
      } else if (!tauriAvailableRef.current) {
        setStatus(
          "Preview mode — open AIOS desktop app for mouse control",
        );
      } else {
        /* Fresh, single screen-size lookup for this session. */
        screenSizeRef.current = null;
        screenSizePromiseRef.current = null;

        void getScreenSize();

        setStatus(
          "Control enabled — point with your index finger",
        );
      }
    }, [
      cameraActive,
      getScreenSize,
      resetGestureState,
      setStatus,
    ]);

  /*
   * Stable error handler (an inline arrow here used to change on
   * every render).
   */
  const handleTrackingError =
    useCallback(
      (error: Error) => {
        console.error(
          "Hand tracking error:",
          error,
        );

        setStatus(
          `Hand tracking unavailable: ${error.message}`,
        );
      },
      [setStatus],
    );

  return (
    <section
      className={`relative flex min-h-[600px] w-full flex-col overflow-hidden rounded-2xl border border-[#263249] bg-[#0b1020] ${className}`}
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#263249] bg-[#0d1425] px-4 py-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#5b8cff]">
            AIOS Vision
          </p>

          <h2 className="mt-1 text-lg font-semibold text-white">
            Hands-Free Control
          </h2>

          <p className="mt-1 text-xs text-[#91a0b8]">
            Point to move • Pinch to click • Open palm to pause
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Tauri status */}
          <span
            className={`rounded-full border px-2.5 py-1 text-[10px] font-medium ${
              tauriAvailable
                ? "border-[#43d19e]/30 bg-[#43d19e]/10 text-[#43d19e]"
                : "border-yellow-400/30 bg-yellow-400/10 text-yellow-300"
            }`}
          >
            {tauriAvailable
              ? "Desktop Runtime"
              : "Browser Preview"}
          </span>

          {/* Camera status */}
          <span
            className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-medium ${
              cameraActive
                ? "border-[#43d19e]/30 bg-[#43d19e]/10 text-[#43d19e]"
                : "border-[#263249] bg-[#111827] text-[#91a0b8]"
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                cameraActive
                  ? "bg-[#43d19e]"
                  : "bg-[#64748b]"
              }`}
            />

            {cameraActive
              ? "Camera Active"
              : "Camera Off"}
          </span>

          {/* Control status */}
          <span
            className={`rounded-full border px-2.5 py-1 text-[10px] font-medium ${
              controlEnabled
                ? "border-blue-400/30 bg-blue-400/10 text-blue-300"
                : "border-[#263249] bg-[#111827] text-[#91a0b8]"
            }`}
          >
            {controlEnabled
              ? paused
                ? "Paused"
                : "Hands-Free ON"
              : "Control OFF"}
          </span>
        </div>
      </div>

      {/* Camera area */}
      <div className="relative flex min-h-0 flex-1 items-center justify-center bg-black p-3">
        <div className="relative aspect-video w-full max-w-[1100px] overflow-hidden rounded-xl border border-[#263249] bg-[#05070d]">
          <video
            ref={videoRef}
            className="h-full w-full object-cover"
            style={{
              transform: "scaleX(-1)",
            }}
            autoPlay
            muted
            playsInline
          />

          {/* MediaPipe hand tracking */}
          <HandGestureController
            videoRef={videoRef}
            enabled={cameraActive}
            controlEnabled={controlEnabled}
            mirrored
            onResult={handleVisionResult}
            onError={handleTrackingError}
          />

          {/* Camera loading */}
          {cameraLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm">
              <div className="rounded-xl border border-[#263249] bg-[#0b1020]/90 px-5 py-4 text-center">
                <div className="mx-auto mb-3 h-6 w-6 animate-spin rounded-full border-2 border-[#263249] border-t-[#5b8cff]" />

                <p className="text-sm font-medium text-white">
                  Starting camera...
                </p>

                <p className="mt-1 text-xs text-[#91a0b8]">
                  Please allow camera access
                </p>
              </div>
            </div>
          )}

          {/* Camera error */}
          {cameraError && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
              <div className="max-w-md rounded-xl border border-red-400/20 bg-[#110d14]/95 p-5 text-center">
                <p className="text-sm font-semibold text-red-300">
                  Camera unavailable
                </p>

                <p className="mt-2 text-xs leading-5 text-[#c1cada]">
                  {cameraError}
                </p>

                <button
                  type="button"
                  onClick={() => {
                    void startCamera();
                  }}
                  className="mt-4 rounded-lg bg-[#5b8cff] px-4 py-2 text-xs font-semibold text-white transition hover:bg-[#4a7bea]"
                >
                  Retry Camera
                </button>
              </div>
            </div>
          )}

          {/* Virtual cursor */}
          <GestureCursor
            position={
              cursor
                ? {
                    x: cursor.x * 100,
                    y: cursor.y * 100,
                  }
                : null
            }
            gesture={gesture}
            visible={
              cameraActive &&
              cursor !== null
            }
            size={
              gesture === "PINCH"
                ? 44
                : 34
            }
          />

          {/* Vision overlay */}
          <VisionOverlay
            active={cameraActive}
            gesture={gesture}
            gestureConfidence={
              gestureConfidence
            }
            hands={hands}
            fps={fps}
            processing={processing}
            showGesture
            showHands
            showStats
            showInstructions
            instruction={
              controlEnabled
                ? paused
                  ? "Control paused. Hold an open palm to resume."
                  : "Point to move. Pinch thumb + index to click. Hold open palm to pause."
                : "Enable Hands-Free Control to control the mouse."
            }
          />

          {/* Browser warning */}
          {!tauriAvailable && (
            <div className="absolute bottom-3 left-3 right-3 rounded-lg border border-yellow-400/20 bg-black/65 px-3 py-2 text-center backdrop-blur">
              <p className="text-[10px] text-yellow-200">
                Browser preview only — native
                mouse control requires the
                AIOS desktop app.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Bottom controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[#263249] bg-[#0d1425] px-4 py-3">
        <div className="min-w-0">
          <p className="truncate text-xs font-medium text-white">
            {mouseStatus}
          </p>

          <p className="mt-1 text-[10px] text-[#71809a]">
            Gesture: {gesture}
            {" • "}
            Hands: {hands}
            {" • "}
            FPS: {fps}
            {" • "}
            Confidence:{" "}
            {Math.round(
              gestureConfidence * 100,
            )}
            %
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Camera button */}
          <button
            type="button"
            onClick={() => {
              if (cameraActive) {
                stopCamera();
              } else {
                void startCamera();
              }
            }}
            className="rounded-lg border border-[#33415c] bg-[#111827] px-3 py-2 text-xs font-medium text-[#d9e2f2] transition hover:bg-[#172033]"
          >
            {cameraActive
              ? "Stop Camera"
              : "Start Camera"}
          </button>

          {/* Hands-free button */}
          <button
            type="button"
            disabled={!cameraActive}
            onClick={toggleControl}
            className={`rounded-lg px-4 py-2 text-xs font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-40 ${
              controlEnabled
                ? "bg-red-500 hover:bg-red-600"
                : "bg-[#5b8cff] hover:bg-[#4a7bea]"
            }`}
          >
            {controlEnabled
              ? "Disable Control"
              : "Enable Hands-Free Control"}
          </button>
        </div>
      </div>
    </section>
  );
}