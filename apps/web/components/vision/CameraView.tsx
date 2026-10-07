"use client";

import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

export interface CameraViewProps {
  autoStart?: boolean;
  facingMode?: "user" | "environment";
  muted?: boolean;
  mirrored?: boolean;
  showControls?: boolean;
  showStatus?: boolean;
  className?: string;

  onStream?: (
    stream: MediaStream
  ) => void;

  onFrame?: (
    video: HTMLVideoElement,
    canvas: HTMLCanvasElement
  ) => void;

  onError?: (
    error: Error
  ) => void;
}

export default function CameraView({
  autoStart = false,
  facingMode = "user",
  muted = true,
  mirrored = true,
  showControls = true,
  showStatus = true,
  className = "",
  onStream,
  onFrame,
  onError,
}: CameraViewProps) {
  const videoRef =
    useRef<HTMLVideoElement | null>(null);

  const canvasRef =
    useRef<HTMLCanvasElement | null>(null);

  const streamRef =
    useRef<MediaStream | null>(null);

  const frameAnimationRef =
    useRef<number | null>(null);

  /*
   * Prevent multiple simultaneous
   * camera startup requests.
   */
  const startingRef =
    useRef(false);

  /*
   * Prevent old async getUserMedia()
   * results from attaching after cleanup.
   */
  const mountedRef =
    useRef(false);

  /*
   * Used to invalidate an old camera
   * startup operation.
   */
  const cameraGenerationRef =
    useRef(0);

  /*
   * Prevent multiple video.play()
   * calls from running together.
   */
  const playPromiseRef =
    useRef<Promise<void> | null>(null);

  const [active, setActive] =
    useState(false);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  /*
   * --------------------------------------------------------------------------
   * STOP CAMERA
   * --------------------------------------------------------------------------
   */

  const stopCamera = useCallback(() => {
    /*
     * Invalidate any currently running
     * async camera startup.
     */
    cameraGenerationRef.current += 1;

    /*
     * Stop frame processing.
     */
    if (
      frameAnimationRef.current !== null
    ) {
      cancelAnimationFrame(
        frameAnimationRef.current
      );

      frameAnimationRef.current = null;
    }

    const video =
      videoRef.current;

    const stream =
      streamRef.current;

    /*
     * Stop playback before detaching
     * the MediaStream.
     */
    if (video) {
      try {
        video.pause();
      } catch {
        // Ignore playback cleanup errors.
      }

      if (
        video.srcObject === stream
      ) {
        video.srcObject = null;
      }
    }

    /*
     * Stop every camera track.
     */
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

    streamRef.current = null;

    startingRef.current = false;

    playPromiseRef.current = null;

    if (mountedRef.current) {
      setActive(false);
      setLoading(false);
    }
  }, []);

  /*
   * --------------------------------------------------------------------------
   * START CAMERA
   * --------------------------------------------------------------------------
   */

  const startCamera = useCallback(
    async () => {
      /*
       * Never start another camera request
       * while one is already running.
       */
      if (startingRef.current) {
        return;
      }

      /*
       * If camera is already active,
       * there is nothing to do.
       */
      if (
        streamRef.current &&
        streamRef.current.active
      ) {
        return;
      }

      if (
        typeof navigator === "undefined" ||
        !navigator.mediaDevices?.getUserMedia
      ) {
        const cameraError =
          new Error(
            "Camera access is not supported by this browser."
          );

        setError(
          cameraError.message
        );

        onError?.(cameraError);

        return;
      }

      startingRef.current = true;

      const generation =
        cameraGenerationRef.current;

      setLoading(true);
      setError(null);

      try {
        const stream =
          await navigator.mediaDevices.getUserMedia(
            {
              video: {
                facingMode,
              },
              audio: false,
            }
          );

        /*
         * The component may have been unmounted
         * or camera startup may have been cancelled
         * while getUserMedia() was waiting.
         */
        if (
          !mountedRef.current ||
          generation !==
            cameraGenerationRef.current
        ) {
          stream
            .getTracks()
            .forEach((track) =>
              track.stop()
            );

          return;
        }

        /*
         * Another stream should never be attached.
         */
        if (streamRef.current) {
          stream
            .getTracks()
            .forEach((track) =>
              track.stop()
            );

          return;
        }

        const video =
          videoRef.current;

        if (!video) {
          stream
            .getTracks()
            .forEach((track) =>
              track.stop()
            );

          return;
        }

        /*
         * Configure video before assigning
         * the stream.
         */
        video.muted = muted;
        video.playsInline = true;
        video.autoplay = true;

        /*
         * Attach the stream exactly once.
         */
        streamRef.current =
          stream;

        video.srcObject =
          stream;

        /*
         * Notify parent.
         */
        onStream?.(stream);

        /*
         * Wait until the video has enough
         * metadata before calling play().
         */
        if (
          video.readyState <
          HTMLMediaElement.HAVE_METADATA
        ) {
          await new Promise<void>(
            (resolve) => {
              const handleMetadata =
                () => {
                  video.removeEventListener(
                    "loadedmetadata",
                    handleMetadata
                  );

                  resolve();
                };

              video.addEventListener(
                "loadedmetadata",
                handleMetadata,
                {
                  once: true,
                }
              );
            }
          );
        }

        /*
         * Verify that the stream is still
         * the current stream.
         */
        if (
          !mountedRef.current ||
          generation !==
            cameraGenerationRef.current ||
          streamRef.current !== stream ||
          video.srcObject !== stream
        ) {
          stream
            .getTracks()
            .forEach((track) =>
              track.stop()
            );

          if (
            streamRef.current ===
            stream
          ) {
            streamRef.current =
              null;
          }

          return;
        }

        /*
         * Don't call play() if another
         * play request is already running.
         */
        if (
          playPromiseRef.current
        ) {
          try {
            await playPromiseRef.current;
          } catch {
            // The original play request handles the error.
          }
        } else if (
          video.paused
        ) {
          const playPromise =
            video.play();

          playPromiseRef.current =
            playPromise;

          try {
            await playPromise;
          } catch (playError) {
            /*
             * AbortError can happen when the
             * stream is intentionally stopped.
             *
             * It should NOT be shown as a
             * camera failure.
             */
            if (
              playError instanceof
                DOMException &&
              playError.name ===
                "AbortError"
            ) {
              return;
            }

            throw playError;
          } finally {
            if (
              playPromiseRef.current ===
              playPromise
            ) {
              playPromiseRef.current =
                null;
            }
          }
        }

        /*
         * Final validation before marking
         * camera as active.
         */
        if (
          !mountedRef.current ||
          generation !==
            cameraGenerationRef.current ||
          streamRef.current !== stream
        ) {
          return;
        }

        setActive(true);
      } catch (cameraError) {
        /*
         * Ignore intentional cancellation.
         */
        if (
          cameraError instanceof
            DOMException &&
          cameraError.name ===
            "AbortError"
        ) {
          return;
        }

        /*
         * Ignore errors from an obsolete
         * camera generation.
         */
        if (
          generation !==
          cameraGenerationRef.current
        ) {
          return;
        }

        const normalized =
          cameraError instanceof Error
            ? cameraError
            : new Error(
                "Unable to access the camera."
              );

        setActive(false);
        setError(
          normalized.message
        );

        onError?.(normalized);
      } finally {
        /*
         * Only the current startup operation
         * should change loading state.
         */
        if (
          generation ===
          cameraGenerationRef.current
        ) {
          startingRef.current =
            false;

          setLoading(false);
        }
      }
    },
    [
      facingMode,
      muted,
      onError,
      onStream,
    ]
  );

  /*
   * --------------------------------------------------------------------------
   * FRAME PROCESSING
   * --------------------------------------------------------------------------
   */

  const processFrame =
    useCallback(() => {
      const video =
        videoRef.current;

      const canvas =
        canvasRef.current;

      if (
        !video ||
        !canvas ||
        !streamRef.current ||
        !streamRef.current.active
      ) {
        frameAnimationRef.current =
          null;

        return;
      }

      if (
        video.readyState < 2
      ) {
        frameAnimationRef.current =
          requestAnimationFrame(
            processFrame
          );

        return;
      }

      const width =
        video.videoWidth || 640;

      const height =
        video.videoHeight || 480;

      if (
        canvas.width !== width ||
        canvas.height !== height
      ) {
        canvas.width = width;
        canvas.height = height;
      }

      const context =
        canvas.getContext("2d");

      if (context) {
        context.drawImage(
          video,
          0,
          0,
          width,
          height
        );

        onFrame?.(
          video,
          canvas
        );
      }

      frameAnimationRef.current =
        requestAnimationFrame(
          processFrame
        );
    }, [onFrame]);

  /*
   * --------------------------------------------------------------------------
   * COMPONENT MOUNT / UNMOUNT
   * --------------------------------------------------------------------------
   *
   * IMPORTANT:
   *
   * We intentionally DO NOT put startCamera()
   * inside an effect whose dependencies include
   * active/loading.
   *
   * Otherwise React can repeatedly stop/start
   * the camera.
   */

  useEffect(() => {
    mountedRef.current = true;

    if (autoStart) {
      void startCamera();
    }

    return () => {
      mountedRef.current = false;

      /*
       * Cleanup only when this CameraView
       * instance is actually unmounted or
       * when autoStart changes.
       */
      stopCamera();
    };
  }, [
    autoStart,
    startCamera,
    stopCamera,
  ]);

  /*
   * --------------------------------------------------------------------------
   * FRAME LOOP
   * --------------------------------------------------------------------------
   */

  useEffect(() => {
    if (!active) {
      return;
    }

    /*
     * Don't create duplicate frame loops.
     */
    if (
      frameAnimationRef.current !== null
    ) {
      return;
    }

    frameAnimationRef.current =
      requestAnimationFrame(
        processFrame
      );

    return () => {
      if (
        frameAnimationRef.current !==
        null
      ) {
        cancelAnimationFrame(
          frameAnimationRef.current
        );

        frameAnimationRef.current =
          null;
      }
    };
  }, [
    active,
    processFrame,
  ]);

  /*
   * --------------------------------------------------------------------------
   * RENDER
   * --------------------------------------------------------------------------
   */

  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-gray-200 bg-black dark:border-gray-800 ${className}`}
    >
      <video
        ref={videoRef}
        muted={muted}
        playsInline
        autoPlay
        className={`block h-full w-full object-cover ${
          mirrored
            ? "-scale-x-100"
            : ""
        }`}
      />

      <canvas
        ref={canvasRef}
        className="pointer-events-none absolute inset-0 hidden h-full w-full"
      />

      {showStatus && (
        <div className="absolute left-3 top-3 flex items-center gap-2 rounded-full bg-black/60 px-3 py-1.5 text-[10px] text-white backdrop-blur">
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              active
                ? "bg-emerald-400"
                : loading
                ? "animate-pulse bg-amber-400"
                : error
                ? "bg-red-400"
                : "bg-gray-400"
            }`}
          />

          {active
            ? "Camera active"
            : loading
            ? "Starting camera..."
            : error
            ? "Camera error"
            : "Camera inactive"}
        </div>
      )}

      {error && (
        <div className="absolute inset-x-3 bottom-3 rounded-xl border border-red-400/20 bg-red-950/80 px-3 py-2 text-xs text-red-200 backdrop-blur">
          {error}
        </div>
      )}

      {showControls && (
        <div className="absolute bottom-3 right-3 flex gap-2">
          {!active ? (
            <button
              type="button"
              onClick={() =>
                void startCamera()
              }
              disabled={loading}
              className="rounded-lg bg-blue-600 px-3 py-2 text-xs font-medium text-white shadow-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading
                ? "Starting..."
                : "Start Camera"}
            </button>
          ) : (
            <button
              type="button"
              onClick={
                stopCamera
              }
              className="rounded-lg bg-black/70 px-3 py-2 text-xs font-medium text-white backdrop-blur hover:bg-black/80"
            >
              Stop Camera
            </button>
          )}
        </div>
      )}
    </div>
  );
}