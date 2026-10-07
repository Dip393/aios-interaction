/**
 * AIOS Vision API
 *
 * Frontend service for VisionManager.
 */

import {
  apiGet,
  apiPost,
} from "./api";

export interface VisionLandmark {
  x: number;
  y: number;
  z?: number;
}

export interface VisionHand {
  id?: string;
  handedness?: string;
  confidence?: number;
  landmarks?: VisionLandmark[];
}

export interface VisionFrameRequest {
  session_id?: string;
  hands?: VisionHand[];
  gesture?: string;
  gesture_confidence?: number;
  metadata?: Record<
    string,
    unknown
  >;
}

export interface VisionFrameResponse {
  success?: boolean;
  gesture?: string;
  gesture_confidence?: number;
  hands?: VisionHand[];
  cursor?: {
    x: number;
    y: number;
  };
  action?: string;
  [key: string]: unknown;
}

export interface VisionSession {
  id?: string;
  session_id?: string;
  status?: string;
  active?: boolean;
  last_result?: VisionFrameResponse;
  [key: string]: unknown;
}

export interface VisionStatus {
  status?: string;
  active?: boolean;
  sessions?: number;
  [key: string]: unknown;
}

export const visionApi = {
  status() {
    return apiGet<VisionStatus>(
      "/vision/status"
    );
  },

  startSession(
    sessionId: string
  ) {
    return apiPost<VisionSession>(
      `/vision/sessions/${encodeURIComponent(
        sessionId
      )}/start`
    );
  },

  stopSession(
    sessionId: string
  ) {
    return apiPost<VisionSession>(
      `/vision/sessions/${encodeURIComponent(
        sessionId
      )}/stop`
    );
  },

  processFrame(
    request: VisionFrameRequest
  ) {
    return apiPost<
      VisionFrameResponse,
      VisionFrameRequest
    >(
      "/vision/process",
      request
    );
  },

  lastResult(
    sessionId: string
  ) {
    return apiGet<VisionFrameResponse>(
      `/vision/sessions/${encodeURIComponent(
        sessionId
      )}/last`
    );
  },
};