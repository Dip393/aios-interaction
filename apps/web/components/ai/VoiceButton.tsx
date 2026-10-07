"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

export interface VoiceButtonProps {
  onTranscript?: (text: string) => void;
  onListeningChange?: (listening: boolean) => void;
  disabled?: boolean;
  className?: string;
}

type SpeechRecognitionConstructor =
  new () => SpeechRecognition;

export default function VoiceButton({
  onTranscript,
  onListeningChange,
  disabled = false,
  className = "",
}: VoiceButtonProps) {
  const [isListening, setIsListening] =
    useState(false);

  const [isSupported, setIsSupported] =
    useState(true);

  const recognitionRef =
    useRef<SpeechRecognition | null>(null);

  /*
   * Keep the latest callbacks in refs.
   *
   * This prevents the SpeechRecognition instance
   * from being recreated every time the parent
   * component renders with a new callback reference.
   */
  const transcriptCallbackRef =
    useRef(onTranscript);

  const listeningCallbackRef =
    useRef(onListeningChange);

  useEffect(() => {
    transcriptCallbackRef.current =
      onTranscript;
  }, [onTranscript]);

  useEffect(() => {
    listeningCallbackRef.current =
      onListeningChange;
  }, [onListeningChange]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const SpeechRecognitionAPI =
      window.SpeechRecognition ??
      window.webkitSpeechRecognition;

    if (!SpeechRecognitionAPI) {
      setIsSupported(false);
      return;
    }

    setIsSupported(true);

    const recognition =
      new SpeechRecognitionAPI();

    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
      listeningCallbackRef.current?.(true);
    };

    recognition.onresult = (
      event: SpeechRecognitionEvent
    ) => {
      const transcript =
        event.results[0]?.[0]?.transcript ??
        "";

      const cleanedTranscript =
        transcript.trim();

      if (cleanedTranscript) {
        transcriptCallbackRef.current?.(
          cleanedTranscript
        );
      }
    };

    recognition.onerror = () => {
      setIsListening(false);
      listeningCallbackRef.current?.(false);
    };

    recognition.onend = () => {
      setIsListening(false);
      listeningCallbackRef.current?.(false);
    };

    recognitionRef.current =
      recognition;

    return () => {
      try {
        recognition.abort();
      } catch {
        // Recognition may already be stopped.
      }

      recognitionRef.current = null;
    };
  }, []);

  const toggleListening = () => {
    if (
      disabled ||
      !isSupported
    ) {
      return;
    }

    const recognition =
      recognitionRef.current;

    if (!recognition) {
      return;
    }

    if (isListening) {
      try {
        recognition.stop();
      } catch {
        setIsListening(false);
        listeningCallbackRef.current?.(
          false
        );
      }

      return;
    }

    try {
      recognition.start();
    } catch {
      /*
       * Calling start() while recognition is
       * already running can throw an InvalidStateError.
       */
      setIsListening(false);
      listeningCallbackRef.current?.(
        false
      );
    }
  };

  if (!isSupported) {
    return (
      <button
        type="button"
        disabled
        aria-label="Speech recognition is not supported"
        title="Speech recognition is not supported by this browser"
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-gray-200 text-gray-400 dark:border-gray-700 ${className}`}
      >
        <span
          aria-hidden="true"
          className="text-base"
        >
          🎙
        </span>
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={toggleListening}
      disabled={disabled}
      aria-label={
        isListening
          ? "Stop voice input"
          : "Start voice input"
      }
      title={
        isListening
          ? "Stop listening"
          : "Start voice input"
      }
      aria-pressed={isListening}
      className={`relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border transition ${
        isListening
          ? "border-red-300 bg-red-50 text-red-600 dark:border-red-900 dark:bg-red-950/30 dark:text-red-400"
          : "border-gray-200 bg-white text-gray-600 hover:border-blue-300 hover:text-blue-600 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:hover:border-blue-700 dark:hover:text-blue-400"
      } disabled:cursor-not-allowed disabled:opacity-40 ${className}`}
    >
      {isListening && (
        <span
          aria-hidden="true"
          className="absolute inset-0 animate-ping rounded-xl border border-red-400 opacity-30"
        />
      )}

      <span
        aria-hidden="true"
        className="relative text-base"
      >
        🎙
      </span>
    </button>
  );
}

/*
 * Browser Speech Recognition API typings.
 *
 * The Web Speech API is not included consistently
 * in TypeScript's default DOM typings, especially
 * for the webkit-prefixed implementation.
 */

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }

  interface SpeechRecognitionEvent
    extends Event {
    results: SpeechRecognitionResultList;
  }

  interface SpeechRecognition
    extends EventTarget {
    continuous: boolean;
    interimResults: boolean;
    lang: string;
    maxAlternatives: number;

    onstart:
      | ((event: Event) => void)
      | null;

    onresult:
      | ((
          event: SpeechRecognitionEvent
        ) => void)
      | null;

    onerror:
      | ((event: Event) => void)
      | null;

    onend:
      | ((event: Event) => void)
      | null;

    start: () => void;
    stop: () => void;
    abort: () => void;
  }
}