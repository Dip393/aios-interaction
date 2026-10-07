/**
 * AIOS API
 *
 * Main frontend service for communicating
 * with the AIOS Kernel and agent layer.
 */

import {
  apiGet,
  apiPost,
} from "./api";

export interface KernelProcessRequest {
  input: string;
  session_id?: string;
  user_id?: string;
  metadata?: Record<
    string,
    unknown
  >;
}

export interface KernelProcessResponse {
  success?: boolean;
  response?: string;
  message?: string;
  output?: string;
  result?: unknown;
  intent?: unknown;
  plan?: unknown;
  pending_action?: unknown;
  pendingAction?: unknown;
  approval?: unknown;
  action_approval?: unknown;
  task_id?: string;
  environment_id?: string;
  [key: string]: unknown;
}

export interface KernelConfirmationRequest {
  confirmation_id?: string;
  action_id?: string;
  approved: boolean;
  session_id?: string;
  reason?: string;
}

export interface KernelHealth {
  status?: string;
  healthy?: boolean;
  [key: string]: unknown;
}

export interface KernelStatus {
  status?: string;
  active_tasks?: number;
  active_environments?: number;
  [key: string]: unknown;
}

export interface AgentInfo {
  name: string;
  description?: string;
  capabilities?: string[];
  [key: string]: unknown;
}

export interface AgentExecuteRequest {
  input?: string;
  action?: string;
  parameters?: Record<
    string,
    unknown
  >;
  context?: Record<
    string,
    unknown
  >;
}

export const aiosApi = {
  process(
    request: KernelProcessRequest
  ) {
    return apiPost<
      KernelProcessResponse,
      KernelProcessRequest
    >(
      "/kernel/process",
      request
    );
  },

  confirm(
    request: KernelConfirmationRequest
  ) {
    return apiPost<
      KernelProcessResponse,
      KernelConfirmationRequest
    >(
      "/kernel/confirm",
      request
    );
  },

  health() {
    return apiGet<KernelHealth>(
      "/kernel/health"
    );
  },

  status() {
    return apiGet<KernelStatus>(
      "/kernel/status"
    );
  },

  agents() {
    return apiGet<AgentInfo[]>(
      "/agents"
    );
  },

  agent(name: string) {
    return apiGet<AgentInfo>(
      `/agents/${encodeURIComponent(
        name
      )}`
    );
  },

  executeAgent(
    name: string,
    request: AgentExecuteRequest
  ) {
    return apiPost(
      `/agents/${encodeURIComponent(
        name
      )}/execute`,
      request
    );
  },
};

export function processAIOS(
  input: string,
  options: Omit<
    KernelProcessRequest,
    "input"
  > = {}
) {
  return aiosApi.process({
    input,
    ...options,
  });
}