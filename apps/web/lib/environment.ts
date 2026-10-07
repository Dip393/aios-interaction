/**
 * AIOS Environment API
 *
 * Frontend API helpers and shared environment types.
 */

import {
  apiGet,
  apiPost,
} from "./api";

/**
 * Supported AIOS environment states.
 *
 * Keep this as a strict union so components can
 * safely perform status-based rendering.
 */
export type EnvironmentStatus =
  | "idle"
  | "active"
  | "paused"
  | "completed"
  | "error"
  | "destroyed";

/**
 * AIOS environment.
 */
export interface Environment {
  id: string;

  type: string;

  name?: string;

  title?: string;

  description?: string;

  status?: EnvironmentStatus;

  capabilities?: string[];

  data?: Record<string, unknown>;

  created_at?: string;

  createdAt?: string;

  updated_at?: string;

  updatedAt?: string;

  [key: string]: unknown;
}

/**
 * Environment runtime state.
 */
export interface EnvironmentState {
  environment_id?: string;

  id?: string;

  status?: EnvironmentStatus;

  data?: Record<string, unknown>;

  variables?: Record<string, unknown>;

  [key: string]: unknown;
}

/**
 * Create environment request.
 */
export interface CreateEnvironmentRequest {
  type: string;

  name?: string;

  description?: string;

  data?: Record<string, unknown>;

  capabilities?: string[];
}

/**
 * Environment data mutation request.
 */
export interface EnvironmentDataRequest {
  key: string;

  value: unknown;
}

/**
 * Environment API.
 */
export const environmentApi = {
  /**
   * List all environments.
   */
  list() {
    return apiGet<Environment[]>(
      "/environments"
    );
  },

  /**
   * Create a new environment.
   */
  create(
    request: CreateEnvironmentRequest
  ) {
    return apiPost<
      Environment,
      CreateEnvironmentRequest
    >(
      "/environments",
      request
    );
  },

  /**
   * Get one environment.
   */
  get(
    environmentId: string
  ) {
    return apiGet<Environment>(
      `/environments/${encodeURIComponent(
        environmentId
      )}`
    );
  },

  /**
   * Activate an environment.
   */
  activate(
    environmentId: string
  ) {
    return apiPost<Environment>(
      `/environments/${encodeURIComponent(
        environmentId
      )}/activate`
    );
  },

  /**
   * Get environment runtime state.
   */
  state(
    environmentId: string
  ) {
    return apiGet<EnvironmentState>(
      `/environments/${encodeURIComponent(
        environmentId
      )}/state`
    );
  },

  /**
   * Update environment data.
   */
  setData(
    environmentId: string,
    request: EnvironmentDataRequest
  ) {
    return apiPost<
      EnvironmentState,
      EnvironmentDataRequest
    >(
      `/environments/${encodeURIComponent(
        environmentId
      )}/data`,
      request
    );
  },

  /**
   * Pause an environment.
   */
  pause(
    environmentId: string
  ) {
    return apiPost<Environment>(
      `/environments/${encodeURIComponent(
        environmentId
      )}/pause`
    );
  },

  /**
   * Complete an environment.
   */
  complete(
    environmentId: string
  ) {
    return apiPost<Environment>(
      `/environments/${encodeURIComponent(
        environmentId
      )}/complete`
    );
  },
};