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

const CLICK_COOLDOWN_MS = 500;

function clamp(
  value: number,
  min: number,
  max: number,
): number {
  return Math.min(max, Math.max(min, value));
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

  const cameraGenerationRef =
    useRef(0);

  const lastGestureRef =
    useRef("NONE");

  const lastClickTimeRef =
    useRef(0);

  const tauriAvailableRef =
    useRef(false);

  const screenSizeRef =
    useRef<ScreenSize | null>(null);

  const frameCountRef =
    useRef(0);

  const fpsStartRef =
    useRef<number | null>(null);

  const mouseMoveInFlightRef =
    useRef(false);

  const [cameraActive, setCameraActive] =
    useState(false);

  const [cameraLoading, setCameraLoading] =
    useState(false);

  const [cameraError, setCameraError] =
    useState<string | null>(null);

  const [controlEnabled, setControlEnabled] =
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
      setMouseStatus(
        "Browser mode — native mouse control unavailable",
      );
    }

    return () => {
      mountedRef.current = false;
    };
  }, []);

  /*
   * Start camera.
   */
  const startCamera = useCallback(async () => {
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
    }
  }, []);

  /*
   * Stop camera.
   */
  const stopCamera = useCallback(() => {
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

    lastGestureRef.current = "NONE";
    lastClickTimeRef.current = 0;

    screenSizeRef.current = null;
    mouseMoveInFlightRef.current = false;

    setControlEnabled(false);

    setMouseStatus(
      "Hands-free control disabled",
    );
  }, []);

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
   * Get screen dimensions only once
   * and cache them.
   */
  const getScreenSize =
    useCallback(async (): Promise<ScreenSize | null> => {
      if (!tauriAvailableRef.current) {
        return null;
      }

      if (screenSizeRef.current) {
        return screenSizeRef.current;
      }

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

        return null;
      } catch (error) {
        console.error(
          "Failed to get screen size:",
          error,
        );

        return null;
      }
    }, []);

  /*
   * Move native OS mouse.
   *
   * We deliberately avoid sending multiple
   * move requests simultaneously.
   */
  const moveNativeMouse =
    useCallback(
      async (
        position: {
          x: number;
          y: number;
        },
      ) => {
        if (
          !tauriAvailableRef.current ||
          mouseMoveInFlightRef.current
        ) {
          return;
        }

        mouseMoveInFlightRef.current = true;

        try {
          const screen =
            await getScreenSize();

          if (!screen) {
            return;
          }

          const screenX =
            Math.round(
              clamp(position.x, 0, 1) *
                Math.max(
                  0,
                  screen.width - 1,
                ),
            );

          const screenY =
            Math.round(
              clamp(position.y, 0, 1) *
                Math.max(
                  0,
                  screen.height - 1,
                ),
            );

          await invoke<MouseCommandResult>(
            "vision_mouse_move",
            {
              x: screenX,
              y: screenY,
            },
          );
        } catch (error) {
          console.error(
            "Failed to move native mouse:",
            error,
          );

          if (mountedRef.current) {
            setMouseStatus(
              "Native mouse control error",
            );
          }
        } finally {
          mouseMoveInFlightRef.current = false;
        }
      },
      [getScreenSize],
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

        if (mountedRef.current) {
          setMouseStatus("Left click");
        }
      } catch (error) {
        console.error(
          "Failed to click native mouse:",
          error,
        );

        if (mountedRef.current) {
          setMouseStatus(
            "Native mouse click error",
          );
        }
      }
    }, []);

  /*
   * Handle MediaPipe result.
   */
  const handleVisionResult =
    useCallback(
      (result: HandGestureResult) => {
        if (!mountedRef.current) {
          return;
        }

        setProcessing(true);

        setGesture(result.gesture);

        setGestureConfidence(
          result.confidence,
        );

        setCursor(result.cursor);

        setHands(result.hands);

        updateFps();

        /*
         * When control is disabled,
         * we still show tracking results,
         * but we do NOT control the OS mouse.
         */
        if (!controlEnabled) {
          lastGestureRef.current =
            result.gesture;

          setProcessing(false);

          return;
        }

        /*
         * No hand.
         */
        if (
          result.gesture === "NONE" ||
          !result.cursor
        ) {
          setMouseStatus(
            "Control enabled — show your hand",
          );

          lastGestureRef.current =
            result.gesture;

          setProcessing(false);

          return;
        }

        /*
         * POINT and PINCH both keep
         * the OS cursor under the index finger.
         */
        if (
          result.gesture === "POINT" ||
          result.gesture === "PINCH"
        ) {
          void moveNativeMouse(
            result.cursor,
          );

          if (
            result.gesture === "POINT"
          ) {
            setMouseStatus(
              "Cursor control active",
            );
          }
        }

        /*
         * PINCH transition:
         *
         * POINT -> PINCH
         *
         * produces one click only.
         */
        if (
          result.gesture === "PINCH" &&
          lastGestureRef.current !==
            "PINCH"
        ) {
          void clickNativeMouse();
        }

        /*
         * Open palm = safe pause.
         */
        if (
          result.gesture === "OPEN_PALM"
        ) {
          setMouseStatus(
            "Open palm — control paused",
          );
        }

        /*
         * Fist currently has no
         * destructive action.
         */
        if (
          result.gesture ===
          "CLOSED_FIST"
        ) {
          setMouseStatus(
            "Fist detected — control paused",
          );
        }

        lastGestureRef.current =
          result.gesture;

        setProcessing(false);
      },
      [
        clickNativeMouse,
        controlEnabled,
        moveNativeMouse,
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

      setControlEnabled((current) => {
        const next = !current;

        lastGestureRef.current =
          "NONE";

        lastClickTimeRef.current = 0;

        if (!next) {
          setMouseStatus(
            "Hands-free control disabled",
          );
        } else if (
          !tauriAvailableRef.current
        ) {
          setMouseStatus(
            "Preview mode — open AIOS desktop app for mouse control",
          );
        } else {
          setMouseStatus(
            "Control enabled — point with your index finger",
          );
        }

        return next;
      });
    }, [cameraActive]);

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
            Point to move • Pinch to click
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
              ? "Hands-Free ON"
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
            onError={(error) => {
              console.error(
                "Hand tracking error:",
                error,
              );
            }}
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
                ? "Point with your index finger. Pinch thumb + index to click."
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