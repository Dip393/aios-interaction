/**
 * AIOS Voice API
 *
 * Backend voice service wrapper.
 * Browser-level speech recognition remains
 * separate inside VoiceButton.tsx.
 */

import {
  apiGet,
  apiPost,
} from "./api";

export interface VoiceSession {
  id?: string;
  session_id?: string;
  status?: string;
  active?: boolean;
  listening?: boolean;
  [key: string]: unknown;
}

export interface VoiceStatus {
  status?: string;
  stt?: unknown;
  tts?: unknown;
  sessions?: number;
  [key: string]: unknown;
}

export interface TranscriptionResponse {
  success?: boolean;
  text?: string;
  transcript?: string;
  language?: string;
  confidence?: number;
  segments?: unknown[];
  [key: string]: unknown;
}

export interface SpeakRequest {
  text: string;
  session_id?: string;
  voice?: string;
  language?: string;
}

export interface SpeechResponse {
  success?: boolean;
  text?: string;
  audio_url?: string;
  audio_base64?: string;
  format?: string;
  [key: string]: unknown;
}

export interface VoiceProcessRequest {
  text?: string;
  audio?: string;
  session_id?: string;
  metadata?: Record<
    string,
    unknown
  >;
}

export const voiceApi = {
  status() {
    return apiGet<VoiceStatus>(
      "/voice/status"
    );
  },

  startSession(
    sessionId: string
  ) {
    return apiPost<VoiceSession>(
      `/voice/sessions/${encodeURIComponent(
        sessionId
      )}/start`
    );
  },

  stopSession(
    sessionId: string
  ) {
    return apiPost<VoiceSession>(
      `/voice/sessions/${encodeURIComponent(
        sessionId
      )}/stop`
    );
  },

  transcribe(
    audio: FormData
  ) {
    return apiPost<
      TranscriptionResponse,
      FormData
    >(
      "/voice/transcribe",
      audio
    );
  },

  speak(
    request: SpeakRequest
  ) {
    return apiPost<
      SpeechResponse,
      SpeakRequest
    >(
      "/voice/speak",
      request
    );
  },

  process(
    request: VoiceProcessRequest
  ) {
    return apiPost(
      "/voice/process",
      request
    );
  },
};